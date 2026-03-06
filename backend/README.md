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

## Direcionamento de mercado aplicado

O produto foi ajustado para os pontos mais exigidos hoje por pequenos negocios:

- simplicidade operacional (acoes rapidas em poucos cliques)
- visao de caixa e ticket medio em tempo real
- controle de estoque com alerta de nivel baixo
- fluxo integrado venda + baixa automatica de estoque
- exportacao de dados para tomada de decisao