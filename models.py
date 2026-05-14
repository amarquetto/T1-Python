"""Modelos ORM — tabelas MySQL usadas pelo PataFeliz."""

from extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    perfil = db.Column(db.String(80), nullable=False)
    ativo = db.Column(db.String(3), nullable=False, default="Sim")  # Sim / Não
    senha_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Usuario {self.email}>"


class Funcao(db.Model):
    __tablename__ = "funcoes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # ativo / inativo
    descricao = db.Column(db.Text, nullable=False)
    # Lista de chaves de permissão, ex.: ["dashboard", "gerenciar_pets"]
    permissoes = db.Column(db.JSON, nullable=False, default=list)

    def __repr__(self):
        return f"<Funcao {self.nome}>"


class Pet(db.Model):
    __tablename__ = "pets"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    especie = db.Column(db.String(40), nullable=False)
    raca = db.Column(db.String(80), nullable=False, default="SRD")
    idade = db.Column(db.Integer, nullable=False)
    tutor = db.Column(db.String(120), nullable=False)
    peso = db.Column(db.String(40), nullable=False, default="—")

    def __repr__(self):
        return f"<Pet {self.nome}>"


class Servico(db.Model):
    __tablename__ = "servicos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(80), nullable=False)
    preco = db.Column(db.String(40), nullable=False)
    duracao = db.Column(db.String(40), nullable=False)
    disponivel = db.Column(db.String(3), nullable=False, default="Sim")

    def __repr__(self):
        return f"<Servico {self.nome}>"
