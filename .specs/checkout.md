# Checkout — Status do desenvolvimento

Resumo do que já foi desenvolvido, sprint por sprint.

## Sprint 0 — Fundação ✅

**Status: desenvolvida e validada (DoD cumprido).**

### Backend (`backend/`)
- FastAPI + Uvicorn, Python 3.12
- Config por environment via `pydantic-settings` (`src/config/__init__.py`, `.env.example`)
- Logging básico estruturado no `src/main.py`
- SQLAlchemy 2 (async + asyncpg), engine/session em `src/infra/database/__init__.py`
- Alembic configurado com env async (`alembic/env.py`)
- Health check `GET /health` valida conexão com o banco
- Handler global de exceções
- Lint: ruff — passando. Testes: pytest — passando

### Frontend (`frontend/`)
- Vite 8 + React 19 + TypeScript
- Routing: react-router-dom (`src/app/App.tsx`, `Layout.tsx`)
- React Query provisionado
- Design system mínimo em `src/shared/styles/global.css`
- Estrutura modular: `src/modules/` + `src/shared/`
- Proxy `/api` → backend no dev; nginx com proxy + SPA fallback na 8080

### Infra
- `docker-compose.yml`: Postgres 16 (host `5434`), Redis 7, backend `8000`, frontend `8080`
- Backend roda `alembic upgrade head` antes de subir
- CI: `.github/workflows/ci.yml`

## Sprint 1 — Restaurante + catálogo ✅

**Status: desenvolvida e validada (DoD cumprido).**

### Backend — módulos
- `src/modules/restaurant/` — Restaurant (name, slug único, whatsapp, taxa, status) + slugify automático
- `src/modules/category/` — Category (soft delete via `deleted_at`, 409 se tiver produtos)
- `src/modules/product/` — Product, ProductVariant, Addon, ProductAddon (relação many-to-many)
- `src/modules/upload/` — `POST /upload` (JPG/PNG/WEBP, máx 5MB, salva em `media/`, serve em `/media`)

### API (conforme plano)
| Recurso | Rotas |
|---|---|
| Restaurant | `POST /restaurants`, `GET/PUT /restaurants/:id` |
| Category | `GET/POST /restaurants/:id/categories`, `PUT/DELETE /categories/:id` |
| Product | `GET/POST /restaurants/:id/products`, `GET/PUT/DELETE /products/:id` |
| Variant | `POST /products/:id/variants`, `PUT/DELETE /variants/:id` |
| Addon | `GET/POST /restaurants/:id/addons`, `PUT/DELETE /addons/:id` |
| Associação | `POST /products/:id/addons`, `DELETE /products/:id/addons/:addon_id` |
| Upload | `POST /upload` |

### Regras aplicadas
- Slug único (409 em duplicado); categoria de outro restaurante → 400; adicional de outro restaurante → 400
- Isolamento por `restaurant_id` nas rotas de lista (testado)
- Preços `Numeric(10,2)` com validação `>= 0`; produto inativo não é removido do catálogo
- Soft delete: Category e Product (listas e leitura filtram `deleted_at`)
- Datas timezone-aware (`DateTime(timezone=True)` + `utcnow()`)

### Migration
- `0002_catalog` — cria `restaurants`, `categories`, `products`, `product_variants`, `addons`, `product_addons`

### Testes
- 24 testes passando (CRUD, validações, isolamento, soft delete, associações)
- Infra de teste: `tests/conftest.py` com migrations + limpeza entre testes + `AsyncClient`

### Frontend — admin
- `RestaurantPage` (`/restaurante`): criar/editar restaurante, salva id no localStorage
- `CategoriesPage` (`/categorias`): criar/renomear/excluir categorias
- `ProductsPage` (`/produtos`): lista com thumb, ativar/desativar, excluir
- `ProductFormPage` (`/produtos/novo`, `/produtos/:id`): form completo com variações, adicionais (checkbox) e upload de imagem
- `AddonsPage` (`/adicionais`): CRUD de adicionais
- Dashboard com cards de navegação
- `src/shared/services/api.ts` (fetch wrapper) e `src/shared/utils/restaurant.ts`

- Lint: oxlint — passando. Build: tsc + vite — passando

### Validado E2E (docker)
- Restaurante → Categoria → Produto → Variação → Adicional → Associação → Detalhe com tudo embutido
- Upload PNG aceito; arquivo inválido rejeitado com 400

### Como rodar
```sh
docker compose up -d --build
# admin: http://localhost:8080 | API: http://localhost:8000 | health: /health
# testes backend: cd backend && .venv/bin/pytest
```

### Refatoração — camadas repository + usecases
- Routers viraram finos (só HTTP): `src/modules/{restaurant,category,product,upload}/routes.py`
- Cada módulo agora tem `repository.py` (queries/persistência, sem commit) e `usecases.py` (regras de negócio + commit)
- Erros de negócio via `DomainError(status_code, message)` (exceção registrada no `main.py`) em vez de `HTTPException` nos routers
- Validações centralizadas nos usecases: slug único, categoria/adicional do restaurante, 404s, 409 com produtos, soft delete
- Upload delegado a `src/infra/storage/save_image` (validação de formato/tamanho + salvamento)
- API inalterada — 24 testes + ruff passando

