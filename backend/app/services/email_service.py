import smtplib
import ssl
from email.message import EmailMessage


class EmailServiceError(Exception):
    """Raised when email dispatch fails."""


def _required(value, field_name):
    if value:
        return value
    raise EmailServiceError(f"Configuracao SMTP ausente: {field_name}")


def send_password_email(config, to_email, user_name, generated_password):
    """Send onboarding email containing the generated temporary password."""
    smtp_host = _required(config.get("SMTP_HOST"), "SMTP_HOST")
    smtp_port = int(config.get("SMTP_PORT", 587))
    smtp_username = _required(config.get("SMTP_USERNAME"), "SMTP_USERNAME")
    smtp_password = _required(config.get("SMTP_PASSWORD"), "SMTP_PASSWORD")
    from_email = config.get("SMTP_FROM_EMAIL") or smtp_username
    from_name = config.get("SMTP_FROM_NAME") or "VendaMais"
    use_tls = bool(config.get("SMTP_USE_TLS", True))
    use_ssl = bool(config.get("SMTP_USE_SSL", False))

    message = EmailMessage()
    message["Subject"] = "Sua conta no VendaMais foi criada"
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email
    message.set_content(
        (
            f"Ola, {user_name}.\n\n"
            "Sua conta no VendaMais foi criada com sucesso.\n"
            f"E-mail: {to_email}\n"
            f"Senha temporaria: {generated_password}\n\n"
            "Por seguranca, faca login e altere sua senha o quanto antes.\n"
            "Se voce nao solicitou esse cadastro, ignore esta mensagem.\n"
        )
    )

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=20) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                server.login(smtp_username, smtp_password)
                server.send_message(message)
    except Exception as exc:
        raise EmailServiceError(f"Falha ao enviar e-mail: {exc}") from exc
