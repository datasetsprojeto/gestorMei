# GestorMEI API

Sistema de gestao de vendas e estoque para MEI com frontend web integrado.

## Tecnologias

- Backend: Flask
- Banco de dados: SQLite (padrao local) ou PostgreSQL (via `DATABASE_URL`)
- Autenticacao: JWT + Bcrypt
- ORM: SQLAlchemy

## Requisitos

- Python 3.10+
- pip

## Instalar dependencias

```bash
cd backend
python -m pip install -r requirements.txt -r requirements_test.txt
```

## Qualidade frontend (vite + lint + build)

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm run build
```

## Executar backend

```bash
cd backend
python run.py
```

A API sobe em `http://localhost:5000`.

## Start unificado (backend + frontend)

Na raiz do projeto (`gestorMei`), execute:

```bash
start.bat
```

Esse comando sobe:

- backend em `http://localhost:5000`
- frontend em `http://localhost:5501/index.html`

## Banco de dados

- Padrao: `backend/data/gestormei.db` (criado automaticamente no primeiro boot).
- Usuario admin inicial (seed automatica):
	- email: `admin@gestormei.com`
	- senha: `admin123`

Para usar PostgreSQL, defina no `.env`:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/gestormei
```

## Cadastro com senha por e-mail

O endpoint `POST /auth/register` agora recebe `name`, `email` e `phone`, gera uma senha temporaria automaticamente e envia essa senha por SMTP.

Configure no `.env`:

```env
JWT_SECRET_KEY=troque-por-um-segredo-forte
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu-email@provedor.com
SMTP_PASSWORD=sua-senha-ou-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_FROM_EMAIL=seu-email@provedor.com
SMTP_FROM_NAME=VendaMais
```

## Frontend

Abra `frontend/index.html` no navegador com a API rodando. O frontend consome a API real:

- login
- criacao de conta com envio de senha por e-mail
- cadastro/edicao/exclusao de produtos
- entrada de estoque
- registro de venda
- dashboard com metricas reais
- exportacoes de dados (JSON)

## Segurança e observabilidade (produção)

Variáveis relevantes em `backend/.env.example`:

- `CORS_ORIGINS` (restringir para domínio frontend real)
- `ENABLE_SECURITY_HEADERS=True`
- `LOG_JSON=True` (opcional para logs estruturados)
- `TRUST_PROXY_HEADERS=True` (apenas atrás de proxy confiável)

A API também retorna `X-Request-ID` em cada resposta para rastreamento.

## Endpoints principais

- `POST /auth/login`
- `POST /auth/register`
- `GET /products`
- `POST /products`
- `PUT /products/{id}`
- `DELETE /products/{id}`
- `GET /sales`
- `POST /sales`
- `GET /sales/{id}`
- `GET /sales/stats`
- `GET /sales/reports/monthly?year=YYYY&month=MM&format=json|csv|xlsx`
- `GET /sales/reports/monthly/compare?year=YYYY&month=MM`
- `GET /health`
- `GET /health/live`
- `GET /health/ready`

## Fase 2 (bootstrap de producao)

### 1) Subir PostgreSQL local para homologacao

Na raiz do projeto:

```bash
docker compose -f infra/docker-compose.postgres.yml up -d
```

Depois configure `backend/.env` com `DATABASE_URL` apontando para o Postgres.

### 2) CI de backend no GitHub Actions

Pipeline criada em `.github/workflows/backend-ci.yml`.
Ela instala dependencias e roda testes deterministicos:

- `test_auth_direct.py`
- `test_database.py`

### 3) Backup de banco PostgreSQL

Script utilitario criado em `backend/scripts/backup_postgres.py`.

Uso:

```bash
cd backend
python scripts/backup_postgres.py --output-dir backups
```

Requisitos:

- `DATABASE_URL` configurada para PostgreSQL
- `pg_dump` disponivel no PATH

### 4) Restore de backup PostgreSQL

Script utilitario criado em `backend/scripts/restore_postgres.py`.

Uso com arquivo especifico:

```bash
cd backend
python scripts/restore_postgres.py backups/gestormei_20260305_120000.dump
```

Uso com pasta (restaura o dump mais recente):

```bash
cd backend
python scripts/restore_postgres.py backups
```

Requisitos:

- `DATABASE_URL` configurada para PostgreSQL
- `pg_restore` disponivel no PATH

### 5) CI com PostgreSQL + teste de API

O workflow `.github/workflows/backend-ci.yml` agora possui:

- job de testes deterministicos
- job de integracao com service container PostgreSQL
- bootstrap da API Flask no CI e execucao de `test_api.py`

## OpenAPI

Especificação inicial disponível em `backend/openapi.yaml`.

## Compliance (modelos iniciais)

Na raiz do projeto:

- `docs/privacy-policy.md`
- `docs/terms-of-service.md`

## Direcionamento de mercado aplicado

O produto foi ajustado para os pontos mais exigidos hoje por pequenos negocios:

- simplicidade operacional (acoes rapidas em poucos cliques)
- visao de caixa e ticket medio em tempo real
- controle de estoque com alerta de nivel baixo
- fluxo integrado venda + baixa automatica de estoque
- exportacao de dados para tomada de decisao