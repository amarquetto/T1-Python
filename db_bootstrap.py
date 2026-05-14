"""Garante que o schema MySQL exista antes do db.create_all (útil com XAMPP)."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL, make_url


def ensure_mysql_database(database_uri: str) -> None:
    if not database_uri.startswith("mysql"):
        return
    url = make_url(database_uri)
    dbname = url.database
    if not dbname:
        return
    # Conexão ao servidor sem schema selecionado (evita erro 1049 antes do CREATE DATABASE)
    admin = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        query=url.query,
    )
    engine = create_engine(admin, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{dbname}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
    finally:
        engine.dispose()
