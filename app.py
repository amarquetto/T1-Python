"""
app.py — PataFeliz PetShop: rotas e regras de negócio (MySQL + permissões por função).
"""

from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from db_bootstrap import ensure_mysql_database
from extensions import db
from models import Funcao, Pet, Servico, Usuario
from permissions import permission_required, pode
from schema_migrate import run_schema_migrations
from seed import seed_if_empty

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

PERMISSOES_CATALOGO = [
    {"key": "dashboard", "label": "Dashboard", "icone": "bi-speedometer2"},
    {"key": "gerenciar_usuarios", "label": "Gerenciar usuários", "icone": "bi-people"},
    {"key": "gerenciar_funcoes", "label": "Gerenciar funções", "icone": "bi-shield-check"},
    {"key": "gerenciar_pets", "label": "Gerenciar pets", "icone": "bi-heart"},
    {"key": "gerenciar_servicos", "label": "Gerenciar serviços", "icone": "bi-scissors"},
    {"key": "emitir_relatorios", "label": "Emitir relatórios", "icone": "bi-file-earmark-bar-graph"},
]

with app.app_context():
    ensure_mysql_database(app.config["SQLALCHEMY_DATABASE_URI"])
    db.create_all()
    run_schema_migrations(db)
    seed_if_empty()


@app.context_processor
def inject_permissoes():
    return {"pode": pode, "PERMISSOES_CATALOGO": PERMISSOES_CATALOGO}


def _permissoes_para_sessao(usuario: Usuario) -> list:
    if usuario.funcao and usuario.funcao.status == "ativo":
        return list(usuario.funcao.permissoes or [])
    if usuario.funcao_id is None and usuario.perfil == "Administrador":
        return [p["key"] for p in PERMISSOES_CATALOGO]
    return []


def _atualizar_sessao(usuario: Usuario) -> None:
    session["usuario"] = usuario.email
    session["nome"] = usuario.nome or usuario.email.split("@")[0].capitalize()
    session["permissoes"] = _permissoes_para_sessao(usuario)


def _redirect_pos_login():
    ordem = [
        ("dashboard", "painel"),
        ("gerenciar_usuarios", "listar_usuarios"),
        ("gerenciar_funcoes", "listar_funcoes"),
        ("gerenciar_pets", "listar_pets"),
        ("gerenciar_servicos", "listar_servicos"),
        ("emitir_relatorios", "relatorios"),
    ]
    for chave, endpoint in ordem:
        if pode(chave):
            return redirect(url_for(endpoint))
    flash("Sua função não possui permissões de menu. Contate o administrador.", "warning")
    return redirect(url_for("logout"))