## Sprint 2 — Cardápio público ✅

**Status: desenvolvida e validada (DoD cumprido).**

### Backend — módulo `public`
- `GET /public/restaurants/:slug/menu` — restaurante ativo + categorias ativas + produtos ativos, agrupados por categoria (produtos sem categoria em `uncategorized_products`)
- `GET /public/restaurants/:slug/products/:id` — detalhe público do produto (US-015)
- Filtros: só expõe restaurante/categoria/produto/variação/adicional com status `active`; slug inexistente ou restaurante inativo → 404
- `VariantCreate` ganhou campo opcional `status` (variações podem ser inativadas)
- Arquitetura: `repository` + `usecases` + router fino, seguindo a refatoração anterior

### Testes
- 8 testes novos (`tests/test_public.py`) — 32 no total, ruff limpo
- Cobrem: agrupamento, sem categoria, 404 slug, 404 restaurante inativo, produto/variação inativa ocultos, isolamento entre restaurantes

### Frontend — página pública (`/cardapio/:slug`)
- `MenuPage` mobile-first fora do layout admin
- Header com nome, horário, endereço e taxa de entrega
- Chips de navegação sticky por categoria
- Cards de produto: foto (ou placeholder), nome, descrição, preço ("a partir de" quando há variações)
- Sheet de detalhe (US-015): variação (radio), adicionais (checkbox), observação e quantidade
- Botão "Pedir pelo WhatsApp" (US-016): link `wa.me` com mensagem pré-preenchida identificando restaurante, produto, variação, adicionais, observação e quantidade
- Build tsc + vite e oxlint passando

### Validado E2E (docker)
- `GET /public/restaurants/pizzaria-sol/menu` com categoria, produto, variações e adicionais embutidos
- `/cardapio/pizzaria-sol` servido pelo nginx (SPA fallback)

### Como acessar
```sh
# admin: http://localhost:8080 | cardápio: http://localhost:8080/cardapio/{slug}
```

## Sprint 3 — WhatsApp ✅

**Status: desenvolvida e validada (DoD cumprido).**

### Backend — módulo `whatsapp`
- `WhatsAppProvider` (`src/modules/whatsapp/provider.py`): fronteira com a WhatsApp Cloud API (Meta)
  - `verify_hub` — verificação `GET` do webhook (`hub.mode/verify_token/challenge`)
  - `validate_signature` — `X-Hub-Signature-256` (HMAC do `app_secret`); sem segredo configurado, aceita (modo dev)
  - `parse_event` — normaliza payload → `WhatsAppEvent` (message_id, telefone, nome, número do restaurante, texto)
  - `send` — envia mensagem pela Cloud API; sem credenciais, vira stub com log (dev)
- `POST /webhooks/whatsapp` — valida assinatura, normaliza, identifica restaurante (por `whatsapp_phone` normalizado) e persiste a mensagem
- `GET /webhooks/whatsapp` — verificação de subscription da Meta
- Persistência: `Customer` (unique restaurante+telefone), `Conversation` (unique restaurante+cliente — US-019), `Message` (unique `external_message_id` para idempotência)
- Idempotência: reenvio do webhook não duplica (mesmo `message_id` retornado; unique no banco como rede de segurança)
- Config: `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` (vazios = dev)
- `httpx` movido para dependências de runtime (era só de dev)
- Rota trata body JSON inválido → 400 (antes caía no handler global → 500)

### Testes
- 11 testes novos (`tests/test_whatsapp.py`) — 43 no total, ruff limpo
- Cobrem: criação de customer/conversation/message, idempotência, reuso de sessão, isolamento entre restaurantes, payload inválido (400), restaurante desconhecido (404), assinatura (aceita/válida/rejeitada), `verify_hub`, send stub

### Validado E2E (docker)
- Envio com payload Meta → 200 + `message_id`; reenvio → mesmo `message_id`
- Body inválido → 400; número de restaurante desconhecido → 404

### Como rodar em dev
```sh
curl -X POST localhost:8000/webhooks/whatsapp -H 'Content-Type: application/json' \
  -d '{"entry":[...]}'   # payload padrão da Meta Cloud API
```

## Sprint 4 — Carrinho ✅

**Status: desenvolvida e validada (DoD cumprido).**

### Módulo `cart` (backend)
- Models: `Cart` (1 por customer, unique), `CartItem` (unit_price = snapshot no momento da adição), `CartItemAddon` (price = snapshot)
- Endpoints:
  - `GET /customers/{customer_id}/cart` — carrinho completo (itens + subtotal); carrinho lazy (cria vazio se não existe)
  - `POST /cart/items` — adiciona item (201); `PUT /cart/items/{item_id}` — altera quantidade; `DELETE /cart/items/{item_id}` — remove; `DELETE /customers/{customer_id}/cart` — limpa
