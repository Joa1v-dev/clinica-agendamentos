from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'admin123'

@app.template_filter('strftime')
def format_datetime(value, format='%d/%m/%Y'):
    if isinstance(value, datetime):
        return value.strftime(format)
    return value  # Se não for datetime, retorna como está


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
            ''', (agenda_id,))

            conn.commit()
            conn.close()

            # Redireciona para página de comprovante
            return redirect(url_for('comprovante', consulta_id=consulta_id))
        else:
            flash('Horário indisponível. Por favor, escolha outro.')

    # Pegar usuários
    cursor.execute('SELECT id, nome FROM usuario')
    usuarios = cursor.fetchall()

    cursor.execute('SELECT id, nome FROM medico ORDER BY nome')
    medicos = cursor.fetchall()

    # Pegar agendas completas (id, data, horário e médico)
    cursor.execute('''
        SELECT a.id AS agenda_id, a.data, a.horario, m.nome AS medico
        FROM agenda a
        JOIN medico m ON a.medico_id = m.id
        WHERE a.vagas_ocupadas < a.vagas_totais
        ORDER BY a.data, a.horario
    ''')
    agendas_raw = cursor.fetchall()

    # Formatar datas para dd/mm/yyyy
    from datetime import datetime
    agendas = []
    for a in agendas_raw:
        data_formatada = datetime.strptime(a['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        agendas.append({
            'agenda_id': a['agenda_id'],
            'data': data_formatada,
            'horario': a['horario'],
            'medico': a['medico']
        })

    conn.close()

    return render_template('agendar.html', usuarios=usuarios, medicos=medicos)


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
        ORDER BY a.data, a.horario
    """, (medico_id,))
    agendas = cursor.fetchall()
    conn.close()

    horarios = []
    for a in agendas:
        vagas_disp = a['vagas_totais'] - a['vagas_ocupadas']
        data_br = datetime.strptime(a['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        horarios.append({
            'id': a['id'],
            'descricao': f"{a['data']} - {a['horario']}"
        })


    return horarios  # Flask 2.0+ retorna como JSON

from flask import request

@app.route('/consultas')
def listar_consultas():
    if 'atendente_id' not in session:
        return redirect(url_for('login'))

    data_filtro = request.args.get('data')  # data no formato YYYY-MM-DD ou None

    if not data_filtro:
        # Se não escolheu data, retorna lista vazia para não mostrar consultas
        consultas_formatadas = []
        return render_template('consultas.html', consultas=consultas_formatadas, data_filtro=data_filtro, mostrar_mensagem=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.id, u.nome AS paciente, m.nome AS medico, m.especialidade,
               a.data, a.horario, c.status
        FROM consulta c
        JOIN usuario u ON c.usuario_id = u.id
        JOIN agenda a ON c.agenda_id = a.id
        JOIN medico m ON a.medico_id = m.id
        WHERE a.data = ?
        ORDER BY a.horario ASC
    ''', (data_filtro,))

    consultas = cursor.fetchall()

    from datetime import datetime

    consultas_formatadas = []
    for c in consultas:
        c_dict = dict(c)
        c_dict['data'] = datetime.strptime(c_dict['data'], '%Y-%m-%d')
        consultas_formatadas.append(c_dict)

    conn.close()

    return render_template('consultas.html', consultas=consultas_formatadas, data_filtro=data_filtro, mostrar_mensagem=False)



@app.route('/consulta/<int:consulta_id>/cancelar', methods=['POST'])
def cancelar_consulta(consulta_id):
    if 'atendente_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Pegar agenda vinculada para liberar a vaga
    cursor.execute('SELECT agenda_id FROM consulta WHERE id = ?', (consulta_id,))
    agenda_id = cursor.fetchone()

    #cancelar consulta
    cursor.execute('UPDATE consulta SET status = "Cancelada" WHERE id = ?', (consulta_id,))

    #liberar vaga na agenda
    if agenda_id:
        cursor.execute('''
            UPDATE agenda SET vagas_ocupadas = vagas_ocupadas - 1 WHERE id = ?
        ''', (agenda_id['agenda_id'],))

    conn.commit()
    conn.close()
    flash('Consulta cancelada com sucesso!')
    return redirect(url_for('listar_consultas'))

@app.route('/reagendar/<int:consulta_id>', methods=['GET', 'POST'])
def reagendar_consulta(consulta_id):
    if 'atendente_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        novo_agenda_id = request.form['agenda']

        cursor.execute('SELECT agenda_id FROM consulta WHERE id = ?', (consulta_id,))
        agenda_atual = cursor.fetchone()

        if agenda_atual:
            cursor.execute('''
                UPDATE consulta SET agenda_id = ?, status = 'Reagendado' WHERE id = ?
            ''', (novo_agenda_id, consulta_id))

            cursor.execute('UPDATE agenda SET vagas_ocupadas = vagas_ocupadas - 1 WHERE id = ?', (agenda_atual['agenda_id'],))
            cursor.execute('UPDATE agenda SET vagas_ocupadas = vagas_ocupadas + 1 WHERE id = ?', (novo_agenda_id,))

            conn.commit()
            flash('Consulta reagendada com sucesso!')
        else:
            flash('Consulta não encontrada.')

        conn.close()
        return redirect(url_for('listar_consultas'))

    # GET: envia médicos para popular select
    cursor.execute('SELECT id, nome FROM medico ORDER BY nome')
    medicos = cursor.fetchall()

    conn.close()

    return render_template('reagendar.html', consulta_id=consulta_id, medicos=medicos)




#Caminho para fazer logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


#Ponto de partida para iniciar o servidor
if __name__ =='__main__':
    app.run(debug=True)

