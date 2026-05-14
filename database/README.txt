MySQL (XAMPP) — PataFeliz
=========================

1) MySQL ligado no XAMPP.
2) Copie .env.example para .env e ajuste DATABASE_URL se necessário.
3) pip install -r requirements.txt
4) python app.py — cria o banco, tabelas, migrações simples (coluna funcao_id) e seed.

Login seed (usuários iniciais): senha 123456. Perfis vêm das funções
"Administrador" (acesso total) e "Atendente" (dashboard + pets).

Se o schema antigo der conflito, apague o banco patafeliz no Workbench e suba o app de novo.

Permissões de menu: dashboard, gerenciar_usuarios, gerenciar_funcoes,
gerenciar_pets, gerenciar_servicos, emitir_relatorios — marque no cadastro de funções.
