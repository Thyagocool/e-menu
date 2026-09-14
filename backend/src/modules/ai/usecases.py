import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.ai.prompts import PromptService
from src.modules.ai.provider import MAX_TOOL_ROUNDS, LLMProvider
from src.modules.ai.tools import ToolRegistry
from src.modules.restaurant.repository import RestaurantRepository
from src.modules.whatsapp.repository import ConversationRepository, MessageRepository

logger = logging.getLogger(__name__)

TOOLS_WITH_CUSTOMER = {
    "get_cart",
    "add_to_cart",
    "update_cart_item",
    "remove_cart_item",
    "calculate_order",
    "create_order",
}


class AIService:
    def __init__(
        self,
        llm: LLMProvider | None = None,
        registry: ToolRegistry | None = None,
        prompts: PromptService | None = None,
        conversations: ConversationRepository | None = None,
        messages: MessageRepository | None = None,
        restaurants: RestaurantRepository | None = None,
    ):
        self.llm = llm or LLMProvider()
        self.registry = registry or ToolRegistry()
        self.prompts = prompts or PromptService()
        self.conversations = conversations or ConversationRepository()
        self.messages = messages or MessageRepository()
        self.restaurants = restaurants or RestaurantRepository()

    async def handle_message(self, session: AsyncSession, conversation_id: int, text: str) -> str:
        conversation = await self.conversations.get(session, conversation_id)
        # primitivos: expire_all() das tools invalida objetos ORM da sessão
        customer_id, restaurant_id = conversation.customer_id, conversation.restaurant_id
        restaurant = await self.restaurants.get(session, restaurant_id)
        history = await self.messages.recent(session, conversation_id, limit=10)

        system = self.prompts.build_system(restaurant)
        messages = [
            {
                "role": "assistant" if m.direction == "outbound" else "user",
                "content": m.content,
            }
            for m in history
        ]
        response = await self.llm.complete(system, messages, self.registry.list_schemas())

        for _ in range(MAX_TOOL_ROUNDS):
            if not response.tool_calls:
                break
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": f"call_{i}",
                            "type": "function",
                            "function": {"name": c.name, "arguments": c.arguments},
                        }
                        for i, c in enumerate(response.tool_calls)
                    ],
                }
            )
            for call in response.tool_calls:
                args = await self._adapt_args(session, customer_id, restaurant_id, call.name, call.arguments)
                result = await self.registry.execute(session, call.name, **args)
                logger.info("tool %s -> %s", call.name, str(result)[:120])
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": "call_0",
                        "name": call.name,
                        "content": json.dumps(result, default=str),
                    }
                )
            response = await self.llm.complete(system, messages, self.registry.list_schemas())

        return response.content or "Desculpe, não consegui processar. Tente de novo?"

    async def _adapt_args(
        self, session: AsyncSession, customer_id: int, restaurant_id: int, name: str, args: dict
    ) -> dict:
        """Resolve customer_id/restaurant_id e product_name/item_name vindos do LLM (ou do stub)."""
        args = dict(args)
        if name in TOOLS_WITH_CUSTOMER and "customer_id" not in args:
            args["customer_id"] = customer_id
        if name in {"get_restaurant_info", "search_products"} and "restaurant_id" not in args:
            args["restaurant_id"] = restaurant_id
        if name in ("add_to_cart",) and "product_id" not in args and args.get("product_name"):
            products = await self.registry.execute(
                session, "search_products", restaurant_id=restaurant_id, query=args.pop("product_name")
            )
            found = products.get("products")
            if not found:
                args["product_id"] = -1  # tool vai responder "Produto indisponível"
            else:
                args["product_id"] = found[0]["id"]
                if found[0]["variants"] and "variant_id" not in args:
                    args["variant_id"] = found[0]["variants"][0]["id"]
        needs_item = name in ("remove_cart_item", "update_cart_item") and "item_id" not in args
        if needs_item:
            cart = await self.registry.execute(session, "get_cart", customer_id=customer_id)
            items = cart.get("items", [])
            term = args.pop("item_name", "").lower()
            if term:
                match = next((i for i in items if term in i["product_name"].lower()), None)
            else:
                match = min(items, key=lambda i: i["id"]) if items else None  # item mais antigo
            args["item_id"] = match["id"] if match else -1
            if name == "update_cart_item":
                delta = args.pop("quantity", 1)
                args["quantity"] = match["quantity"] + delta if match else delta
        return args