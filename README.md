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
