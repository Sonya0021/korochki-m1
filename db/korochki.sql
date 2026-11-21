CREATE DATABASE IF NOT EXISTS korochki_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE korochki_db;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    login VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role_id INT NOT NULL DEFAULT 1,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    price DECIMAL(8,2) NOT NULL,
    duration_min INT NOT NULL
);

CREATE TABLE payment_methods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE application_statuses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service_id INT NOT NULL,
    start_date DATETIME NOT NULL,
    payment_method_id INT NOT NULL,
    status_id INT NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (service_id) REFERENCES services(id),
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id),
    FOREIGN KEY (status_id) REFERENCES application_statuses(id)
);

CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Начальные справочники
INSERT INTO roles (id, name) VALUES (1, 'user'), (2, 'admin');

INSERT INTO payment_methods (id, name) VALUES 
(1, 'Наличными в салоне'), 
(2, 'Банковской картой / СБП');

INSERT INTO application_statuses (id, name) VALUES 
(1, 'Новая'), 
(2, 'Идёт обучение'), -- по требованию валидации из таблицы 3.3 шаблона (или можно поменять на 'В работе', если разрешено)
(3, 'Обучение завершено');

-- Услуги парикмахерской (Вариант 6)
INSERT INTO services (name, price, duration_min) VALUES
('Женская модельная стрижка', 1800.00, 60),
('Мужская стрижка и укладка', 1200.00, 45),
('Сложное окрашивание (AirTouch / Балаяж)', 5500.00, 180),
('Укладка вечерняя у топ-стилиста', 2500.00, 60),
('Уходовая спа-процедура для волос', 2100.00, 50);

-- Тестовые учетные записи из пункта 5.3 шаблона (Admin / KorokNET и testuser / qazqaz123)
-- Пароли захешированы через SHA-256
INSERT INTO users (login, password_hash, full_name, phone, email, role_id) VALUES
('Admin', '4d32c3d22284e76f2a655e577e2517d0a6198630f77b3d1f0d315d213d95070e', 'Администратор Салона', '8(999)000-00-00', 'admin@salon.ru', 2),
('testuser', '700b892815d694b45e9f49e8a6b5431c1a9f70e1b182e2b6b7d1a4b6c1646218', 'Иванова Анна Сергеевна', '8(916)123-45-67', 'anna@mail.ru', 1);

INSERT INTO applications (user_id, service_id, start_date, payment_method_id, status_id) VALUES
(2, 1, '2026-11-25 14:00:00', 2, 1),
(2, 3, '2026-11-28 11:30:00', 1, 3);