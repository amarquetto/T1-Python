"""
Popula o banco na primeira execução (tabelas vazias).
Senha dos usuários seed: 123456
"""

from werkzeug.security import generate_password_hash

from extensions import db
from models import Funcao, Pet, Servico, Usuario


def seed_if_empty() -> None:
    if Usuario.query.count() > 0:
        return

    todas = [
        "dashboard",
        "gerenciar_usuarios",
        "gerenciar_funcoes",
        "gerenciar_pets",
        "gerenciar_servicos",
        "emitir_relatorios",
    ]
    admin = Funcao(
        nome="Administrador",
        status="ativo",
        descricao="Acesso total ao sistema.",
        permissoes=todas,
    )
    atendente = Funcao(
        nome="Atendente",
        status="ativo",
        descricao="Operações básicas: painel e pets.",
        permissoes=["dashboard", "gerenciar_pets"],
    )
    db.session.add_all([admin, atendente])
    db.session.commit()

    admin_id = Funcao.query.filter_by(nome="Administrador").first().id
    atend_id = Funcao.query.filter_by(nome="Atendente").first().id

    senha = generate_password_hash("123456")
    usuarios_seed = [
        ("Ingrid Venancio", "ingrid.venancio@patafeliz.com", admin_id, "Sim"),
        ("Andre Marquetto", "andre@patafeliz.com", admin_id, "Sim"),
        ("Carla Mendes", "carla@patafeliz.com", atend_id, "Sim"),
        ("Diego Rocha", "diego@patafeliz.com", atend_id, "Não"),
        ("Eduarda Farias", "edu@patafeliz.com", atend_id, "Sim"),
    ]
    for nome, email, fid, ativo in usuarios_seed:
        fn = db.session.get(Funcao, fid)
        db.session.add(
            Usuario(
                nome=nome,
                email=email,
                perfil=fn.nome if fn else "Atendente",
                ativo=ativo,
                senha_hash=senha,
                funcao_id=fid,
            )
        )

    pets_seed = [
        ("Thor", "Cão", "Golden Retriever", 3, "João Alves", "32 kg"),
        ("Mel", "Gato", "Persa", 5, "Maria Costa", "4 kg"),
        ("Bob", "Cão", "Bulldog Francês", 2, "Pedro Santos", "12 kg"),
        ("Luna", "Gato", "Siamês", 1, "Clara Nunes", "3,5 kg"),
        ("Bolinha", "Cão", "Poodle", 7, "Rafa Moura", "8 kg"),
        ("Pipoca", "Coelho", "Angorá", 2, "Luana Barros", "2 kg"),
    ]
    for nome, especie, raca, idade, tutor, peso in pets_seed:
        db.session.add(
            Pet(nome=nome, especie=especie, raca=raca, idade=idade, tutor=tutor, peso=peso)
        )

    servicos_seed = [
        ("Banho e Tosa Completa", "Estética", "R$ 80,00", "2h", "Sim"),
        ("Consulta Veterinária", "Saúde", "R$ 150,00", "45min", "Sim"),
        ("Vacinação Antirrábica", "Saúde", "R$ 60,00", "15min", "Sim"),
        ("Hotel para Pets", "Hospedagem", "R$ 120,00", "diária", "Sim"),
        ("Adestramento Básico", "Treinamento", "R$ 200,00", "1h", "Sim"),
        ("Hidratação de Pelagem", "Estética", "R$ 45,00", "1h", "Não"),
    ]
    for nome, cat, preco, dur, disp in servicos_seed:
        db.session.add(
            Servico(
                nome=nome,
                categoria=cat,
                preco=preco,
                duracao=dur,
                disponivel=disp,
            )
        )

    db.session.commit()
