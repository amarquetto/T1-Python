"""Ajustes incrementais de schema para bancos já existentes (ex.: antes de funcao_id)."""

from sqlalchemy import inspect, text


def run_schema_migrations(db) -> None:
    insp = inspect(db.engine)
    tables = insp.get_table_names()
    if "usuarios" not in tables:
        return
    cols = {c["name"] for c in insp.get_columns("usuarios")}
    if "funcao_id" in cols:
        return
    with db.engine.begin() as conn:
        conn.execute(text("ALTER TABLE usuarios ADD COLUMN funcao_id INT NULL"))
    if "funcoes" in tables:
        try:
            with db.engine.begin() as conn:
                conn.execute(
                    text(
                        "UPDATE usuarios SET funcao_id = "
                        "(SELECT id FROM funcoes WHERE nome = 'Administrador' LIMIT 1) "
                        "WHERE funcao_id IS NULL"
                    )
                )
        except Exception:
            pass
        try:
            with db.engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE usuarios ADD CONSTRAINT fk_usuarios_funcao "
                        "FOREIGN KEY (funcao_id) REFERENCES funcoes(id) "
                        "ON DELETE SET NULL ON UPDATE CASCADE"
                    )
                )
        except Exception:
            pass
