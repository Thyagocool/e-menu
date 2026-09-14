# Plano de Desenvolvimento — SaaS Cardápio + WhatsApp + Garçom IA

## Status das Sprints

| Sprint | Status |
|--------|--------|
| Sprint 0 — Fundação | ✅ Desenvolvida |
| Sprint 1 — Restaurante + catálogo | ✅ Desenvolvida |
| Sprint 2 — Cardápio público | ✅ Desenvolvida |
| Sprint 3 — WhatsApp | Pendente |
| Sprint 4 — Carrinho | ✅ Desenvolvida |
| Sprint 5 — IA | ✅ Desenvolvida |
| Sprint 6 — Checkout | ✅ Desenvolvida |
| Sprint 7 — Pedidos | ⏳ Próxima |
| Sprint 7 — Pedidos | Pendente |
| Sprint 8 — Dashboard | Pendente |
| Sprint 9 — Hardening | Pendente |

> Detalhes por sprint: ver `.specs/checkout.md`.

## Objetivo técnico

Implementar o MVP definido em `BA.md` priorizando um fluxo vertical funcional:

**Restaurante → Produto → Cardápio → WhatsApp → IA → Carrinho → Checkout → Pedido**

Não desenvolver funcionalidades fora do escopo sem solicitação.

Princípios:
- YAGNI
- modularidade
- soluções simples e explícitas
- backend como autoridade das regras
- LLM como interface conversacional
- WhatsApp como canal
- não criar abstrações prematuras

# Stack inicial

## Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic
- Redis

## Frontend
- React
- TypeScript
- Vite
- React Query

## Infra
- Docker
- PostgreSQL
- Redis
- Object Storage
- CI/CD

## IA
- provider de LLM
- tool calling
- RAG para conhecimento textual
- tools para operações transacionais

# Estrutura backend

```text
src/
├── modules/
│   ├── restaurant/
│   ├── category/
│   ├── product/
│   ├── customer/
│   ├── conversation/
│   ├── cart/
│   ├── order/
│   ├── whatsapp/
│   └── ai/
├── infra/
│   ├── database/
│   ├── whatsapp/
│   ├── ai/
│   └── storage/
└── config/
```

Cada módulo deve concentrar route/controller/usecase/schema/repository quando aplicável.

Evitar um `models/` global gigante.

# Estrutura frontend

```text
src/
├── modules/
│   ├── restaurant/
│   ├── category/
│   ├── product/
│   ├── menu/
│   ├── order/
│   └── dashboard/
├── shared/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   └── utils/
└── app/
```

Separar claramente Admin e Public Menu.

# Sprint 0 — Fundação ✅ DESENVOLVIDA

## Backend
- criar projeto FastAPI
- configuração por environment
- logging
- SQLAlchemy
- Alembic
- PostgreSQL
- health check
- tratamento base de erros

## Frontend
- criar projeto
- routing
- environment
- layout base
- design system mínimo

## Infra
- Docker Compose
- PostgreSQL
- Redis
- lint
- testes
- CI básico

Definition of Done:
- backend sobe
- frontend sobe
- banco conecta
- migration executa
- health check responde
- lint/testes passam

# Sprint 1 — Restaurante + catálogo ✅ DESENVOLVIDA

Implementar entidades:
- Restaurant
- Category
- Product
- ProductVariant
- Addon
- ProductAddon

Implementar CRUDs necessários.

Frontend:
- dashboard inicial
- categorias
- produtos
- formulário de produto
- variações
- adicionais
- upload de imagem

Testes:
- CRUD
- validações
- isolamento por restaurant_id

# Sprint 2 — Cardápio público ✅ DESENVOLVIDA

Endpoint:

```text
GET /public/restaurants/:slug/menu
```

Frontend:
- página pública
- categorias
- cards de produto
- fotos
- detalhes
- variações
- adicionais
- responsividade mobile

O cardápio deve ser visual e comercialmente apresentável.

Não implementar carrinho web completo no MVP. O objetivo é iniciar o WhatsApp.

# Sprint 3 — WhatsApp ✅ DESENVOLVIDA

Criar abstração:

```text
WhatsAppProvider
```

Responsabilidades:
- validar webhook
- receber mensagens
- enviar mensagens
- normalizar eventos
- identificar usuário
- idempotência

Endpoints:

```text
POST /webhooks/whatsapp
```

Persistir:
- Customer
- Conversation
- Message

Não acoplar o domínio inteiro ao provider.

# Sprint 4 — Carrinho ✅ DESENVOLVIDA

Implementar:
- Cart
- CartItem
- CartItemAddon

Domínio:

```text
addItem()
removeItem()
updateQuantity()
calculateSubtotal()
clear()
```

Regras:
- produto precisa estar ativo
- preço vem do backend
- quantidade válida
- adicionais válidos
- restaurant_id sempre validado

Criar testes unitários fortes para cálculo.

# Sprint 5 — IA ✅ DESENVOLVIDA

Criado (ver `.specs/checkout.md` Sprint 5):

```text
LLMProvider (OpenAI-compat + stub heurístico dev)
ToolRegistry (7 tools com schemas JSON)
PromptService
AIService (loop de tools, adaptação de args)
```

Integração no webhook do WhatsApp: mensagem → IA → tool → backend → resposta salva como outbound e enviada. `LLM_API_KEY` vazio = assistente heurístico determinístico (mesma interface, troca só configurando a chave).

# Sprint 6 — Checkout ✅ DESENVOLVIDA

Implementado (ver `.specs/checkout.md` Sprint 6):

