"""
app.py — Arquivo principal do sistema PataFeliz PetShop
Rotas públicas e protegidas; dados persistidos em MySQL (Flask-SQLAlchemy).
"""

from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from db_bootstrap import ensure_mysql_database
from extensions import db
from models import Funcao, Pet, Servico, Usuario
from seed import seed_if_empty

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Catálogo fixo de permissões (UI do cadastro de funções)
PERMISSOES_CATALOGO = [
    {"key": "dashboard", "label": "Dashboard", "icone": "bi-speedometer2"},
    {"key": "gerenciar_usuarios", "label": "Gerenciar usuários", "icone": "bi-people"},
    {"key": "gerenciar_funcoes", "label": "Gerenciar funções", "icone": "bi-shield-check"},
    {"key": "gerenciar_pets", "label": "Gerenciar pets", "icone": "bi-heart"},
    {"key": "emitir_relatorios", "label": "Emitir relatórios", "icone": "bi-file-earmark-bar-graph"},
]

with app.app_context():
    ensure_mysql_database(app.config["SQLALCHEMY_DATABASE_URI"])
    db.create_all()
    seed_if_empty()


# ─────────────────────────────────────────────
# ROTAS PÚBLICAS
# ─────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "").strip()
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha_hash, senha):
            session["usuario"] = email
            session["nome"] = usuario.nome or email.split("@")[0].capitalize()
            flash("Login realizado com sucesso! Bem-vindo(a) 🐾", "success")
            return redirect(url_for("listar_usuarios"))
        flash("E-mail ou senha incorretos. Tente novamente.", "danger")

    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "").strip()
        conf = request.form.get("confirmar_senha", "").strip()

        if not nome or not email or not senha or not conf:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("cadastro.html")

        if senha != conf:
            flash("As senhas não coincidem. Tente novamente.", "danger")
            return render_template("cadastro.html")

        if len(senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template("cadastro.html")

        if Usuario.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado. Faça login ou use outro e-mail.", "danger")
            return render_template("cadastro.html")

        try:
            db.session.add(
                Usuario(
                    nome=nome,
                    email=email,
                    perfil="Atendente",
                    ativo="Sim",
                    senha_hash=generate_password_hash(senha),
                )
            )
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Este e-mail já está cadastrado.", "danger")
            return render_template("cadastro.html")

        flash("Cadastro realizado com sucesso! Faça login para entrar.", "success")
        return redirect(url_for("login"))

    return render_template("cadastro.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema. Até logo! 🐾", "info")
    return redirect(url_for("login"))


# ─────────────────────────────────────────────
# DECORATOR
# ─────────────────────────────────────────────


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario" not in session:
            flash("Você precisa estar logado para acessar esta página.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


# ─────────────────────────────────────────────
# USUÁRIOS E FUNÇÕES
# ─────────────────────────────────────────────


@app.route("/usuarios/listar")
@login_required
def listar_usuarios():
    usuarios = Usuario.query.order_by(Usuario.id).all()
    return render_template("usuarios/listar_usuarios.html", usuarios=usuarios)


@app.route("/usuarios/listar-funcoes")
@login_required
def listar_funcoes():
    funcoes = Funcao.query.order_by(Funcao.id).all()
    return render_template(
        "usuarios/listar_funcoes.html",
        funcoes=funcoes,
        permissoes_catalogo=PERMISSOES_CATALOGO,
    )


@app.route("/usuarios/cadastrar-funcoes", methods=["GET", "POST"])
@login_required
def cadastrar_funcoes():
    if request.method == "POST":
        nome_funcao = request.form.get("nome_funcao", "").strip()
        status = request.form.get("status_funcao", "").strip()
        descricao = request.form.get("descricao_funcao", "").strip()
        permissoes = request.form.getlist("permissoes")

        if not nome_funcao:
            flash("Informe o nome da função.", "danger")
        elif len(nome_funcao) > 120:
            flash("O nome da função pode ter no máximo 120 caracteres.", "danger")
        elif status not in ("ativo", "inativo"):
            flash("Selecione se a função ficará ativa ou inativa.", "danger")
        elif not descricao:
            flash("Informe a descrição com as responsabilidades da função.", "danger")
        else:
            chaves_validas = {p["key"] for p in PERMISSOES_CATALOGO}
            permissoes_limpas = [k for k in permissoes if k in chaves_validas]
            db.session.add(
                Funcao(
                    nome=nome_funcao,
                    status=status,
                    descricao=descricao,
                    permissoes=permissoes_limpas,
                )
            )
            db.session.commit()
            flash("Função cadastrada com sucesso!", "success")
            return redirect(url_for("listar_funcoes"))

    return render_template(
        "usuarios/cadastrar_funcoes.html",
        permissoes_catalogo=PERMISSOES_CATALOGO,
    )


@app.route("/usuarios/inserir", methods=["GET", "POST"])
@login_required
def inserir_usuario():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        perfil = request.form.get("perfil", "").strip()
        senha = request.form.get("senha", "").strip()

        if not nome or not email or not perfil or not senha:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("usuarios/inserir_usuario.html")

        if Usuario.query.filter_by(email=email).first():
            flash("Já existe um usuário com este e-mail.", "danger")
            return render_template("usuarios/inserir_usuario.html")

        try:
            db.session.add(
                Usuario(
                    nome=nome,
                    email=email,
                    perfil=perfil,
                    ativo="Sim",
                    senha_hash=generate_password_hash(senha),
                )
            )
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um usuário com este e-mail.", "danger")
            return render_template("usuarios/inserir_usuario.html")

        flash(f'Usuário "{nome}" cadastrado com sucesso!', "success")
        return redirect(url_for("listar_usuarios"))

    return render_template("usuarios/inserir_usuario.html")


# ─────────────────────────────────────────────
# PETS
# ─────────────────────────────────────────────


@app.route("/pets/listar")
@login_required
def listar_pets():
    pets = Pet.query.order_by(Pet.id).all()
    return render_template("pets/listar_pets.html", pets=pets)


@app.route("/pets/inserir", methods=["GET", "POST"])
@login_required
def inserir_pet():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        especie = request.form.get("especie", "").strip()
        raca = request.form.get("raca", "").strip()
        tutor = request.form.get("tutor", "").strip()
        idade_raw = request.form.get("idade", "").strip()
        peso = request.form.get("peso", "").strip()

        if not nome or not especie or not tutor or not idade_raw:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("pets/inserir_pet.html")

        try:
            idade = int(idade_raw)
        except ValueError:
            flash("A idade deve ser um número inteiro.", "danger")
            return render_template("pets/inserir_pet.html")

        db.session.add(
            Pet(
                nome=nome,
                especie=especie,
                raca=raca if raca else "SRD",
                idade=idade,
                tutor=tutor,
                peso=f"{peso} kg" if peso else "—",
            )
        )
        db.session.commit()

        flash(f'Pet "{nome}" cadastrado com sucesso! 🐾', "success")
        return redirect(url_for("listar_pets"))

    return render_template("pets/inserir_pet.html")


# ─────────────────────────────────────────────
# SERVIÇOS
# ─────────────────────────────────────────────


@app.route("/servicos/listar")
@login_required
def listar_servicos():
    servicos = Servico.query.order_by(Servico.id).all()
    return render_template("servicos/listar_servicos.html", servicos=servicos)


@app.route("/servicos/inserir", methods=["GET", "POST"])
@login_required
def inserir_servico():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        categoria = request.form.get("categoria", "").strip()
        preco = request.form.get("preco", "").strip()
        duracao = request.form.get("duracao", "").strip()
        disponivel = request.form.get("disponivel", "Sim").strip()

        if not nome or not categoria or not preco or not duracao:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("servicos/inserir_servico.html")

        try:
            preco_fmt = f"R$ {float(preco):.2f}".replace(".", ",")
        except ValueError:
            flash("Informe um preço numérico válido.", "danger")
            return render_template("servicos/inserir_servico.html")

        db.session.add(
            Servico(
                nome=nome,
                categoria=categoria,
                preco=preco_fmt,
                duracao=duracao,
                disponivel=disponivel,
            )
        )
        db.session.commit()

        flash(f'Serviço "{nome}" cadastrado com sucesso!', "success")
        return redirect(url_for("listar_servicos"))

    return render_template("servicos/inserir_servico.html")


# ─────────────────────────────────────────────
# EQUIPE
# ─────────────────────────────────────────────


@app.route("/equipe")
def equipe():
    return render_template("sobre_equipe.html")


# ─────────────────────────────────────────────
# INICIALIZAÇÃO
# ─────────────────────────────────────────────


if __name__ == "__main__":
    app.run(debug=True)