- Regras (todas no backend):
  - produto precisa estar **ativo** e ser do **mesmo restaurante** do customer (restaurant_id sempre validado)
  - produto com variações ativas **exige** variação ativa; sem variações, variação é recusada
  - adicionais devem estar **ativos**, ser do mesmo restaurante **e vinculados ao produto**
  - item repetido (mesmo produto + variação + mesmos adicionais) **soma quantidade** (teto 99)
  - quantidade válida 1–99 (validate no schema)
  - preço vem do backend: `line_total = (unit_price + Σ addons) × qty`; `subtotal = Σ line_total` (Decimal)
- Isolamento: carrinho pertence ao customer (que pertence a um restaurante) — nenhum carrinho cruza restaurantes
- Webhook do WhatsApp **agora devolve `customer_id`** na resposta (a IA vai precisar nas tools da Sprint 5)
- Nota técnica: `session.get()` dispara autoflush que marca a collection vazia de um objeto recém-criado como *unloaded* → iterar dispara IO síncrona (MissingGreenlet no async); correção: inicializar `cart.items = []` no create (1 linha)

### Testes
- 17 testes novos (`tests/test_cart.py`) — **60 no total**, ruff limpo
- Cobertos: subtotais fortes (múltiplos itens, variações, adicionais, quantidades), snapshot de preços, merge de itens, update/remove/clear, produto/variação/adicionais inválidos, quantity 0 (422), customer inexistente (404), isolamento entre customers

### Validado E2E (docker)
- Fluxo completo: add pizza (variação + adicional) `106.00` → + refri `124.00` → update `112.00` → remove `106.00` → get `106.00` → clear `0.00`

## Sprint 5 — Garçom IA ✅

Atendimento conversacional via WhatsApp com LLM (ou assistente heurístico em dev): o webhook responde ao cliente com cardápio, busca, carrinho, adição/alteração/remoção de itens — as US-020..026 da Fase 6 do BA.md.

### O que entrou
- `Restaurant.description` (String 2000) — modelo + schemas + migration `0005_restaurant_description.py`
- Settings LLM (`LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`; chave vazia = modo dev)
- `src/modules/ai/`:
  - `provider.py` — `LLMProvider` OpenAI-compat (`/chat/completions` com tools) + stub heurístico determinístico em pt-BR (regras: saudação, cardápio, busca, adicionar "quero 2 pizzas e 1 coca", "coloca mais uma", remover, ver carrinho), `MAX_TOOL_ROUNDS=3`
  - `tools.py` — `ToolRegistry` com 7 tools (get_restaurant_info, search_products, get_product, get_cart, add_to_cart, update_cart_item, remove_cart_item) com schemas JSON
  - `prompts.py` — system prompt do garçom com regra de confirmação explícita (US-026)
  - `usecases.py` — `AIService.handle_message`: histórico recente → LLM → loop de tools → resposta; `_adapt_args` injeta `customer_id`/`restaurant_id` (contexto da conversa), resolve `product_name` → `product_id` (1ª variação ativa) e `item_name` → `item_id`; "coloca mais uma" sem nome = item mais antigo
- Webhook do WhatsApp agora: salva a resposta como `Message` outbound (**2 mensagens por interação**: inbound + outbound), devolve `reply` no body; reenvio idempotente não re-responde
- Busca textual com singularização básica ("pizzas" acha "Pizza")
- `.env.example` com as 3 vars `LLM_*`

### Lições (SQLAlchemy async)
- `expire_all()` das tools do carrinho invalida objetos ORM da sessão compartilhada → capturar `customer_id`/`restaurant_id` como primitivos antes do loop de tools; `message.id` também é lido antes
- Ordem dos itens no dump do carrinho não é garantida → testes buscam por `product_name`, "sem nome" resolve pelo menor `item_id`

### Testes
- 11 testes novos em `tests/test_ai.py` (fluxo completo via webhook: saudação, cardápio, busca, adição com quantidade/variação, merge, update, remove, carrinho vazio/cheio, produto inexistente, remover item que não está no carrinho) + ajuste dos testes do whatsapp (contagem de mensagens) — **73 no total**, ruff limpo
- Cobertos também pela suíte: idempotência com resposta (`Message` não duplica), isolamento entre restaurantes

### Validado E2E (docker)
- Fluxo: "quero 2 pizzas" → `2x Pizza Pepperoni (Grande) = 110.00`; "tira a coca" (inexistente) → "Item não encontrado" sem alterar o carrinho; "meu pedido" → pedido atual; "coloca mais uma" → `3x ... = 165.00`; "cardápio" → lista com preços
- Stub heurístico em prod de dev; com `LLM_API_KEY` + tools o mesmo fluxo funciona com IA real sem mudança de código

## Sprint 6 — Pedido / Checkout ⏳

Implementar pedido (US-026..028): fechar pedido após confirmação explícita, snapshot final no pedido, Webhook assíncrono (ver `.specs/PLANO_DESENVOLVIMENTO.md`)