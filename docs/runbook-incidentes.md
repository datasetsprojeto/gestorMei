# Runbook de Incidentes

## Escopo
Procedimentos para incidentes de disponibilidade, autenticação, banco e degradação de performance do GestorMEI.

## 1) Queda da API
- Verificar health: `GET /health`, `GET /health/live`, `GET /health/ready`.
- Revisar logs da aplicação com `X-Request-ID`.
- Confirmar variáveis críticas: `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`.
- Reiniciar serviço backend e validar readiness.

## 2) Erros de autenticação em massa
- Verificar taxa de `401` e `429` nos logs.
- Confirmar relógio do servidor (impacta JWT expiração).
- Revisar configuração de rate limit global e de login.
- Se necessário, reduzir janela de rate limit temporariamente.

## 3) Falha de banco de dados
- Validar conexão com Postgres e credenciais.
- Rodar restore do último backup válido:
  - `python backend/scripts/restore_postgres.py backups`
- Confirmar integridade básica com testes críticos.

## 4) Recuperação e comunicação
- Registrar causa raiz preliminar.
- Informar impacto para clientes e ETA de normalização.
- Abrir item no changelog com data, impacto e ação corretiva.

## 5) Pós-incidente
- Definir ação preventiva.
- Atualizar este runbook com o aprendizado.
