-- Execute no MySQL Workbench (como root ou usuário com permissão CREATE).
-- Depois suba o Flask: as tabelas são criadas automaticamente (db.create_all).

CREATE DATABASE IF NOT EXISTS patafeliz
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE patafeliz;
