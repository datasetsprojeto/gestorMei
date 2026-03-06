# Changelog

## 2026-03-06
- Backend dependency hardening:
  - `Flask-Cors` atualizado para linha `6.x` para mitigar CVEs reportadas por `pip-audit`.
  - `requests` de testes atualizado para linha `2.32.x`.
- Frontend migrado para entrypoint ES Module com Vite build real.
- Code splitting e assets com hash ativados no build.
- Husky + lint-staged adicionados para pre-commit.
- Testes frontend com Vitest (unit) e Playwright (e2e) adicionados.
- Testes backend de fluxos críticos adicionados (`test_critical_flows.py`).
- Baseline de migration Alembic criado.
- Removidas alterações automáticas de schema em runtime.
- Hardening de segurança:
  - Rate limit global configurável.
  - Headers de segurança ampliados (HSTS).
  - Política de senha reforçada.
- CI ampliado para incluir testes frontend e auditoria de dependências.
