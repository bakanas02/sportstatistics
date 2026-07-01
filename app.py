import os
import pyodbc
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime

# Загружаем переменные из файла .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key') # Лучше хранить и секретный ключ в .env

# Получаем настройки базы данных из переменных окружения
db_server = os.getenv('DB_SERVER')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

def get_db_connection():
    """Функция для создания подключения к базе данных"""
    conn_str = (
        f'DRIVER={{SQL Server}};'
        f'SERVER={db_server};'
        f'DATABASE={db_name};'
        f'UID={db_user};'
        f'PWD={db_password}'
    )
    return pyodbc.connect(conn_str)

# Инициализируем соединение
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    print("Успешное подключение к базе данных!")
except Exception as e:
    print(f"Ошибка подключения к базе данных: {e}")

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Очищаем данные сеанса
    session.clear()
    # Перенаправляем пользователя на страницу входа
    return redirect(url_for('login'))

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    cursor.execute("SELECT * FROM Users WHERE Username = ? AND Password = ?", (username, password))
    user = cursor.fetchone()

    if user:
        session['username'] = username
        flash('You are logged into the application web', 'success')  # Добавьте эту строку
        return redirect(url_for('homepage'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

def is_admin(username):
    cursor.execute("SELECT Role FROM Users WHERE Username = ?", (username,))
    role = cursor.fetchone()
    return role and role[0] == 'admin'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or not is_admin(session['username']):
            flash('You do not have permission to perform this operation.', 'error')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function

# Other routes and functions...

@app.route('/homepage')
def homepage():
    # Check if there are flash messages indicating permission errors
    permission_error = session.pop('no_permission', None)
    return render_template('homepage.html', permission_error=permission_error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username.strip() or not password.strip():
            return "Please fill in all fields.", 400

        # Check if the username already exists
        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return "This username is already taken. Please choose a different one."
        else:
            cursor.execute("INSERT INTO Users (Username, Password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/fighters')
def fighters():
    cursor.execute('SELECT * FROM Fighters')
    fighters = cursor.fetchall()
    return render_template('fighters.html', fighters=fighters)

@app.route('/events')
def events():
    cursor.execute('SELECT * FROM Events')
    events = cursor.fetchall()
    return render_template('events.html', events=events)

@app.route('/fights')
def fights():
    cursor.execute('SELECT * FROM Fights')
    fights = cursor.fetchall()
    return render_template('fights.html', fights=fights)

@app.route('/add_fighter', methods=['POST'])
@admin_required
def add_fighter():
    if request.method == 'POST':
        name = request.form['name']
        nickname = request.form['nickname']
        country = request.form['country']
        age = request.form['age']
        weight_class = request.form['weight_class']

        cursor.execute("INSERT INTO Fighters (Name, Nickname, Country, Age, WeightClass) VALUES (?, ?, ?, ?, ?)",
                       (name, nickname, country, age, weight_class))
        conn.commit()
        return jsonify(message='Fighter added successfully')

    return jsonify(error='Method not allowed')

@app.route('/delete_fighter/<int:fighter_id>', methods=['POST'])
@admin_required

def delete_fighter(fighter_id):
    if request.method == 'POST':
        cursor.execute("DELETE FROM Fighters WHERE FighterID = ?", (fighter_id,))
        conn.commit()
        return jsonify(message='Fighter deleted successfully')
    return jsonify(error='Method not allowed')

@app.route('/update_fighter/<int:fighter_id>', methods=['POST'])
@admin_required
def update_fighter(fighter_id):
    if request.method == 'POST':
        name = request.form['name']
        nickname = request.form['nickname']
        country = request.form['country']
        age = request.form['age']
        weight_class = request.form['weight_class']

        cursor.execute("UPDATE Fighters SET Name = ?, Nickname = ?, Country = ?, Age = ?, WeightClass = ? WHERE FighterID = ?",
                       (name, nickname, country, age, weight_class, fighter_id))
        conn.commit()
        return jsonify(message='Fighter updated successfully')

    return jsonify(error='Method not allowed')


@app.route('/fighter_logs')
def fighter_logs():
    cursor.execute('SELECT * FROM FighterLog ORDER BY ActionDate DESC')
    fighter_logs = cursor.fetchall()
    return render_template('fighter_logs.html', fighter_logs=fighter_logs)


@app.route('/add_fight', methods=['POST'])
@admin_required
def add_fight():
    if request.method == 'POST':
        event_id = request.form['event_id']
        fighter1_id = request.form['fighter1_id']
        fighter2_id = request.form['fighter2_id']
        winner_name = request.form['winner_name']
        finish_type = request.form['finish_type']
        record_id = request.form['record_id']

        cursor.execute(
            "INSERT INTO Fights (EventID, Fighter1ID, Fighter2ID, WinnerName, FinishType, RecordID) VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, fighter1_id, fighter2_id, winner_name, finish_type, record_id))
        conn.commit()

        # Flash success message
        flash('Fight added successfully', 'success')

        return redirect(url_for('fights'))


@app.route('/update_fight/<int:fight_id>', methods=['POST'])
@admin_required
def update_fight(fight_id):
    if request.method == 'POST':
        event_id = request.form['event_id']
        fighter1_id = request.form['fighter1_id']
        fighter2_id = request.form['fighter2_id']
        winner_name = request.form['winner_name']
        finish_type = request.form['finish_type']
        record_id = request.form['record_id']

        cursor.execute("UPDATE Fights SET EventID = ?, Fighter1ID = ?, Fighter2ID = ?, WinnerName = ?, FinishType = ?, RecordID = ? WHERE FightID = ?",
                       (event_id, fighter1_id, fighter2_id, winner_name, finish_type, record_id, fight_id))
        conn.commit()
        return redirect(url_for('fights'))

@app.route('/delete_fight/<int:fight_id>', methods=['POST'])
@admin_required
def delete_fight(fight_id):
    if request.method == 'POST':
        cursor.execute("DELETE FROM Fights WHERE FightID = ?", (fight_id,))
        conn.commit()
        return redirect(url_for('fights'))

@app.route('/record')
def record():
    cursor.execute('SELECT * FROM Record')
    records = cursor.fetchall()
    return render_template('record.html', records=records)

@app.route('/add_record', methods=['POST'])
@admin_required
def add_record():
    if request.method == 'POST':
        fighter_id = request.form['fighter_id']
        statistics = request.form['statistics']
        ko = request.form['ko']
        submishen = request.form['submishen']
        decision = request.form['decision']

        cursor.execute("INSERT INTO Record (FighterID, [Statistics], KO, Submishen, Decision) VALUES (?, ?, ?, ?, ?)",
                       (fighter_id, statistics, ko, submishen, decision))

        conn.commit()
        return redirect(url_for('record'))

@app.route('/delete_record/<int:record_id>', methods=['POST'])
@admin_required
def delete_record(record_id):
    if request.method == 'POST':
        cursor.execute("DELETE FROM Record WHERE RecordID = ?", (record_id,))
        conn.commit()
        return redirect(url_for('record'))

@app.route('/update_record/<int:record_id>', methods=['POST'])
@admin_required
def update_record(record_id):
    if request.method == 'POST':
        fighter_id = request.form['fighter_id']
        statistics = request.form['statistics']
        ko = request.form['ko']
        submishen = request.form['submishen']
        decision = request.form['decision']

        cursor.execute(
            "UPDATE Record SET FighterID = ?, [Statistics] = ?, KO = ?, Submishen = ?, Decision = ? WHERE RecordID = ?",
            (fighter_id, statistics, ko, submishen, decision, record_id))

        conn.commit()
        return redirect(url_for('record'))


@app.route('/add_event', methods=['POST'])
@admin_required
def add_event():
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']

        try:
            # Convert date string to datetime object
            date = datetime.strptime(date, '%Y-%m-%d').date()

            # Use string formatting to insert values into the SQL query
            query = "INSERT INTO Events (Name, Date, Location) VALUES ('{}', '{}', '{}')".format(name, date, location)
            cursor.execute(query)

            conn.commit()
            return redirect(url_for('events'))
        except Exception as e:
            # Handle any exceptions, such as incorrect date format
            return "Error: {}".format(str(e))


@app.route('/update_event/<int:event_id>', methods=['POST'])
@admin_required
def update_event(event_id):
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']

        try:
            # Format date string to match SQL Server expected format
            formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')

            # Use parameterized query
            query = "UPDATE Events SET Name=?, Date=?, Location=? WHERE EventID=?"
            cursor.execute(query, (name, formatted_date, location, event_id))

            conn.commit()
            return redirect(url_for('events'))
        except Exception as e:
            # Handle any exceptions
            return "Error: {}".format(str(e))


@app.route('/delete_event/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    if request.method == 'POST':
        cursor.execute("DELETE FROM Events WHERE EventID = ?", (event_id,))
        conn.commit()
        return redirect(url_for('events'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)

