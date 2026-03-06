# GestorMEI

Aplicação de gestão para pequenos negócios com backend Flask e frontend web.

## Estrutura
- `backend/`: API Flask, autenticação, regras de negócio, auditoria.
- `frontend/`: aplicação web com CSS e JS modulares.
- `infra/`: docker compose para PostgreSQL local.
- `docs/`: documentos de política e termos (modelos iniciais).

## Qualidade de Código
- Frontend com `vite`, `eslint` e `prettier`.
- Backend com testes automatizados e CI no GitHub Actions.
- Hooks de commit com `husky` + `lint-staged`.
- Testes frontend com `vitest` (unit) e `playwright` (e2e).

## Frontend moderno (ES Modules)
- Entry único em `frontend/js/main.js` com módulos ES reais.
- Build de produção via Vite com minificação, sourcemap e assets versionados por hash.

Comandos:

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm run test:unit
npm run build
npm run test:e2e
```

## Migrations
- Baseline Alembic criado em `backend/migrations/versions/20260306_000001_baseline_schema.py`.
- Evolução de schema deve ser feita via migrações, evitando `ALTER TABLE` automático em runtime.

## Execução Rápida
- Windows: `start.bat`
- Linux/macOS: `start.sh`

## Documentação de API
- Especificação OpenAPI: `backend/openapi.yaml`

## Produção (Recomendado)
- PostgreSQL configurado em `DATABASE_URL`.
- `SECRET_KEY` e `JWT_SECRET_KEY` fortes.
- `CORS_ORIGINS` restrito ao domínio frontend.
- `ENABLE_SECURITY_HEADERS=True`.

## Compliance Inicial
- Política de privacidade: `docs/privacy-policy.md`
- Termos de uso: `docs/terms-of-service.md`

## Operação e governança
- Runbook de incidentes: `docs/runbook-incidentes.md`
- Histórico de mudanças: `CHANGELOG.md`
