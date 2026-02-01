"""Per-request database connection config (multi-user / production)."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import Any
from config import get_settings


@dataclass
class ConnectionConfig:
    """Database connection parameters. When None, use env/default."""
    host: str
    port: int
    user: str
    password: str
    database: str
    database_type: str = "mysql"  # mysql | postgres

    def connection_key(self) -> str:
        """Stable key for this connection (e.g. for FAISS store path)."""
        raw = f"{self.host}:{self.port}:{self.user}:{self.database}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def mysql_url(self) -> str:
        return (
            f"mysql+pymysql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

    def postgres_url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

    def sqlalchemy_url(self) -> str:
        if self.database_type == "postgres":
            return self.postgres_url()
        return self.mysql_url()


def connection_from_request(body: dict[str, Any] | None) -> ConnectionConfig | None:
    """Build ConnectionConfig from request body (connection key). None = use env."""
    if not body or not body.get("database"):
        return None
    host = body.get("host") or "localhost"
    port = int(body.get("port") or 3306)
    user = body.get("user") or "root"
    password = body.get("password") or ""
    database = body.get("database")
    db_type = (body.get("database_type") or "mysql").lower()
    return ConnectionConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        database_type=db_type,
    )


def connection_from_settings() -> ConnectionConfig:
    """Build ConnectionConfig from app settings (default)."""
    s = get_settings()
    return ConnectionConfig(
        host=s.mysql_host,
        port=s.mysql_port,
        user=s.mysql_user,
        password=s.mysql_password,
        database=s.mysql_database,
        database_type=s.database_type,
    )


def get_connection(connection_config: ConnectionConfig | None) -> ConnectionConfig:
    """Return connection_config if provided, else from settings."""
    if connection_config is not None:
        return connection_config
    return connection_from_settings()
