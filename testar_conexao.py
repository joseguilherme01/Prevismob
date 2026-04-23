import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

host = os.getenv("DB_HOST", "127.0.0.1").strip()
port = int(os.getenv("DB_PORT", "3306").strip())
user = os.getenv("DB_USER", "root").strip()
password = os.getenv("DB_PASSWORD", "")  # pode estar vazio
db = os.getenv("DB_NAME", "prevismob").strip()

url = URL.create(
    drivername="mysql+pymysql",
    username=user,
    password=password if password != "" else None,
    host=host,
    port=port,
    database=db,
    query={"charset": "utf8mb4"},
)

print(f"Testando conexão em {host}:{port}, banco={db}, usuário={user}")

try:
    engine = create_engine(url, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Conexão com banco OK.")
except Exception as e:
    print("❌ Falha na conexão.")
    print(type(e).__name__, "-", e)
    raise SystemExit(1)