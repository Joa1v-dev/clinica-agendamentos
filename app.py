from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'admin123'

#Criando função para conectar o banco
def get_db_connection():
    conn = sqlite3.connect('clinica.db')
    conn.row_factory = sqlite3.Row
    return conn

#Métodos Get e Post para login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn= get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM atendente WHERE email = ? AND senha_hash = ?', (email, senha))
        atendente = cursor.fetchone()
        conn.close()

        if atendente:
            session['atendente_id'] = atendente['id']
            session['atendente_nome'] = atendente['nome']
            return redirect(url_for('home'))
        else:
            flash('Email ou senha inválidos')

    return render_template('login.html')

#Caminho para a página home após validar o login
@app.route('/home')
def home():
    if 'atendente_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', nome=session['atendente_nome'])

#Criando a página para agendamento
@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if 'atendente_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        usuario_id = request.form['usuario']
        agenda_id = request.form['agenda']

        # Verificar se ainda há vaga
        cursor.execute('SELECT vagas_totais, vagas_ocupadas FROM agenda WHERE id = ?', (agenda_id,))
        agenda = cursor.fetchone()
        if agenda and agenda['vagas_ocupadas'] < agenda['vagas_totais']:
            # Inserir consulta
         cursor.execute('''
            INSERT INTO consulta (usuario_id, agenda_id, status)
            VALUES (?, ?, 'Agendado')
        ''', (usuario_id, agenda_id))
        consulta_id = cursor.lastrowid  # Captura o ID da nova consulta

# Atualizar vagas ocupadas
        cursor.execute('''
            UPDATE agenda SET vagas_ocupadas = vagas_ocupadas + 1 WHERE id = ?
        ''',  (agenda_id,))

        conn.commit()
        conn.close()

# Redireciona para página de comprovante
        return redirect(url_for('comprovante', consulta_id=consulta_id))

    # Pegar usuários
    cursor.execute('SELECT id, nome FROM usuario')
    usuarios = cursor.fetchall()

# Pegar médicos distintos das agendas
    cursor.execute('''
    SELECT DISTINCT m.id as medico_id, m.nome as medico
    FROM agenda a
    JOIN medico m ON a.medico_id = m.id
''')
    agendas = cursor.fetchall()

    conn.close()

    return render_template('agendar.html', usuarios=usuarios, agendas=agendas)

@app.route('/comprovante/<int:consulta_id>')
def comprovante(consulta_id):
    if 'atendente_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.id, u.nome AS paciente, m.nome AS medico, m.especialidade,
               a.data, a.horario
        FROM consulta c
        JOIN usuario u ON c.usuario_id = u.id
        JOIN agenda a ON c.agenda_id = a.id
        JOIN medico m ON a.medico_id = m.id
        WHERE c.id = ?
    ''', (consulta_id,))
    consulta = cursor.fetchone()
    conn.close()

    return render_template('comprovante.html', consulta=consulta)


@app.route('/horarios/<int:medico_id>')
def horarios_por_medico(medico_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.data, a.horario, a.vagas_totais, a.vagas_ocupadas
        FROM agenda a
        WHERE a.medico_id = ?
    """, (medico_id,))
    agendas = cursor.fetchall()
    conn.close()

    horarios = []
    for a in agendas:
        vagas_disp = a['vagas_totais'] - a['vagas_ocupadas']
        horarios.append({
            'id': a['id'],
            'descricao': f"{a['data']} - {a['horario']} ({vagas_disp} vagas)"
        })

    return horarios  # Flask 2.0+ retorna JSON automaticamente

#Caminho para fazer logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


#Ponto de partida para iniciar o servidor
if __name__ =='__main__':
    app.run(debug=True)

