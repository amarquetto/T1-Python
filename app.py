"""
app.py — Arquivo principal do sistema PataFeliz PetShop
Contém todas as rotas públicas e protegidas do sistema.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
# Chave secreta usada para assinar os cookies de sessão
app.secret_key = 'patafeliz_secret_2024'

# ─────────────────────────────────────────────
# DADOS SIMULADOS (hardcoded para esta entrega)
# ─────────────────────────────────────────────

# Lista de usuários cadastrados no sistema
usuarios = [
    {'id': 1, 'nome': 'Ingrid Venancio', 'email': 'ingrid.venancio@patafeliz.com',    'perfil': 'Administrador', 'ativo': 'Sim'},
    {'id': 2, 'nome': 'Andre Marquetto',     'email': 'andre@patafeliz.com',  'perfil': 'Administrador',   'ativo': 'Sim'},
    {'id': 3, 'nome': 'Carla Mendes',   'email': 'carla@patafeliz.com',  'perfil': 'Atendente',     'ativo': 'Sim'},
    {'id': 4, 'nome': 'Diego Rocha',    'email': 'diego@patafeliz.com',  'perfil': 'Atendente',     'ativo': 'Não'},
    {'id': 5, 'nome': 'Eduarda Farias', 'email': 'edu@patafeliz.com',    'perfil': 'Veterinário',   'ativo': 'Sim'},
]

# Catálogo de permissões no cadastro de funções (ordem alinhada ao menu do sistema)
PERMISSOES_CATALOGO = [
    {'key': 'dashboard', 'label': 'Dashboard', 'icone': 'bi-speedometer2'},
    {'key': 'gerenciar_usuarios', 'label': 'Gerenciar usuários', 'icone': 'bi-people'},
    {'key': 'gerenciar_funcoes', 'label': 'Gerenciar funções', 'icone': 'bi-shield-check'},
    {'key': 'gerenciar_pets', 'label': 'Gerenciar pets', 'icone': 'bi-heart'},
    {'key': 'emitir_relatorios', 'label': 'Emitir relatórios', 'icone': 'bi-file-earmark-bar-graph'},
]

# Funções cadastradas pelo usuário (nome livre + status + permissões)
funcoes = []

# Lista de pets cadastrados no sistema
pets = [
    {'id': 1, 'nome': 'Thor',    'especie': 'Cão',   'raca': 'Golden Retriever', 'idade': 3, 'tutor': 'João Alves',    'peso': '32 kg'},
    {'id': 2, 'nome': 'Mel',     'especie': 'Gato',  'raca': 'Persa',            'idade': 5, 'tutor': 'Maria Costa',   'peso': '4 kg'},
    {'id': 3, 'nome': 'Bob',     'especie': 'Cão',   'raca': 'Bulldog Francês',  'idade': 2, 'tutor': 'Pedro Santos',  'peso': '12 kg'},
    {'id': 4, 'nome': 'Luna',    'especie': 'Gato',  'raca': 'Siamês',           'idade': 1, 'tutor': 'Clara Nunes',   'peso': '3,5 kg'},
    {'id': 5, 'nome': 'Bolinha', 'especie': 'Cão',   'raca': 'Poodle',           'idade': 7, 'tutor': 'Rafa Moura',    'peso': '8 kg'},
    {'id': 6, 'nome': 'Pipoca',  'especie': 'Coelho','raca': 'Angorá',           'idade': 2, 'tutor': 'Luana Barros',  'peso': '2 kg'},
]

# Lista de serviços oferecidos pelo petshop
servicos = [
    {'id': 1, 'nome': 'Banho e Tosa Completa',  'categoria': 'Estética',    'preco': 'R$ 80,00',  'duracao': '2h',    'disponivel': 'Sim'},
    {'id': 2, 'nome': 'Consulta Veterinária',   'categoria': 'Saúde',       'preco': 'R$ 150,00', 'duracao': '45min', 'disponivel': 'Sim'},
    {'id': 3, 'nome': 'Vacinação Antirrábica',  'categoria': 'Saúde',       'preco': 'R$ 60,00',  'duracao': '15min', 'disponivel': 'Sim'},
    {'id': 4, 'nome': 'Hotel para Pets',        'categoria': 'Hospedagem',  'preco': 'R$ 120,00', 'duracao': 'diária','disponivel': 'Sim'},
    {'id': 5, 'nome': 'Adestramento Básico',    'categoria': 'Treinamento', 'preco': 'R$ 200,00', 'duracao': '1h',    'disponivel': 'Sim'},
    {'id': 6, 'nome': 'Hidratação de Pelagem',  'categoria': 'Estética',    'preco': 'R$ 45,00',  'duracao': '1h',    'disponivel': 'Não'},
]


# ─────────────────────────────────────────────
# ROTAS PÚBLICAS (sem necessidade de login)
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Página inicial — apresenta o negócio para visitantes não logados."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → exibe o formulário de login.
    POST → valida credenciais e inicia a sessão do usuário.
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()

        # Verificação simples: qualquer e-mail + senha '123456' loga no sistema
        if email and senha == '123456':
            session['usuario'] = email
            session['nome'] = email.split('@')[0].capitalize()
            flash('Login realizado com sucesso! Bem-vindo(a) 🐾', 'success')
            return redirect(url_for('listar_usuarios'))

        flash('E-mail ou senha incorretos. Tente novamente.', 'danger')

    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """
    GET  → exibe o formulário de cadastro de novo usuário.
    POST → valida os campos e redireciona para o login.
    """
    if request.method == 'POST':
        nome  = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '').strip()
        conf  = request.form.get('confirmar_senha', '').strip()

        # Validações de campos obrigatórios
        if not nome or not email or not senha or not conf:
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return render_template('cadastro.html')

        if senha != conf:
            flash('As senhas não coincidem. Tente novamente.', 'danger')
            return render_template('cadastro.html')

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('cadastro.html')

        flash('Cadastro realizado com sucesso! Faça login para entrar.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html')


@app.route('/logout')
def logout():
    """Encerra a sessão do usuário e redireciona para o login."""
    session.clear()
    flash('Você saiu do sistema. Até logo! 🐾', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# DECORATOR de proteção de rotas
# ─────────────────────────────────────────────

def login_required(f):
    """Decorador que bloqueia acesso a rotas protegidas sem sessão ativa."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# ROTAS DE USUÁRIOS
