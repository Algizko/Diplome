# Для подключения надо настроить DB_CONFIG ниже!!! Под сервер MySQL.

import hashlib
import mysql.connector
from mysql.connector import Error

# ── Настройки подключения ──────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "973100",            # пароль MySQL!!!
    "database": "attendance_system",
    "charset":  "utf8mb4",
}

# ── SQL-схема для авто-создания ─────────────────────────────
_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS users (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        login       VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(64) NOT NULL,
        full_name   VARCHAR(100) NOT NULL,
        role        ENUM('teacher','admin') NOT NULL DEFAULT 'teacher',
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB""",

    """CREATE TABLE IF NOT EXISTS subjects (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        name        VARCHAR(150) NOT NULL,
        teacher_id  INT,
        FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB""",

    """CREATE TABLE IF NOT EXISTS students (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        full_name   VARCHAR(100) NOT NULL,
        phone       VARCHAR(20)  DEFAULT '',
        email       VARCHAR(100) DEFAULT ''
    ) ENGINE=InnoDB""",

    """CREATE TABLE IF NOT EXISTS enrollments (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        student_id  INT NOT NULL,
        subject_id  INT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        UNIQUE KEY uq_enrollment (student_id, subject_id)
    ) ENGINE=InnoDB""",

    """CREATE TABLE IF NOT EXISTS attendance (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        student_id  INT NOT NULL,
        subject_id  INT NOT NULL,
        lesson_date DATE NOT NULL,
        present     TINYINT(1) DEFAULT 0,
        score       INT DEFAULT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    ) ENGINE=InnoDB""",

    """CREATE TABLE IF NOT EXISTS exam_results (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        student_id  INT NOT NULL,
        subject_id  INT NOT NULL,
        score       INT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        UNIQUE KEY uq_exam (student_id, subject_id)
    ) ENGINE=InnoDB""",
]


def _hash(password: str) -> str:
    """SHA-256 хеш пароля"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class Database:
    """Обёртка над MySQL: подключение, авто-создание, CRUD-операции."""

    def __init__(self):
        self.conn = None

    # ── Подключение ────────────────────────────────────────
    def connect(self) -> bool:
        """Подключиться к БД. Если БД не существует — создать."""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            return True
        except Error as exc:
            if exc.errno == 1049:          # Ошибка unknown database
                return self._bootstrap()
            return False

    def _bootstrap(self) -> bool:
        """Создать БД, таблицы и пользователя-администратора."""
        try:
            cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
            conn = mysql.connector.connect(**cfg)
            cur = conn.cursor()
            cur.execute(
                "CREATE DATABASE IF NOT EXISTS attendance_system "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute("USE attendance_system")
            for ddl in _SCHEMA:
                cur.execute(ddl)
            cur.execute(
                "INSERT IGNORE INTO users (login, password_hash, full_name, role) "
                "VALUES (%s, %s, %s, 'admin')",
                ("admin", _hash("admin123"), "Администратор"),
            )
            conn.commit()
            cur.close()
            conn.close()
            self.conn = mysql.connector.connect(**DB_CONFIG)
            return True
        except Error:
            return False

    def disconnect(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()

    # ── Внутренний хелпер ──────────────────────────────────
    def _q(self, sql, params=None, fetch=True):
        self.conn.ping(reconnect=True, attempts=2, delay=1)
        cur = self.conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        if fetch:
            rows = cur.fetchall()
            cur.close()
            return rows
        self.conn.commit()
        lid = cur.lastrowid
        cur.close()
        return lid

    # ── Авторизация ────────────────────────────────────────
    def authenticate(self, login: str, password: str):
        rows = self._q(
            "SELECT id, login, full_name, role FROM users "
            "WHERE login=%s AND password_hash=%s",
            (login, _hash(password)),
        )
        return rows[0] if rows else None

    # ── Пользователи (учителя / админы) ───────────────────
    def get_users(self):
        return self._q(
            "SELECT id, login, full_name, role FROM users ORDER BY full_name"
        )

    def add_user(self, login, password, full_name, role="teacher"):
        return self._q(
            "INSERT INTO users (login, password_hash, full_name, role) "
            "VALUES (%s,%s,%s,%s)",
            (login, _hash(password), full_name, role),
            fetch=False,
        )

    def promote(self, user_id):
        self._q(
            "UPDATE users SET role='admin' WHERE id=%s", (user_id,), fetch=False
        )

    def update_user(self, user_id, full_name, login):
        self._q(
            "UPDATE users SET full_name=%s, login=%s WHERE id=%s",
            (full_name, login, user_id),
            fetch=False,
        )

    def delete_user(self, user_id):
        self._q("DELETE FROM users WHERE id=%s", (user_id,), fetch=False)

    # ── Предметы
    def get_subjects(self):
        return self._q(
            "SELECT s.id, s.name, s.teacher_id, "
            "IFNULL(u.full_name,'—') AS teacher "
            "FROM subjects s LEFT JOIN users u ON s.teacher_id=u.id "
            "ORDER BY s.name"
        )

    def get_subjects_for(self, teacher_id):
        return self._q(
            "SELECT id, name FROM subjects WHERE teacher_id=%s ORDER BY name",
            (teacher_id,),
        )

    def add_subject(self, name, teacher_id):
        return self._q(
            "INSERT INTO subjects (name, teacher_id) VALUES (%s,%s)",
            (name, teacher_id),
            fetch=False,
        )

    def update_subject(self, subject_id, name, teacher_id):
        self._q(
            "UPDATE subjects SET name=%s, teacher_id=%s WHERE id=%s",
            (name, teacher_id, subject_id),
            fetch=False,
        )

    def delete_subject(self, subject_id):
        self._q("DELETE FROM subjects WHERE id=%s", (subject_id,), fetch=False)

    # ── Ученики
    def get_students(self):
        return self._q(
            "SELECT id, full_name, phone, email FROM students ORDER BY full_name"
        )

    def add_student(self, full_name, phone="", email=""):
        return self._q(
            "INSERT INTO students (full_name, phone, email) VALUES (%s,%s,%s)",
            (full_name, phone, email),
            fetch=False,
        )

    def update_student(self, student_id, full_name, phone="", email=""):
        self._q(
            "UPDATE students SET full_name=%s, phone=%s, email=%s WHERE id=%s",
            (full_name, phone, email, student_id),
            fetch=False,
        )

    def delete_student(self, student_id):
        self._q("DELETE FROM students WHERE id=%s", (student_id,), fetch=False)

    # ── Запись на предмет
    def enrolled(self, subject_id):
        return self._q(
            "SELECT s.id, s.full_name FROM students s "
            "JOIN enrollments e ON s.id=e.student_id "
            "WHERE e.subject_id=%s ORDER BY s.full_name",
            (subject_id,),
        )

    def not_enrolled(self, subject_id):
        return self._q(
            "SELECT id, full_name FROM students "
            "WHERE id NOT IN "
            "(SELECT student_id FROM enrollments WHERE subject_id=%s) "
            "ORDER BY full_name",
            (subject_id,),
        )

    def enroll(self, student_id, subject_id):
        self._q(
            "INSERT IGNORE INTO enrollments (student_id, subject_id) "
            "VALUES (%s,%s)",
            (student_id, subject_id),
            fetch=False,
        )

    # ── Посещаемость ──────────────────────────────────────
    def get_attendance(self, subject_id, lesson_date):
        return self._q(
            "SELECT a.id, a.student_id, s.full_name, a.present, a.score "
            "FROM attendance a JOIN students s ON a.student_id=s.id "
            "WHERE a.subject_id=%s AND a.lesson_date=%s "
            "ORDER BY s.full_name",
            (subject_id, lesson_date),
        )

    def save_att(self, student_id, subject_id, lesson_date, present, score):
        row = self._q(
            "SELECT id FROM attendance "
            "WHERE student_id=%s AND subject_id=%s AND lesson_date=%s",
            (student_id, subject_id, lesson_date),
        )
        if row:
            self._q(
                "UPDATE attendance SET present=%s, score=%s WHERE id=%s",
                (present, score, row[0]["id"]),
                fetch=False,
            )
        else:
            self._q(
                "INSERT INTO attendance "
                "(student_id, subject_id, lesson_date, present, score) "
                "VALUES (%s,%s,%s,%s,%s)",
                (student_id, subject_id, lesson_date, present, score),
                fetch=False,
            )

    def lesson_dates(self, subject_id):
        return self._q(
            "SELECT DISTINCT lesson_date FROM attendance "
            "WHERE subject_id=%s ORDER BY lesson_date DESC",
            (subject_id,),
        )

    # ── Результаты экзаменов ──────────────────────────────
    def get_exams(self, subject_id):
        return self._q(
            "SELECT e.student_id, s.full_name, e.score "
            "FROM exam_results e JOIN students s ON e.student_id=s.id "
            "WHERE e.subject_id=%s ORDER BY s.full_name",
            (subject_id,),
        )

    def save_exam(self, student_id, subject_id, score):
        row = self._q(
            "SELECT id FROM exam_results "
            "WHERE student_id=%s AND subject_id=%s",
            (student_id, subject_id),
        )
        if row:
            self._q(
                "UPDATE exam_results SET score=%s WHERE id=%s",
                (score, row[0]["id"]),
                fetch=False,
            )
        else:
            self._q(
                "INSERT INTO exam_results (student_id, subject_id, score) "
                "VALUES (%s,%s,%s)",
                (student_id, subject_id, score),
                fetch=False,
            )

    # ── Данные для прогноза ───────────────────────────────
    def prediction_data(self, subject_id):
        return self._q(
            "SELECT s.id AS student_id, s.full_name, "
            "  AVG(CASE WHEN a.present=1 AND a.score IS NOT NULL "
            "           THEN a.score END) AS avg_score, "
            "  er.score AS exam_score, "
            "  ( SELECT AVG(CASE WHEN a2.present=1 AND a2.score IS NOT NULL "
            "                     THEN a2.score END) "
            "    FROM attendance a2 WHERE a2.student_id = s.id "
            "  ) AS global_avg "
            "FROM students s "
            "JOIN enrollments en ON s.id=en.student_id AND en.subject_id=%s "
            "LEFT JOIN attendance a ON s.id=a.student_id AND a.subject_id=%s "
            "LEFT JOIN exam_results er ON s.id=er.student_id AND er.subject_id=%s "
            "GROUP BY s.id, s.full_name, er.score "
            "ORDER BY s.full_name",
            (subject_id, subject_id, subject_id),
        )


    def prediction_train_all(self):
        return self._q(
            "SELECT "
            "  AVG(CASE WHEN a.present=1 AND a.score IS NOT NULL "
            "           THEN a.score END) AS avg_score, "
            "  er.score AS exam_score "
            "FROM students s "
            "JOIN enrollments en ON s.id=en.student_id "
            "JOIN exam_results er ON s.id=er.student_id "
            "  AND er.subject_id=en.subject_id "
            "LEFT JOIN attendance a ON s.id=a.student_id "
            "  AND a.subject_id=en.subject_id "
            "GROUP BY s.id, en.subject_id, er.score "
            "HAVING avg_score IS NOT NULL"
        )
