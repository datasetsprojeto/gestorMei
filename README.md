# GestorMEI

Aplicação de gestão para pequenos negócios com backend Flask e frontend web modular.

## Acesso online
- Executar no navegador via GitHub Codespaces: `https://codespaces.new/datasetsprojeto/gestorMei`

Observação:
- O projeto depende de frontend + backend para funcionar completo.
- Em Codespaces, inicie os dois serviços e use as portas expostas para acessar a aplicação.

## Fluxos principais (atualizado)
- Dashboard com métricas de bruto/liquido e comparação Entradas x Vendas.
- Vendas com filtros por periodo e relatório mensal.
- Produtos focado em edicao (cadastro centralizado no fluxo de entradas).
- Entradas com duas formas:
	- `+ Nova Entrada`: registra entrada para produto existente.
	- `Cadastrar Novo Produto`: cadastra produto + registra entrada inicial no mesmo fluxo.
- Regra de custo unitario divergente:
	- ao registrar entrada com custo diferente do produto base, o sistema cria variante automaticamente.
	- essa regra agora está no backend (`POST /products/entries`), garantindo consistência também em chamadas diretas de API.

## Estrutura
- `backend/`: API Flask, autenticação, regras de negócio, auditoria.
- `frontend/`: aplicação web com CSS e JS modulares.
- `infra/`: docker compose para PostgreSQL local.
- `docs/`: documentos de política, termos e operação.

## Execução rápida
- Windows: `start.bat`
- Linux/macOS: `start.sh`

## Comandos úteis

### Frontend
```bash
cd frontend
npm install
npm run lint
npm run build
```

### Backend
```bash
cd backend
python run.py
```

## Qualidade de código
- Frontend com `vite`, `eslint` e `prettier`.
- Testes frontend com `vitest` (unit) e `playwright` (e2e).
- Backend com testes automatizados e CI no GitHub Actions.
- Hooks de commit com `husky` + `lint-staged`.

## API e banco
- OpenAPI: `backend/openapi.yaml`
- Migrações Alembic em `backend/migrations/`
- Baseline atual: `backend/migrations/versions/20260306_000001_baseline_schema.py`

## Produção (recomendado)
- PostgreSQL em `DATABASE_URL`.
- `SECRET_KEY` e `JWT_SECRET_KEY` fortes.
- `CORS_ORIGINS` restrito ao dominio do frontend.
- `ENABLE_SECURITY_HEADERS=True`.

## Documentação adicional
- Política de privacidade: `docs/privacy-policy.md`
- Termos de uso: `docs/terms-of-service.md`
- Runbook de incidentes: `docs/runbook-incidentes.md`
- Histórico de mudanças: `CHANGELOG.md`
