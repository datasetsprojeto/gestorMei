from app import create_app
import os

# Determinar ambiente - padrão para desenvolvimento
env = os.getenv("FLASK_ENV", "development")

print(f"🚀 Iniciando GestorMEI API no modo: {env}")
print(f"📁 Diretório: {os.getcwd()}")

app = create_app(config_name=env)

if __name__ == "__main__":
    if env == "development":
        print("🌐 Servidor rodando em: http://localhost:5000")
        print("🔧 Modo debug: ATIVADO")
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=True,
            use_reloader=True
        )
    else:
        print("⚡ Modo produção")
        app.run(
            host="0.0.0.0",
            port=int(os.getenv("PORT", 5000)),
            debug=False
        )