- `Order` + `OrderItem` (snapshot comercial) — migration `0006`
- calculo de total pelo backend (subtotal + taxa fixa)
- retirada/entrega + endereço obrigatório pra entrega
- pagamento: pix / dinheiro / cartão (sem gateway no MVP)
- resumo pré-confirmação e criação só após confirmação explícita
- tools: `calculate_order`, `create_order`

Garantias:
- total calculado pelo backend
- pedido vazio não pode ser criado
- produto inativo não pode ser vendido
- preço não vem do LLM
- pedido só nasce após confirmação

# Sprint 7 — Pedidos

Implementar:
- criação
- listagem
- detalhes
- alteração de status

Status:

```text
RECEIVED
CONFIRMED
PREPARING
READY
DELIVERING
COMPLETED
CANCELLED
```

Frontend:
- lista
- filtros simples
- detalhe
- atualização de status

# Sprint 8 — Dashboard

Exibir:
- pedidos hoje
- faturamento hoje
- pedidos pendentes
- produtos mais pedidos

Evitar BI complexo.

Implementar QR Code do cardápio.

# Sprint 9 — Hardening

Implementar:
- autenticação
- autorização
- tenant isolation
- rate limiting
- logs
- erros
- idempotência
- validações
- observabilidade
- testes de integração
- E2E

# Fluxo E2E obrigatório

```text
abrir cardápio
→ selecionar produto
→ iniciar WhatsApp
→ receber resposta da IA
→ adicionar produto
→ adicionar adicional
→ consultar carrinho
→ escolher entrega
→ informar endereço
→ escolher pagamento
→ receber resumo
→ confirmar
→ pedido criado
→ pedido aparece no dashboard
```

Esse é o teste de ouro do MVP.

# API inicial

## Restaurant

```text
POST /restaurants
GET /restaurants/:id
PUT /restaurants/:id
```

## Category

```text
GET /restaurants/:id/categories
POST /restaurants/:id/categories
PUT /categories/:id
DELETE /categories/:id
```

## Product

```text
GET /restaurants/:id/products
POST /restaurants/:id/products
GET /products/:id
PUT /products/:id
DELETE /products/:id
```

## Public

```text
GET /public/restaurants/:slug/menu
GET /public/restaurants/:slug/products/:id
```

## WhatsApp

```text
POST /webhooks/whatsapp
```

## Cart

```text
GET /customers/:id/cart
POST /cart/items
PUT /cart/items/:id
DELETE /cart/items/:id
```

## Orders

```text
GET /restaurants/:id/orders
GET /orders/:id
POST /orders
PUT /orders/:id/status
```

# Segurança

Toda operação privada deve validar:

```text
authenticated_user
+
allowed_restaurant_id
```

Toda entidade operacional deve ter `restaurant_id` direta ou indiretamente.

Nunca confiar em:
- restaurant_id vindo livremente do frontend
- preço vindo do frontend
- total vindo do frontend
- preço/total informado pelo LLM

# Idempotência

Webhook externo pode ser reenviado.

Usar `external_message_id` ou equivalente como chave idempotente.

Uma mensagem não pode:
- ser processada duas vezes
- adicionar item duas vezes
- criar dois pedidos

# Snapshot de pedido

Ao criar pedido, copiar para OrderItem:
- nome
- variação
- quantidade
- preço unitário
- total

E para adicionais:
- nome
- quantidade
- preço
- total

Alterações futuras no catálogo não podem modificar pedidos históricos.

# Testes

## Unitários
- carrinho
- adicionais
- quantidade
- subtotal
- taxa
- total
- regras de pedido

## Integração
- repositories
- APIs
- webhook
- tools
- banco

## E2E
Executar fluxo completo do consumidor até dashboard.

# Definition of Done

Uma tarefa só está pronta quando:
- código implementado
- validações implementadas
- testes relevantes passando
- lint passando
- integração funcionando
- erros tratados
- documentação mínima atualizada
- sem hardcode indevido
- sem `any` desnecessário
- sem acesso direto indevido ao banco
- sem TODO crítico

# Ordem de execução

Prioridade:

```text
1. Fundação
2. Restaurant
3. Category
4. Product
5. Public Menu
6. WhatsApp
7. Customer/Conversation
8. Cart
9. AI tools
10. Checkout
11. Order
12. Dashboard
13. QR Code
14. Hardening
15. E2E
```

# Estratégia de implementação

Não construir todo o CRUD antes de validar o fluxo principal.

Depois da fundação, buscar o primeiro vertical slice:

```text
Restaurant
→ Product
→ Public Menu
→ WhatsApp
→ AI
→ Cart
→ Order
```

Após esse fluxo funcionar, completar funcionalidades administrativas e refinamentos.

# Regra para o agente

Antes de implementar uma tarefa:

1. Ler `BA.md`.
2. Identificar US e critérios envolvidos.
3. Verificar código existente.
4. Não duplicar abstrações.
5. Implementar o menor conjunto necessário.
6. Testar.
7. Atualizar documentação quando necessário.

Não implementar feature não solicitada apenas porque "seria interessante".

Se uma decisão técnica tiver impacto relevante no domínio, documentar a decisão antes de criar uma abstração.

# Resultado esperado

Ao final do MVP:

Um restaurante consegue cadastrar seu cardápio, publicar uma URL/QR Code e receber pedidos através do WhatsApp, onde uma IA atua como garçom virtual, utilizando ferramentas seguras do backend para consultar produtos, montar carrinhos e finalizar pedidos.

O produto só deve ser considerado MVP concluído quando o fluxo completo funcionar de ponta a ponta.
