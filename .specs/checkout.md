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

## Sprint 2 — Cardápio público ⏳
Próxima sprint. `GET /public/restaurants/:slug/menu` + página pública visual e responsiva.