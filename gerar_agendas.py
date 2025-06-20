import sqlite3
from datetime import datetime, timedelta

# Conexão com o banco
conn = sqlite3.connect('clinica.db')
cursor = conn.cursor()

# Buscar todos os médicos
cursor.execute("SELECT id, nome FROM medico")
medicos = cursor.fetchall()

# Definir horários de atendimento
horarios = ['08:00', '09:00', '10:00', '11:00', '12:00']

# Gerar agendas para os próximos 5 dias úteis
hoje = datetime.now().date()
dias_criados = 0
dia = 0

while dias_criados < 5:
    data = hoje + timedelta(days=dia)
    if data.weekday() < 5:  # segunda a sexta
        for medico in medicos:
            for horario in horarios:
                cursor.execute("""
                    INSERT INTO agenda (medico_id, data, horario, vagas_totais, vagas_ocupadas)
                    VALUES (?, ?, ?, ?, ?)
                """, (medico[0], str(data), horario, 5, 0))
        dias_criados += 1
    dia += 1

conn.commit()
conn.close()
print("Agendas geradas com sucesso para os próximos 5 dias úteis.")