def _funcoes_para_formulario():
    return (
        Funcao.query.filter_by(status="ativo")
        .order_by(Funcao.nome)
        .all()
    )


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
        usuario = (
            Usuario.query.options(joinedload(Usuario.funcao))
            .filter_by(email=email)
            .first()
        )
        if usuario and check_password_hash(usuario.senha_hash, senha):
            if usuario.ativo != "Sim":
                flash("Usuário inativo. Procure o administrador.", "danger")
                return render_template("login.html")
            _atualizar_sessao(usuario)
            flash("Login realizado com sucesso! Bem-vindo(a) 🐾", "success")
            return _redirect_pos_login()
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

        fn_padrao = Funcao.query.filter_by(nome="Atendente", status="ativo").first()
        if not fn_padrao:
            fn_padrao = Funcao.query.filter_by(status="ativo").first()
        perfil_txt = fn_padrao.nome if fn_padrao else "Atendente"
        fid = fn_padrao.id if fn_padrao else None

        try:
            db.session.add(
                Usuario(
                    nome=nome,
                    email=email,
                    perfil=perfil_txt,
                    ativo="Sim",
                    senha_hash=generate_password_hash(senha),
                    funcao_id=fid,
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
# DECORADORES
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
# PAINEL E RELATÓRIOS
# ─────────────────────────────────────────────


@app.route("/painel")
@login_required
def painel():
    return render_template("painel.html")


@app.route("/relatorios")
@login_required
@permission_required("emitir_relatorios")
def relatorios():
    return render_template("relatorios.html")


# ─────────────────────────────────────────────
# USUÁRIOS
# ─────────────────────────────────────────────


@app.route("/usuarios/listar")
@login_required
@permission_required("gerenciar_usuarios")
def listar_usuarios():
    usuarios = Usuario.query.options(joinedload(Usuario.funcao)).order_by(Usuario.id).all()
    return render_template("usuarios/listar_usuarios.html", usuarios=usuarios)


@app.route("/usuarios/inserir", methods=["GET", "POST"])
@login_required
@permission_required("gerenciar_usuarios")
def inserir_usuario():
    funcoes = _funcoes_para_formulario()
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "").strip()
        try:
            funcao_id = int(request.form.get("funcao_id", "0"))
        except ValueError:
            funcao_id = 0

        if not nome or not email or not senha or not funcao_id:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template(
                "usuarios/inserir_usuario.html", funcoes=funcoes
            )

        fn = db.session.get(Funcao, funcao_id)
        if not fn or fn.status != "ativo":
            flash("Selecione uma função ativa válida.", "danger")
            return render_template("usuarios/inserir_usuario.html", funcoes=funcoes)

        if Usuario.query.filter_by(email=email).first():
            flash("Já existe um usuário com este e-mail.", "danger")
            return render_template("usuarios/inserir_usuario.html", funcoes=funcoes)

        try:
            db.session.add(
                Usuario(
                    nome=nome,
                    email=email,
                    perfil=fn.nome,
                    ativo="Sim",
                    senha_hash=generate_password_hash(senha),
                    funcao_id=fn.id,
                )
            )
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um usuário com este e-mail.", "danger")
            return render_template("usuarios/inserir_usuario.html", funcoes=funcoes)

        flash(f'Usuário "{nome}" cadastrado com sucesso!', "success")
        return redirect(url_for("listar_usuarios"))

    return render_template("usuarios/inserir_usuario.html", funcoes=funcoes)


@app.route("/usuarios/editar/<int:id>", methods=["GET", "POST"])
@login_required
@permission_required("gerenciar_usuarios")
def editar_usuario(id):
    usuario = Usuario.query.options(joinedload(Usuario.funcao)).get_or_404(id)
    funcoes = _funcoes_para_formulario()
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "").strip()
        ativo = request.form.get("ativo", "Sim").strip()
        try:
            funcao_id = int(request.form.get("funcao_id", "0"))
        except ValueError:
            funcao_id = 0

        if not nome or not email or not funcao_id:
            flash("Preencha nome, e-mail e função.", "danger")
            return render_template(
                "usuarios/editar_usuario.html",
                usuario_edit=usuario,
                funcoes=funcoes,
            )

        fn = db.session.get(Funcao, funcao_id)
        if not fn or fn.status != "ativo":
            flash("Selecione uma função ativa válida.", "danger")
            return render_template(
                "usuarios/editar_usuario.html",
                usuario_edit=usuario,
                funcoes=funcoes,
            )

        outro = Usuario.query.filter(Usuario.email == email, Usuario.id != id).first()
        if outro:
            flash("Já existe outro usuário com este e-mail.", "danger")
            return render_template(
                "usuarios/editar_usuario.html",
                usuario_edit=usuario,
                funcoes=funcoes,
            )

        usuario.nome = nome
        usuario.email = email
        usuario.funcao_id = fn.id
        usuario.perfil = fn.nome
        usuario.ativo = ativo if ativo in ("Sim", "Não") else "Sim"
        if senha:
            if len(senha) < 6:
                flash("A nova senha deve ter pelo menos 6 caracteres.", "danger")
                return render_template(
                    "usuarios/editar_usuario.html",
                    usuario_edit=usuario,
                    funcoes=funcoes,
                )
            usuario.senha_hash = generate_password_hash(senha)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Não foi possível salvar (e-mail duplicado?).", "danger")
            return render_template(
                "usuarios/editar_usuario.html",
                usuario_edit=usuario,
                funcoes=funcoes,
            )

        if session.get("usuario") == usuario.email:
            _atualizar_sessao(usuario)

        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("listar_usuarios"))

    return render_template(
        "usuarios/editar_usuario.html",
        usuario_edit=usuario,
        funcoes=funcoes,
    )


