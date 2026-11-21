import hashlib
import re
import os
import pymysql
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # если в XAMPP/MySQL есть пароль, впиши сюда
    'database': 'korochki_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

def pw(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# --- Раздача HTML-страниц ---
@app.route('/')
def index():
    return redirect('/login')

@app.route('/login')
def page_login():
    return send_from_directory(FRONTEND_DIR, 'login.html')

@app.route('/register')
def page_register():
    return send_from_directory(FRONTEND_DIR, 'register.html')

@app.route('/applications')
def page_applications():
    return send_from_directory(FRONTEND_DIR, 'applications.html')

@app.route('/create_application')
def page_create_application():
    return send_from_directory(FRONTEND_DIR, 'create_application.html')

@app.route('/admin')
def page_admin():
    return send_from_directory(FRONTEND_DIR, 'admin.html')

@app.route('/styles.css')
def page_styles():
    return send_from_directory(FRONTEND_DIR, 'styles.css')

# --- API маршруты ---
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json or {}
    login = data.get('login', '').strip()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()

    if not re.match(r'^[A-Za-z0-9]{6,}$', login):
        return jsonify({'error': 'Логин: минимум 6 символов (латиница и цифры)'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Пароль должен содержать не менее 8 символов'}), 400
    if not re.match(r'^[А-Яа-яЁё\s]+$', full_name):
        return jsonify({'error': 'ФИО должно содержать только кириллицу и пробелы'}), 400
    if not re.match(r'^8\(\d{3}\)\d{3}-\d{2}-\d{2}$', phone):
        return jsonify({'error': 'Телефон должен быть в формате 8(XXX)XXX-XX-XX'}), 400
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'error': 'Некорректный формат email'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE login=%s OR email=%s", (login, email))
            if cur.fetchone():
                return jsonify({'error': 'Пользователь с таким логином или email уже существует'}), 409
            cur.execute(
                "INSERT INTO users (login, password_hash, full_name, phone, email, role_id) VALUES (%s, %s, %s, %s, %s, 1)",
                (login, pw(password), full_name, phone, email)
            )
        conn.commit()
        return jsonify({'message': 'Регистрация прошла успешно'}), 201
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    login = data.get('login', '').strip()
    password = data.get('password', '')

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id, u.login, u.full_name, r.name AS role
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.login=%s AND u.password_hash=%s
            """, (login, pw(password)))
            user = cur.fetchone()
            if not user:
                return jsonify({'error': 'Неверный логин или пароль'}), 401
            return jsonify({'message': 'Успешный вход', 'user': user})
    finally:
        conn.close()

@app.route('/api/services', methods=['GET'])
def api_services():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, price, duration_min FROM services")
            return jsonify(cur.fetchall())
    finally:
        conn.close()

@app.route('/api/applications/my', methods=['GET'])
def api_my_applications():
    user_id = request.args.get('user_id')
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, s.name AS service_name, s.price, s.duration_min,
                       DATE_FORMAT(a.start_date, '%%Y-%%m-%%d %%H:%%i') AS start_date,
                       pm.name AS payment_method, st.name AS status
                FROM applications a
                JOIN services s ON a.service_id = s.id
                JOIN payment_methods pm ON a.payment_method_id = pm.id
                JOIN application_statuses st ON a.status_id = st.id
                WHERE a.user_id = %s
                ORDER BY a.id DESC
            """, (user_id,))
            apps = cur.fetchall()

            # Доработка по варианту 6: SUM по чеку пользователя
            cur.execute("""
                SELECT COALESCE(SUM(s.price), 0) AS total_sum
                FROM applications a
                JOIN services s ON a.service_id = s.id
                WHERE a.user_id = %s
            """, (user_id,))
            total_sum = float(cur.fetchone()['total_sum'])

            return jsonify({'applications': apps, 'total_sum': total_sum})
    finally:
        conn.close()

@app.route('/api/applications', methods=['POST'])
def api_create_application():
    data = request.json or {}
    user_id = data.get('user_id')
    service_id = data.get('service_id')
    start_date = data.get('start_date')
    payment_method_id = int(data.get('payment_method_id', 0))

    if not all([user_id, service_id, start_date]) or payment_method_id not in (1, 2):
        return jsonify({'error': 'Заполните все поля корректно'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO applications (user_id, service_id, start_date, payment_method_id, status_id)
                VALUES (%s, %s, %s, %s, 1)
            """, (user_id, service_id, start_date, payment_method_id))
        conn.commit()
        return jsonify({'message': 'Запись на услугу создана'}), 201
    finally:
        conn.close()

@app.route('/api/reviews', methods=['POST'])
def api_create_review():
    data = request.json or {}
    user_id = data.get('user_id')
    text = data.get('text', '').strip()
    if not user_id or not text:
        return jsonify({'error': 'Введите текст отзыва'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO reviews (user_id, text) VALUES (%s, %s)", (user_id, text))
        conn.commit()
        return jsonify({'message': 'Отзыв успешно добавлен'}), 201
    finally:
        conn.close()

@app.route('/api/admin/applications', methods=['GET'])
def api_admin_applications():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.id, u.full_name AS client_name, u.phone,
                       s.name AS service_name, s.price, s.duration_min,
                       DATE_FORMAT(a.start_date, '%%Y-%%m-%%d %%H:%%i') AS start_date,
                       pm.name AS payment_method, a.status_id, st.name AS status
                FROM applications a
                JOIN users u ON a.user_id = u.id
                JOIN services s ON a.service_id = s.id
                JOIN payment_methods pm ON a.payment_method_id = pm.id
                JOIN application_statuses st ON a.status_id = st.id
                ORDER BY a.id DESC
            """)
            apps = cur.fetchall()

            # Доработка по варианту 6: общая сумма по всем чекам (SUM)
            cur.execute("""
                SELECT COALESCE(SUM(s.price), 0) AS total_revenue
                FROM applications a
                JOIN services s ON a.service_id = s.id
            """)
            total_revenue = float(cur.fetchone()['total_revenue'])

            return jsonify({'applications': apps, 'total_revenue': total_revenue})
    finally:
        conn.close()

@app.route('/api/admin/applications/<int:app_id>/status', methods=['PATCH'])
def api_update_status(app_id):
    data = request.json or {}
    status_id = int(data.get('status_id', 0))
    if status_id not in (1, 2, 3):
        return jsonify({'error': 'Недопустимый статус'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE applications SET status_id=%s WHERE id=%s", (status_id, app_id))
        conn.commit()
        return jsonify({'message': 'Статус обновлен'})
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)