# ─────────────────────────────────────────────

@app.route('/usuarios/listar')
@login_required
def listar_usuarios():
    """Exibe a tabela com todos os usuários cadastrados no sistema."""
    return render_template('usuarios/listar_usuarios.html', usuarios=usuarios)


@app.route('/usuarios/listar-funcoes')
@login_required
def listar_funcoes():
    """Listagem das funções cadastradas (permissões e status)."""
    return render_template(
        'usuarios/listar_funcoes.html',
        funcoes=funcoes,
        permissoes_catalogo=PERMISSOES_CATALOGO,
    )


@app.route('/usuarios/cadastrar-funcoes', methods=['GET', 'POST'])
@login_required
def cadastrar_funcoes():
    """
    GET  → formulário para cadastrar uma nova função com nome livre, status e permissões.
    POST → valida, grava em memória e redireciona para a listagem de funções.
    """
    if request.method == 'POST':
        nome_funcao = request.form.get('nome_funcao', '').strip()
        status = request.form.get('status_funcao', '').strip()
        descricao = request.form.get('descricao_funcao', '').strip()
        permissoes = request.form.getlist('permissoes')

        if not nome_funcao:
            flash('Informe o nome da função.', 'danger')
        elif len(nome_funcao) > 120:
            flash('O nome da função pode ter no máximo 120 caracteres.', 'danger')
        elif status not in ('ativo', 'inativo'):
            flash('Selecione se a função ficará ativa ou inativa.', 'danger')
        elif not descricao:
            flash('Informe a descrição com as responsabilidades da função.', 'danger')
        else:
            novo_id = max((item['id'] for item in funcoes), default=0) + 1
            chaves_validas = {p['key'] for p in PERMISSOES_CATALOGO}
            permissoes_limpas = [k for k in permissoes if k in chaves_validas]
            funcoes.append({
                'id': novo_id,
                'nome': nome_funcao,
                'status': status,
                'descricao': descricao,
                'permissoes': permissoes_limpas,
            })
            flash('Função cadastrada com sucesso!', 'success')
            return redirect(url_for('listar_funcoes'))

    return render_template(
        'usuarios/cadastrar_funcoes.html',
        permissoes_catalogo=PERMISSOES_CATALOGO,
    )


@app.route('/usuarios/inserir', methods=['GET', 'POST'])
@login_required
def inserir_usuario():
    """
    GET  → exibe o formulário para cadastrar um novo usuário.
    POST → valida os dados e redireciona para a listagem.
    """
    if request.method == 'POST':
        nome   = request.form.get('nome', '').strip()
        email  = request.form.get('email', '').strip()
        perfil = request.form.get('perfil', '').strip()
        senha  = request.form.get('senha', '').strip()

        if not nome or not email or not perfil or not senha:
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return render_template('usuarios/inserir_usuario.html')

        # Gera um novo ID único e adiciona o usuário na lista global
        novo_id = max((u['id'] for u in usuarios), default=0) + 1
        usuarios.append({
            'id':     novo_id,
            'nome':   nome,
            'email':  email,
            'perfil': perfil,
            'ativo':  'Sim',  # todo novo usuário começa ativo
        })  # ✅ Adiciona de verdade na lista em memória

        flash(f'Usuário "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_usuarios'))

    return render_template('usuarios/inserir_usuario.html')


