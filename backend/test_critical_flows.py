from app import create_app
from app.extensions import db
from app.models.product import Product
from app.models.sale import Sale
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _login(client, email: str = "admin@gestormei.com", password: str = "admin123") -> str:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.get_json()["access_token"]


def test_auth_rate_limit_invalid_credentials():
    app = create_app("testing")
    client = app.test_client()

    for _ in range(5):
        response = client.post(
            "/auth/login",
            json={"email": "rate.limit@example.com", "password": "invalid123"},
        )
        assert response.status_code == 401

    blocked = client.post(
        "/auth/login",
        json={"email": "rate.limit@example.com", "password": "invalid123"},
    )
    assert blocked.status_code == 429


def test_owner_can_clear_operational_data_only_with_password():
    app = create_app("testing")
    client = app.test_client()

    with app.app_context():
        db.session.add(Product(name="P1", price=10, stock=5, user_id=1, cost=4))
        db.session.commit()

    token = _login(client)
    headers = _auth_headers(token)

    denied = client.post("/products/cache/clear-data", headers=headers, json={"owner_password": "wrong"})
    assert denied.status_code == 403

    allowed = client.post("/products/cache/clear-data", headers=headers, json={"owner_password": "admin123"})
    assert allowed.status_code == 200

    with app.app_context():
        assert Product.query.count() == 0
        assert Sale.query.count() == 0
        assert User.query.count() >= 1


def test_employee_link_and_unlink_flow():
    app = create_app("testing")
    client = app.test_client()

    token = _login(client)
    headers = _auth_headers(token)

    linked = client.post(
        "/employees/link",
        headers=headers,
        json={"email": "funcionario@example.com", "name": "Funcionario Teste", "phone": "11999999999"},
    )
    assert linked.status_code == 200
    employee_id = linked.get_json()["employee"]["id"]

    unlinked = client.post(f"/employees/unlink/{employee_id}", headers=headers)
    assert unlinked.status_code == 200


def test_sales_flow_rejects_insufficient_stock_and_updates_stock_on_success():
    app = create_app("testing")
    client = app.test_client()

    token = _login(client)
    headers = _auth_headers(token)

    created_product = client.post(
        "/products/",
        headers=headers,
        json={"name": "Produto Venda", "price": 20, "stock": 1, "cost": 5},
    )
    assert created_product.status_code == 201
    product_id = created_product.get_json()["product"]["id"]

    insufficient = client.post(
        "/sales/",
        headers=headers,
        json={"items": [{"product_id": product_id, "quantity": 2}]},
    )
    assert insufficient.status_code == 400

    successful = client.post(
        "/sales/",
        headers=headers,
        json={"items": [{"product_id": product_id, "quantity": 1}]},
    )
    assert successful.status_code == 201

    with app.app_context():
        product = Product.query.get(product_id)
        assert product is not None
        assert int(product.stock) == 0