@app.post("/usuarios/excluir/<int:id>")
@login_required
@permission_required("gerenciar_usuarios")
def excluir_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.email == session.get("usuario"):
        flash("Você não pode excluir a si mesmo enquanto estiver logado.", "danger")
        return redirect(url_for("listar_usuarios"))
    nome = usuario.nome
    db.session.delete(usuario)
    db.session.commit()
    flash(f'Usuário "{nome}" removido do sistema.', "success")
    return redirect(url_for("listar_usuarios"))


# ─────────────────────────────────────────────
# FUNÇÕES (PERFIS / PERMISSÕES)
# ─────────────────────────────────────────────


@app.route("/usuarios/listar-funcoes")
@login_required
@permission_required("gerenciar_funcoes")
def listar_funcoes():
    funcoes = Funcao.query.order_by(Funcao.id).all()
    return render_template(
        "usuarios/listar_funcoes.html",
        funcoes=funcoes,
        permissoes_catalogo=PERMISSOES_CATALOGO,
    )


@app.route("/usuarios/cadastrar-funcoes", methods=["GET", "POST"])
@login_required
@permission_required("gerenciar_funcoes")
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


@app.route("/usuarios/editar-funcao/<int:id>", methods=["GET", "POST"])
@login_required
@permission_required("gerenciar_funcoes")
def editar_funcao(id):
    funcao = Funcao.query.get_or_404(id)
    if request.method == "POST":
        nome_funcao = request.form.get("nome_funcao", "").strip()
        status = request.form.get("status_funcao", "").strip()
        descricao = request.form.get("descricao_funcao", "").strip()
        permissoes = request.form.getlist("permissoes")

        if not nome_funcao or len(nome_funcao) > 120:
            flash("Nome da função inválido.", "danger")
        elif status not in ("ativo", "inativo"):
            flash("Status inválido.", "danger")
        elif not descricao:
            flash("Informe a descrição.", "danger")
        else:
            chaves_validas = {p["key"] for p in PERMISSOES_CATALOGO}
            funcao.nome = nome_funcao
            funcao.status = status
            funcao.descricao = descricao
            funcao.permissoes = [k for k in permissoes if k in chaves_validas]
            for u in funcao.usuarios:
                u.perfil = nome_funcao
            db.session.commit()
            flash("Função atualizada com sucesso!", "success")
            return redirect(url_for("listar_funcoes"))

    return render_template(
        "usuarios/editar_funcao.html",
        funcao_edit=funcao,
        permissoes_catalogo=PERMISSOES_CATALOGO,
    )


@app.post("/usuarios/excluir-funcao/<int:id>")
@login_required
@permission_required("gerenciar_funcoes")
def excluir_funcao(id):
    funcao = Funcao.query.get_or_404(id)
    if Usuario.query.filter_by(funcao_id=funcao.id).count() > 0:
        flash("Não é possível excluir: existem usuários vinculados a esta função.", "danger")
        return redirect(url_for("listar_funcoes"))
    nome = funcao.nome
    db.session.delete(funcao)
    db.session.commit()
    flash(f'Função "{nome}" removida.', "success")
    return redirect(url_for("listar_funcoes"))


# ─────────────────────────────────────────────
# PETS
# ─────────────────────────────────────────────


@app.route("/pets/listar")
@login_required
@permission_required("gerenciar_pets")
def listar_pets():
    pets = Pet.query.order_by(Pet.id).all()
    return render_template("pets/listar_pets.html", pets=pets)


@app.route("/pets/inserir", methods=["GET", "POST"])
@login_required
@permission_required("gerenciar_pets")
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


