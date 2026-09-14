import json
import logging
import re

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3


class LLMToolCall:
    def __init__(self, name: str, arguments: dict):
        self.name = name
        self.arguments = arguments


class LLMResponse:
    def __init__(self, content: str | None, tool_calls: list[LLMToolCall] | None = None):
        self.content = content
        self.tool_calls = tool_calls or []


class LLMProvider:
    """Fronteira com o LLM. Duas implementações: OpenAI-compat (credenciais) e stub heurístico (dev)."""

    def __init__(self, settings=None):
        self.settings = settings or get_settings()

    async def complete(
        self, system: str, history: list[dict], tools: list[dict]
    ) -> LLMResponse:
        if not self.settings.llm_api_key:
            return await self._complete_stub(system, history, tools)
        return await self._complete_openai(system, history, tools)

    async def _complete_openai(
        self, system: str, history: list[dict], tools: list[dict]
    ) -> LLMResponse:
        url = f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.llm_model,
            "messages": [{"role": "system", "content": system}, *history],
        }
        if tools:
            payload["tools"] = [{"type": "function", "function": t} for t in tools]
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            msg = response.json()["choices"][0]["message"]
        tool_calls = []
        for call in msg.get("tool_calls") or []:
            tool_calls.append(
                LLMToolCall(call["function"]["name"], json.loads(call["function"]["arguments"]))
            )
        return LLMResponse(msg.get("content"), tool_calls)

    # --- modo dev: assistente heurístico determinístico -------------------
    # ponytail: substitui o LLM quando não há credenciais; cobre os comandos
    # das US-020..025. Trocar por IA real basta configurar LLM_API_KEY.

    async def _complete_stub(self, system: str, history: list[dict], tools: list[dict]) -> LLMResponse:
        last_tool = next(
            (m for m in reversed(history) if m["role"] == "tool"),
            None,
        )
        if last_tool is not None:
            return LLMResponse(self._format_tool_result(last_tool["name"], last_tool["content"]))

        text = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        low = text.lower().strip()

        if re.search(r"\b(oi|olá|ola|bom dia|boa tarde|boa noite)\b", low) and len(low) < 30:
            return LLMResponse(
                "Olá! 👋 Sou o atendente virtual. Posso mostrar o cardápio, recomendar algo, "
                "adicionar/alterar/remover itens do seu pedido ou ver seu carrinho."
            )
        if re.search(r"\b(obrigad|valeu|brigad)\b", low):
            return LLMResponse("Por nada! 😊 Quando quiser fechar o pedido, é só me avisar.")
        if re.search(r"card[aá]pio|\bmenu\b|o que voc[êe] tem|lista", low):
            return LLMResponse("", [LLMToolCall("search_products", {"query": ""})])
        if "carrinho" in low or "meu pedido" in low or "resumo" in low:
            return LLMResponse("", [LLMToolCall("get_cart", {})])
        if re.search(r"\b(confirmo|confirmar|pode fechar|fecha o pedido)\b", low):
            return LLMResponse("", [LLMToolCall("create_order", self._order_args(low))])
        if re.search(r"\b(fechar|finalizar|fazer o pedido|quero pedir|pedir agora)\b", low):
            args = self._order_args(low)
            if args.get("delivery_type") == "entrega" and not args.get("address"):
                # US-028: endereço é obrigatório para entrega
                return LLMResponse(
                    "Pra entrega, me passa o endereço (rua, número e bairro) que eu calculo "
                    "a taxa e te mostro o resumo completo. 📍"
                )
            return LLMResponse("", [LLMToolCall("calculate_order", args)])
        if re.search(r"\b(tira|remove|cancela|retira)\b", low):
            match = re.search(r"\b(tira|remove|cancela|retira)\b\s+(?:o |a |do |da )?(.+)", low)
            if match:
                return LLMResponse(
                    "",
                    [LLMToolCall("remove_cart_item", {"item_name": match.group(2).strip()})],
                )
        match = re.search(r"\b(?:coloca|aumenta|bota)\s+mais\s*(?:(\d+|uma|um)\s*)?(.*)", low)
        if match and (match.group(2).strip() or "mais" in low):
            count = match.group(1) or ""
            delta = int(count) if count.isdigit() else 1  # "mais uma/um" = +1
            # sem nome ("coloca mais uma") = primeiro item do carrinho
            args: dict = {"quantity": delta}
            if match.group(2).strip():
                args["item_name"] = match.group(2).strip()
            return LLMResponse("", [LLMToolCall("update_cart_item", args)])
        if re.search(r"\b(adiciona|quero|coloca|bota|pede)\b", low):
            # "quero 2 pizzas e 1 coca" vira duas adições
            match = re.search(r"\b(?:adiciona|quero|coloca|bota|pede)\b\s+(?:(\d+)\s*[x ]\s*)?(.+)", low)
            if match:
                calls = []
                first_qty = int(match.group(1)) if match.group(1) else 1
                for i, part in enumerate(re.split(r"\s+e\s+", match.group(2))):
                    item = re.match(r"(?:(\d+)\s*[x ]\s*)?(.+)", part.strip())
                    name = item.group(2).strip() if item else part.strip()
                    if i == 0:
                        qty = first_qty  # quantidade do match principal
                    elif item and item.group(1):
                        qty = int(item.group(1))  # "e 1 coca" carrega a própria
                    else:
                        qty = 1
                    calls.append(LLMToolCall("add_to_cart", {"product_name": name, "quantity": qty}))
                if calls:
                    return LLMResponse("", calls)
        if re.search(r"\b(procura|busca|acha|tem)\b", low):
            match = re.search(r"\b(?:procura|busca|acha|tem)\b\s+(?:um |uma |o |a )?(.+)", low)
            if match:
                query = match.group(1).strip().rstrip("?!.,;:")
                return LLMResponse("", [LLMToolCall("search_products", {"query": query})])
        return LLMResponse(
            "Ainda não entendi! 😅 Posso: mostrar o cardápio, procurar um produto, "
            "adicionar/alterar/remover itens ou ver seu carrinho. Ex.: \"quero 2 pizzas\", "
            "\"coloca mais uma\", \"tira a coca\", \"meu pedido\"."
        )

    def _order_args(self, low: str) -> dict:
        """Extrai delivery_type/address/payment_method de uma frase de checkout."""
        args: dict = {}
        if "entrega" in low:
            args["delivery_type"] = "entrega"
        elif "retirada" in low or "retirar" in low or "buscar" in low or "pegar" in low:
            args["delivery_type"] = "retirada"
        if "pix" in low:
            args["payment_method"] = "pix"
        elif "dinheiro" in low:
            args["payment_method"] = "dinheiro"
        elif "cartão" in low or "cartao" in low:
            args["payment_method"] = "cartao"
        match = re.search(
            r"(?:rua|avenida|av\.|travessa|alameda|praça|endereço|endereco)[^,]{3,80}", low
        )
        if match:
            args["address"] = match.group(0).strip().strip(" !?.")
        return args

    def _format_tool_result(self, name: str, content: str) -> str:
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            return content
        if isinstance(result, dict) and result.get("error"):
            return result["error"]
        if name in ("get_cart", "add_to_cart", "update_cart_item", "remove_cart_item"):
            return self._format_cart(result)
        if name == "calculate_order":
            return self._format_order_summary(result)
        if name == "create_order":
            return self._format_order_created(result)
        if name == "search_products":
            return self._format_products(result)
        if name == "get_product":
            return self._format_product(result)
        if name == "get_restaurant_info":
            return result.get("resumo", json.dumps(result, ensure_ascii=False))
        return json.dumps(result, ensure_ascii=False)

    def _format_cart(self, cart: dict) -> str:
        if not cart.get("items"):
            return "Seu carrinho está vazio. 🛒 Quer que eu adicione algo do cardápio?"
        lines = [f"*Seu pedido ({cart['subtotal']}):*"]
        for item in cart["items"]:
            desc = item["product_name"]
            if item.get("variant_name"):
                desc += f" ({item['variant_name']})"
            if item.get("addons"):
                desc += " + " + ", ".join(a["name"] for a in item["addons"])
            lines.append(f"- {item['quantity']}x {desc} = {item['line_total']}")
        return "\n".join(lines)

    def _format_order_summary(self, result: dict) -> str:
        # resumo pré-confirmação (calculate_order)
        lines = [f"*Resumo do pedido ({result['delivery_type']}):*"]
        for item in result["items"]:
            desc = item["product_name"]
            if item.get("variant_name"):
                desc += f" ({item['variant_name']})"
            if item.get("addons"):
                desc += " + " + ", ".join(a["name"] for a in item["addons"])
            lines.append(f"- {item['quantity']}x {desc} = {item['line_total']}")
        lines.append(f"Subtotal: {result['subtotal']}")
        if result["delivery_type"] == "entrega":
            lines.append(f"Taxa de entrega: {result['delivery_fee']}")
        lines.append(f"*Total: {result['total']}*")
        lines.append(
            "Para confirmar, responda \"confirmo\". Se quiser entrega, inclua o endereço; "
            "e a forma de pagamento (pix, dinheiro ou cartão)."
        )
        return "\n".join(lines)

    def _format_order_created(self, result: dict) -> str:
        lines = [f"*Pedido #{result['id']} confirmado!* 🎉", f"Status: {result['status']}"]
        if result["delivery_type"] == "entrega":
            lines.append(f"Entrega em: {result['address']}")
        else:
            lines.append("Retirada no local")
        lines.append(f"Pagamento: {result['payment_method']}")
        lines.append(f"Total: {result['total']}")
        lines.append("Obrigado! Quando quiser pedir de novo, é só chamar. 😊")
        return "\n".join(lines)

    def _format_products(self, result: dict) -> str:
        products = result.get("products", [])
        if not products:
            return "Não encontrei produtos com esse nome. 😕 Quer ver o cardápio completo?"
        lines = ["*Cardápio:*"]
        for p in products:
            if p.get("variants"):
                prices = ", ".join(f"{v['name']} {v['price']}" for v in p["variants"])
                lines.append(f"- {p['name']}: {prices}")
            else:
                lines.append(f"- {p['name']}: {p['base_price']}")
                for a in p.get("addons", []):
                    lines.append(f"   + {a['name']} {a['price']}")
        lines.append("É só falar \"quero\" + nome + quantidade que adiciono ao pedido. 😉")
        return "\n".join(lines)

    def _format_product(self, product: dict) -> str:
        if not product:
            return "Produto não encontrado."
        return self._format_products({"products": [product]})