# Checkout — Status do desenvolvimento

Resumo do que já foi desenvolvido, sprint por sprint.

## Sprint 0 — Fundação ✅

**Status: desenvolvida e validada (DoD cumprido).**

### Backend (`backend/`)
- FastAPI + Uvicorn, Python 3.12
- Config por environment via `pydantic-settings` (`src/config/__init__.py`, `.env.example`)
- Logging básico estruturado no `src/main.py`
- SQLAlchemy 2 (async + asyncpg), engine/session em `src/infra/database/__init__.py`
- Alembic configurado com env async (`alembic/env.py`), migration inicial `0001_initial_base` executa com sucesso
- Health check `GET /health` valida conexão com o banco (retorna `status` e `database`)
- Handler global de exceções (500 estruturado, `Exception` logada)
- Lint: ruff (E, F, I, UP, B) — passando
- Testes: pytest + TestClient (`tests/test_health.py`) — passando

### Frontend (`frontend/`)
- Vite 8 + React 19 + TypeScript, gerado com template oficial
- Routing: react-router-dom (`src/app/App.tsx`, `Layout.tsx` com header/footer)
- React Query instalado e provisionado em `src/main.tsx`
- Design system mínimo em `src/shared/styles/global.css` (CSS variables: cores, espaçamento, componentes base `.btn`, `.card`)
- Estrutura modular conforme plano: `src/modules/` + `src/shared/`
- Home placeholder em `src/modules/dashboard/DashboardPage.tsx`
- Proxy `/api` → backend no dev (`vite.config.ts`)
- Lint: oxlint — passando. Build — passando

### Infra
- `docker-compose.yml`: Postgres 16, Redis 7, backend, frontend (nginx)
- Portas expostas: backend `8000`, frontend `8080` (db/redis acessam só via rede interna)
- Backend roda `alembic upgrade head` antes de subir
- Dockerfiles multi-stage: backend python-slim, frontend node build → nginx (SPA fallback + proxy `/api`)
- CI: `.github/workflows/ci.yml` (jobs backend: lint+test, frontend: lint+build)

### Como rodar
```sh
docker compose up -d --build
# frontend: http://localhost:8080 | health: http://localhost:8000/health
```

## Sprint 1 — Restaurante + catálogo ⏳
Próxima sprint. Restaurante, Categoria, Produto, Variações, Adicionais (CRUDs + frontend admin).