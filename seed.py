"""
Popula o banco na primeira execução (tabelas vazias).
Senha de todos os usuários seed: 123456
"""

from werkzeug.security import generate_password_hash

from extensions import db
from models import Pet, Servico, Usuario


def seed_if_empty() -> None:
    if Usuario.query.count() > 0:
        return

    senha = generate_password_hash("123456")
    usuarios_seed = [
        ("Ingrid Venancio", "ingrid.venancio@patafeliz.com", "Administrador", "Sim"),
        ("Andre Marquetto", "andre@patafeliz.com", "Administrador", "Sim"),
    ]

    for nome, email, perfil, ativo in usuarios_seed:
        db.session.add(
            Usuario(
                nome=nome,
                email=email,
                perfil=perfil,
                ativo=ativo,
                senha_hash=senha,
            )
        )

    pets_seed = [
        ("Thor", "Cão", "Golden Retriever", 3, "João Alves", "32 kg"),
        ("Mel", "Gato", "Persa", 5, "Maria Costa", "4 kg"),
        ("Bob", "Cão", "Bulldog Francês", 2, "Pedro Santos", "12 kg"),
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

    # Funções: começar vazio (cadastro pela tela), ou exemplo opcional — deixamos vazio

    db.session.commit()
