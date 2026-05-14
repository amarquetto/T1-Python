"""Permissões de sessão e decorador por chave de permissão (função cadastrada)."""

from functools import wraps

from flask import flash, redirect, session, url_for


def permissoes_sessao():
    return list(session.get("permissoes") or [])


def pode(chave: str) -> bool:
    return chave in set(permissoes_sessao())


def permission_required(*chaves: str):
    """Exige login (usar abaixo de @login_required) e pelo menos uma das permissões listadas."""

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            perms = set(permissoes_sessao())
            if not chaves or not any(c in perms for c in chaves):
                flash("Você não tem permissão para acessar esta área.", "danger")
                return redirect(url_for("painel"))
            return f(*args, **kwargs)

        return wrapped

    return decorator