@app.route("/pets/editar/<int:id>", methods=["GET", "POST"])
@login_required
@permission_required("gerenciar_pets")
def editar_pet(id):
    pet = Pet.query.get_or_404(id)
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        especie = request.form.get("especie", "").strip()
        raca = request.form.get("raca", "").strip()
        tutor = request.form.get("tutor", "").strip()
        idade_raw = request.form.get("idade", "").strip()
        peso = request.form.get("peso", "").strip()

        if not nome or not especie or not tutor or not idade_raw:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("pets/editar_pet.html", pet=pet)

        try:
            idade = int(idade_raw)
        except ValueError:
            flash("A idade deve ser um número inteiro.", "danger")
            return render_template("pets/editar_pet.html", pet=pet)

        pet.nome = nome
        pet.especie = especie
        pet.raca = raca if raca else "SRD"
        pet.idade = idade
        pet.tutor = tutor
        pet.peso = f"{peso} kg" if peso else "—"
        db.session.commit()
        flash("Pet atualizado com sucesso!", "success")
        return redirect(url_for("listar_pets"))

    return render_template("pets/editar_pet.html", pet=pet)


@app.post("/pets/excluir/<int:id>")
@login_required
@permission_required("gerenciar_pets")
def excluir_pet(id):
    pet = Pet.query.get_or_404(id)
    nome = pet.nome
    db.session.delete(pet)
    db.session.commit()
    flash(f'Pet "{nome}" removido.', "success")
    return redirect(url_for("listar_pets"))


# ─────────────────────────────────────────────
# SERVIÇOS
# ─────────────────────────────────────────────


@app.route("/servicos/listar")
@login_required
@permission_required("gerenciar_servicos")
def listar_servicos():
    servicos = Servico.query.order_by(Servico.id).all()
    return render_template("servicos/listar_servicos.html", servicos=servicos)


@app.route("/servicos/inserir", methods=["GET", "POST"])
@login_required
@permission_required("gerenciar_servicos")
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


@app.route("/servicos/editar/<int:id>", methods=["GET", "POST"])
@login_required
@permission_required("gerenciar_servicos")
def editar_servico(id):
    serv = Servico.query.get_or_404(id)
    preco_editavel = ""
    try:
        raw = (
            serv.preco.replace("R$", "")
            .replace(" ", "")
            .replace(".", "")
            .replace(",", ".")
        )
        preco_editavel = str(float(raw))
    except ValueError:
        preco_editavel = ""

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        categoria = request.form.get("categoria", "").strip()
        preco = request.form.get("preco", "").strip()
        duracao = request.form.get("duracao", "").strip()
        disponivel = request.form.get("disponivel", "Sim").strip()

        if not nome or not categoria or not preco or not duracao:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template(
                "servicos/editar_servico.html",
                serv=serv,
                preco_editavel=preco_editavel,
            )

        try:
            preco_fmt = f"R$ {float(preco):.2f}".replace(".", ",")
        except ValueError:
            flash("Informe um preço numérico válido.", "danger")
            return render_template(
                "servicos/editar_servico.html",
                serv=serv,
                preco_editavel=preco_editavel,
            )

        serv.nome = nome
        serv.categoria = categoria
        serv.preco = preco_fmt
        serv.duracao = duracao
        serv.disponivel = disponivel
        db.session.commit()
        flash("Serviço atualizado com sucesso!", "success")
        return redirect(url_for("listar_servicos"))

    return render_template(
        "servicos/editar_servico.html",
        serv=serv,
        preco_editavel=preco_editavel,
    )


@app.post("/servicos/excluir/<int:id>")
@login_required
@permission_required("gerenciar_servicos")
def excluir_servico(id):
    serv = Servico.query.get_or_404(id)
    nome = serv.nome
    db.session.delete(serv)
    db.session.commit()
    flash(f'Serviço "{nome}" removido.', "success")
    return redirect(url_for("listar_servicos"))


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
