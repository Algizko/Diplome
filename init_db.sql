-- ============================================================
-- Схема БД: attendance_system
-- Система учёта посещаемости образовательных курсов
-- ============================================================

CREATE DATABASE IF NOT EXISTS attendance_system
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE attendance_system;

-- Пользователи (учителя и администраторы)
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    login       VARCHAR(50)  UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL,
    full_name   VARCHAR(100) NOT NULL,
    role        ENUM('teacher','admin') NOT NULL DEFAULT 'teacher',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Предметы / курсы
CREATE TABLE IF NOT EXISTS subjects (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    teacher_id  INT,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Ученики
CREATE TABLE IF NOT EXISTS students (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(100) NOT NULL,
    phone       VARCHAR(20)  DEFAULT '',
    email       VARCHAR(100) DEFAULT ''
) ENGINE=InnoDB;

-- Записи учеников на предметы
CREATE TABLE IF NOT EXISTS enrollments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    subject_id  INT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE KEY uq_enrollment (student_id, subject_id)
) ENGINE=InnoDB;

-- Посещаемость и оценки за занятия
CREATE TABLE IF NOT EXISTS attendance (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    subject_id  INT NOT NULL,
    lesson_date DATE NOT NULL,
    present     TINYINT(1) DEFAULT 0,
    score       INT DEFAULT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Результаты экзаменов (для обучения модели регрессии)
CREATE TABLE IF NOT EXISTS exam_results (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    subject_id  INT NOT NULL,
    score       INT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE KEY uq_exam (student_id, subject_id)
) ENGINE=InnoDB;

-- Администратор по умолчанию: admin / admin123
INSERT IGNORE INTO users (login, password_hash, full_name, role)
VALUES ('admin', SHA2('admin123', 256), 'Администратор', 'admin');
