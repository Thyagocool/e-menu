# MVP SaaS — Cardápio + WhatsApp + Garçom IA

## Objetivo

Desenvolver um SaaS para restaurantes, lanchonetes, pizzarias e pequenos estabelecimentos que permita:

1. Cadastrar restaurante.
2. Cadastrar categorias e produtos.
3. Publicar um cardápio visual.
4. Disponibilizar o cardápio por URL/QR Code.
5. Levar o consumidor ao WhatsApp.
6. Atender o consumidor com um agente de IA.
7. Montar o pedido por conversa.
8. Coletar entrega/retirada e pagamento.
9. Confirmar e registrar o pedido.
10. Permitir ao restaurante acompanhar os pedidos.

## Proposta de valor

> Transforme seu cardápio em um vendedor que atende pelo WhatsApp.

## Escopo do MVP

### Backoffice
- Restaurante e configurações básicas
- Categorias
- Produtos
- Imagens
- Preços
- Variações/tamanhos
- Adicionais
- Ativação/inativação
- Configuração do WhatsApp
- Pedidos
- Status dos pedidos

### Cardápio público
- URL pública por restaurante
- Categorias
- Produtos e fotos
- Descrição e preço
- Variações e adicionais
- Início do pedido pelo WhatsApp

### WhatsApp + IA
- Webhook de entrada
- Envio de mensagens
- Identificação de restaurante/cliente
- Conversação persistida
- Consulta ao catálogo
- Recomendações
- Carrinho conversacional
- Checkout
- Criação do pedido

### Fora do MVP
- App mobile
- Marketplace
- Delivery próprio
- Estoque
- Fiscal/NF-e
- ERP
- Fidelidade/cashback
- Cupons
- Gateway de pagamento próprio
- iFood e outros marketplaces
- KDS/impressora
- Gestão financeira
- Analytics avançado

# Atores

## Proprietário/operador
Configura restaurante, catálogo e acompanha pedidos.

## Consumidor
Consulta cardápio, conversa com IA e realiza pedidos.

## Agente IA
É o garçom virtual. Interpreta linguagem natural e usa ferramentas do backend.

## Administrador da plataforma
Administração técnica do SaaS.

# Princípio fundamental

O LLM não controla diretamente o banco nem regras financeiras.

```text
WhatsApp
  ↓
Webhook
  ↓
Orquestrador IA
  ↓
LLM
  ↓
Tool / Function
  ↓
Backend
  ↓
Banco
```

O backend é a autoridade sobre:
- produtos
- preços
- disponibilidade
- carrinho
- totais
- pedidos

# User Stories

## Fase 0 — Fundação

### US-000 — Criar base técnica
**Como** equipe de desenvolvimento  
**Quero** uma base backend/frontend configurada  
**Para** desenvolver o produto com consistência.

Critérios:
- projetos criados
- ambientes configurados
- banco configurado
- migrations
- lint
- testes
- Docker
- health check

## Fase 1 — Restaurante

### US-001 — Criar restaurante
**Como** proprietário  
**Quero** cadastrar meu restaurante  
**Para** utilizar a plataforma.

Critérios:
- nome obrigatório
- slug único
- telefone/WhatsApp
- status ativo/inativo

### US-002 — Visualizar configurações
Exibir nome, WhatsApp, endereço, horário, atendimento e taxa.

### US-003 — Editar restaurante
Permitir atualização dos dados.

## Fase 2 — Catálogo

### US-004 — Criar categoria
Categorias organizam produtos.

### US-005 — Editar categoria
Nome, descrição, ordem e status.

### US-006 — Excluir categoria
Preferir soft delete. Categoria com produtos deve ser tratada antes da remoção.

### US-007 — Criar produto
Campos: nome, descrição, categoria, imagem, preço e status.

### US-008 — Editar produto
Alterar dados do produto.

### US-009 — Ativar/desativar produto
Produto inativo não pode ser vendido.

### US-010 — Adicionar imagem
Upload, validação de formato/tamanho e URL persistida.

## Fase 3 — Variações e adicionais

### US-011 — Criar variação
Ex.: Média R$39,90 / Grande R$49,90.

### US-012 — Criar adicional
Ex.: Borda Catupiry +R$8.

### US-013 — Associar adicionais ao produto
Suportar adicional opcional e preço adicional. Evitar regras excessivamente complexas no MVP.

## Fase 4 — Cardápio público

### US-014 — Visualizar cardápio
URL conceitual: `/cardapio/{restaurant_slug}`.

### US-015 — Visualizar produto
Exibir imagem, nome, descrição, variação, adicionais, observação e quantidade.

### US-016 — Iniciar pedido pelo WhatsApp
A mensagem deve identificar o restaurante e, quando aplicável, o produto/variação selecionado.

## Fase 5 — WhatsApp

### US-017 — Receber mensagem
Webhook, validação, identificação do cliente e persistência.

### US-018 — Enviar mensagem
Suportar texto e formatos estruturados quando disponíveis.

### US-019 — Identificar conversa
Sessão por restaurante + consumidor.

## Fase 6 — Garçom IA

