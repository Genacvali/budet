import os
from dotenv import load_dotenv

def main():
    import uvicorn  # импорт внутри функции, чтобы ре-лоадер не споткнулся
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "1") not in ("0", "false", "False")

    print(f"🚀 Starting Budget PWA Backend on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/api/health")
    print("🛑 Press Ctrl+C to stop")

    uvicorn.run("app.main:app", host=host, port=port, reload=reload, workers=1)

if __name__ == "__main__":
    main()