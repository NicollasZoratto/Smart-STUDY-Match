-- StudyMatch: modelagem do domínio (grupos de estudo).
-- Idempotente: pode rodar quantas vezes quiser (CREATE IF NOT EXISTS / INSERT IGNORE).
-- O app_principal executa todos os db/*.sql em ordem ao iniciar. Também dá para rodar à mão:
--   mysql -h HOST -u USER -p NOME_DO_BANCO < db/001_dominio.sql

CREATE TABLE IF NOT EXISTS disciplinas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nome VARCHAR(120) NOT NULL
);

-- lider_id aponta para usuarios.id, que pertence ao auth_service (outro serviço),
-- por isso é uma referência lógica e não uma FOREIGN KEY.
CREATE TABLE IF NOT EXISTS grupos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lider_id INT NOT NULL,
    disciplina_id INT NOT NULL,
    titulo VARCHAR(120) NOT NULL,
    descricao VARCHAR(500) NOT NULL DEFAULT '',
    dia_semana TINYINT NOT NULL,
    horario_inicio TIME NOT NULL,
    horario_fim TIME NOT NULL,
    vagas INT NOT NULL DEFAULT 5,
    modalidade VARCHAR(12) NOT NULL DEFAULT 'online',
    foto_key VARCHAR(255),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_grupos_lider (lider_id),
    CONSTRAINT fk_grupos_disciplina FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id)
);

CREATE TABLE IF NOT EXISTS grupo_membros (
    grupo_id INT NOT NULL,
    user_id INT NOT NULL,
    entrou_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (grupo_id, user_id),
    INDEX idx_membros_user (user_id),
    CONSTRAINT fk_membros_grupo FOREIGN KEY (grupo_id) REFERENCES grupos(id) ON DELETE CASCADE
);

-- Seed: disciplinas do curso
INSERT IGNORE INTO disciplinas (codigo, nome) VALUES
    ('ISW055', 'Introdução à Computação em Nuvem'),
    ('BDD001', 'Banco de Dados'),
    ('ESW001', 'Engenharia de Software'),
    ('ALG001', 'Algoritmos e Lógica de Programação'),
    ('EDD001', 'Estrutura de Dados'),
    ('RED001', 'Redes de Computadores'),
    ('MAT001', 'Matemática Discreta'),
    ('ING001', 'Inglês Técnico');