# ─────────────────────────────────────────────
# ROTAS DE PETS
# ─────────────────────────────────────────────

@app.route('/pets/listar')
@login_required
def listar_pets():
    """Exibe a tabela com todos os pets cadastrados no sistema."""
    return render_template('pets/listar_pets.html', pets=pets)


@app.route('/pets/inserir', methods=['GET', 'POST'])
@login_required
def inserir_pet():
    """
    GET  → exibe o formulário para cadastrar um novo pet.
    POST → valida os dados, adiciona na lista e redireciona para a listagem.
    """
    if request.method == 'POST':
        nome    = request.form.get('nome', '').strip()
        especie = request.form.get('especie', '').strip()
        raca    = request.form.get('raca', '').strip()
        tutor   = request.form.get('tutor', '').strip()
        idade   = request.form.get('idade', '').strip()
        peso    = request.form.get('peso', '').strip()

        # Validação dos campos obrigatórios
        if not nome or not especie or not tutor or not idade:
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return render_template('pets/inserir_pet.html')

        # Garante que a idade é um número válido
        try:
            idade = int(idade)
        except ValueError:
            flash('A idade deve ser um número inteiro.', 'danger')
            return render_template('pets/inserir_pet.html')

        # Gera um novo ID único baseado no maior ID existente na lista
        novo_id = max((p['id'] for p in pets), default=0) + 1

        # Monta o dicionário do novo pet e adiciona na lista global
        novo_pet = {
            'id':      novo_id,
            'nome':    nome,
            'especie': especie,
            'raca':    raca if raca else 'SRD',  # SRD = Sem Raça Definida
            'idade':   idade,
            'tutor':   tutor,
            'peso':    f"{peso} kg" if peso else '—',
        }
        pets.append(novo_pet)  # ✅ Adiciona de verdade na lista em memória

        flash(f'Pet "{nome}" cadastrado com sucesso! 🐾', 'success')
        return redirect(url_for('listar_pets'))

    return render_template('pets/inserir_pet.html')


# ─────────────────────────────────────────────
# ROTAS DE SERVIÇOS
# ─────────────────────────────────────────────

@app.route('/servicos/listar')
@login_required
def listar_servicos():
    """Exibe a tabela com todos os serviços oferecidos pelo petshop."""
    return render_template('servicos/listar_servicos.html', servicos=servicos)


@app.route('/servicos/inserir', methods=['GET', 'POST'])
@login_required
def inserir_servico():
    """
    GET  → exibe o formulário para cadastrar um novo serviço.
    POST → valida os dados e redireciona para a listagem de serviços.
    """
    if request.method == 'POST':
        nome       = request.form.get('nome', '').strip()
        categoria  = request.form.get('categoria', '').strip()
        preco      = request.form.get('preco', '').strip()
        duracao    = request.form.get('duracao', '').strip()
        disponivel = request.form.get('disponivel', 'Sim').strip()

        if not nome or not categoria or not preco or not duracao:
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return render_template('servicos/inserir_servico.html')

        # Formata o preço com prefixo R$ e adiciona na lista global
        novo_id = max((s['id'] for s in servicos), default=0) + 1
        servicos.append({
            'id':         novo_id,
            'nome':       nome,
            'categoria':  categoria,
            'preco':      f"R$ {float(preco):.2f}".replace('.', ','),
            'duracao':    duracao,
            'disponivel': disponivel,
        })  # ✅ Adiciona de verdade na lista em memória

        flash(f'Serviço "{nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_servicos'))

    return render_template('servicos/inserir_servico.html')


# ─────────────────────────────────────────────
# ROTA DA EQUIPE
# ─────────────────────────────────────────────

@app.route('/equipe')
def equipe():
    """Página da equipe de desenvolvimento — layout próprio, sem herança de base.html."""
    return render_template('sobre_equipe.html')


# ─────────────────────────────────────────────
# INICIALIZAÇÃO
# ─────────────────────────────────────────────

if __name__ == '__main__':
    # debug=True recarrega o servidor automaticamente a cada alteração no código
    app.run(debug=True)
