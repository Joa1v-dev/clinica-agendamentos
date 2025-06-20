import sqlite3

#Criando a conexão com o banco de dados
conexao = sqlite3.connect('clinica.db')
cursor = conexao.cursor()

#Criando a tabela de usuários
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL
);
               
""")

#Criando a tabela de médicos
cursor.execute("""
CREATE TABLE IF NOT EXISTS medico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    especialidade TEXT NOT NULL
);
    
""")

#Criando a tabela de agendas
cursor.execute("""
CREATE TABLE IF NOT EXISTS agenda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medico_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    horario TEXT NOT NULL,
    vagas_totais INTEGER NOT NULL,
    vagas_ocupadas INTEGER DEFAULT 0,
    FOREIGN KEY (medico_id) REFERENCES medico(id)
);
""")

#Criando a tabela de consultas
cursor.execute("""
CREATE TABLE IF NOT EXISTS consulta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    agenda_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    FOREIGN KEY (agenda_id) REFERENCES agenda(id)
);
""")

#Salvando conexão e fechando
conexao.commit()
conexao.close()

print("Banco de Dados criado com sucesso!")