### US-020 — Responder dúvidas
Consultar catálogo e informações do restaurante.

### US-021 — Recomendar produtos
Ex.: opções até determinado valor.

### US-022 — Adicionar produto
Interpretar produto, variação e quantidade.

### US-023 — Alterar quantidade
Ex.: “coloca mais uma”.

### US-024 — Remover item
Ex.: “tira a Coca”.

### US-025 — Consultar carrinho
Retornar o carrinho real.

### US-026 — Confirmar pedido
Pedido só deve ser criado após confirmação explícita.

## Fase 7 — Checkout

### US-027 — Escolher entrega ou retirada
Opções: retirada / entrega.

### US-028 — Coletar endereço
Para entrega, coletar endereço necessário.

### US-029 — Calcular taxa
MVP usa taxa fixa configurada pelo restaurante.

### US-030 — Escolher pagamento
Pix, dinheiro ou cartão na entrega. Sem pagamento online no MVP.

### US-031 — Confirmar checkout
Exibir resumo final antes de criar o pedido.

## Fase 8 — Pedidos

### US-032 — Criar pedido
Salvar snapshot comercial dos itens.

### US-033 — Listar pedidos
Número, cliente, horário, valor, tipo e status.

### US-034 — Visualizar pedido
Detalhes completos.

### US-035 — Alterar status
`RECEIVED`, `CONFIRMED`, `PREPARING`, `READY`, `DELIVERING`, `COMPLETED`, `CANCELLED`.

## Fase 9 — Operação

### US-036 — Dashboard
Pedidos hoje, faturamento, pendentes e produtos mais pedidos.

### US-037 — QR Code
Gerar QR Code para o cardápio público.

## Fase 10 — Qualidade

### US-038 — Isolamento entre restaurantes
Nenhum tenant acessa dados de outro.

### US-039 — Autorização
Validar usuário e restaurante permitido.

### US-040 — Idempotência
Eventos duplicados do WhatsApp não podem duplicar mensagens ou pedidos.

### US-041 — Logs
Registrar webhooks, erros, IA/tools e criação de pedidos sem registrar dados sensíveis desnecessários.

# Regras de negócio

- Preços são determinados pelo backend.
- Produto inativo não pode entrar no carrinho.
- Pedido exige confirmação explícita.
- Pedido guarda snapshot dos dados comerciais.
- Toda entidade operacional pertence a um restaurante.
- Webhooks externos precisam ser idempotentes.
- Carrinho é controlado pelo backend.
- Total é calculado pelo backend.
- Conversas devem ser persistidas.
- IA não recebe SQL genérico nem acesso direto ao banco.

# Modelo conceitual

## Restaurant
`id, name, slug, phone, whatsapp_phone, address, opening_hours, delivery_fee, status, created_at, updated_at`

## Category
`id, restaurant_id, name, description, sort_order, status, created_at, updated_at, deleted_at`

## Product
`id, restaurant_id, category_id, name, description, image_url, base_price, status, created_at, updated_at, deleted_at`

## ProductVariant
`id, product_id, name, price, status`

## Addon
`id, restaurant_id, name, price, status`

## ProductAddon
`product_id, addon_id`

## Customer
`id, restaurant_id, name, whatsapp_id, phone, created_at, updated_at`

## Conversation
`id, restaurant_id, customer_id, status, context, created_at, updated_at`

## Message
`id, conversation_id, external_message_id, direction, message_type, content, created_at`

## Cart
`id, restaurant_id, customer_id, status, created_at, updated_at`

## CartItem
`id, cart_id, product_id, variant_id, quantity, unit_price, notes`

## CartItemAddon
`id, cart_item_id, addon_id, quantity, unit_price`

## Order
`id, restaurant_id, customer_id, order_number, status, fulfillment_type, payment_method, subtotal, delivery_fee, total, address_snapshot, created_at, updated_at`

## OrderItem
`id, order_id, product_id, product_name, variant_name, quantity, unit_price, total, notes`

## OrderItemAddon
`id, order_item_id, addon_id, addon_name, quantity, unit_price, total`

# Tools da IA

- `get_restaurant_info`
- `search_products`
- `get_product`
- `get_cart`
- `add_to_cart`
- `update_cart_item`
- `remove_cart_item`
- `clear_cart`
- `calculate_order`
- `create_order`

Não criar tool genérica como `execute_sql`.

# Fluxo principal

```text
Cliente abre cardápio
  ↓
Seleciona produto
  ↓
Abre WhatsApp
  ↓
IA atende
  ↓
Consulta catálogo
  ↓
Adiciona itens
  ↓
Consulta/edita carrinho
  ↓
Escolhe entrega/retirada
  ↓
Informa endereço
  ↓
Escolhe pagamento
  ↓
Recebe resumo
  ↓
Confirma
  ↓
Pedido criado
  ↓
Restaurante acompanha
```

# Critério de sucesso

Um usuário que nunca viu o sistema deve conseguir realizar um pedido completo sem explicação humana.

O fluxo de ouro é:

**cardápio → WhatsApp → IA → carrinho → checkout → pedido no dashboard.**
