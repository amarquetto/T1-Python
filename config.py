"""Configuração do app — lê variáveis de ambiente (.env) para MySQL e segredo."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "patafeliz_secret_2024")
    # XAMPP padrão: usuário root, senha vazia, porta 3306
    # Crie o banco `patafeliz` no MySQL Workbench antes de subir o Flask.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:@127.0.0.1:3306/patafeliz?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Pool pequeno para ambiente local / XAMPP
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
