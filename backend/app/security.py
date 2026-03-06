from app.extensions import bcrypt, db
from app.models.user import User


def workspace_owner_user(user):
    if not user:
        return None
    owner_id = user.owner_id if user.owner_id else user.id
    return db.session.get(User, owner_id)


def verify_owner_password(user, plain_password):
    """Validate owner password against real account hash.

    Returns tuple: (ok, owner_user, error_message)
    """
    owner = workspace_owner_user(user)
    if not owner:
        return False, None, "Proprietário não encontrado."

    password = str(plain_password or "").strip()
    if not password:
        return False, owner, "Senha de proprietário é obrigatória."

    try:
        is_valid = bcrypt.check_password_hash(owner.password_hash, password.encode("utf-8"))
    except Exception:
        is_valid = False

    if is_valid:
        return True, owner, None

    return False, owner, "Senha de proprietário inválida."
