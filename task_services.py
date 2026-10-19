import sqlite3
from datetime import date, datetime
from werkzeug.security import check_password_hash, generate_password_hash
from models import STATUS_VALIDOS, PENDENTE, CONCLUIDA, get_db


class ValidationError(Exception):
    pass


class UserService:
    @staticmethod
    def register(name, email, password):
        name = (name or "").strip()
        email = (email or "").strip().lower()
        if not name:
            raise ValidationError("O nome é obrigatório.")
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValidationError("E-mail inválido.")
        if len(password or "") < 6:
            raise ValidationError("A senha deve ter no mínimo 6 caracteres.")
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, pwd_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            raise ValidationError("Já existe um usuário com este e-mail.")

    @staticmethod
    def authenticate(email, password):
        email = (email or "").strip().lower()
        user = get_db().execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if user and check_password_hash(user["pwd_hash"], password or ""):
            return user
        return None

    @staticmethod
    def get(user_id):
        return get_db().execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def _validate(title, description, deadline, status=None):
    title = (title or "").strip()
    description = (description or "").strip()
    if not title:
        raise ValidationError("O título é obrigatório.")
    if len(title) > 64:
        raise ValidationError("O título deve ter no máximo 64 caracteres.")
    if len(description) > 256:
        raise ValidationError("A descrição deve ter no máximo 256 caracteres.")
    try:
        datetime.strptime(deadline or "", "%Y-%m-%d")
    except ValueError:
        raise ValidationError("Informe um prazo válido.")
    if status is not None and status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido.")
    return title, description


class TaskService:
    @staticmethod
    def create(user_id, title, description, deadline):
        title, description = _validate(title, description, deadline)
        db = get_db()
        cur = db.execute(
            "INSERT INTO tasks (title, description, creation_date, deadline_date, status, user_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, date.today().isoformat(), deadline, PENDENTE, user_id),
        )
        db.commit()
        return cur.lastrowid

    @staticmethod
    def list(user_id, status=None):
        sql = "SELECT * FROM tasks WHERE user_id = ?"
        params = [user_id]
        if status in STATUS_VALIDOS:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY deadline_date ASC, id ASC"
        return get_db().execute(sql, params).fetchall()

    @staticmethod
    def get(task_id, user_id):
        return get_db().execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        ).fetchone()

    @staticmethod
    def update(task_id, user_id, title, description, deadline, status):
        if TaskService.get(task_id, user_id) is None:
            return False
        title, description = _validate(title, description, deadline, status)
        db = get_db()
        db.execute(
            "UPDATE tasks SET title = ?, description = ?, deadline_date = ?, status = ? "
            "WHERE id = ? AND user_id = ?",
            (title, description, deadline, status, task_id, user_id),
        )
        db.commit()
        return True

    @staticmethod
    def complete(task_id, user_id):
        db = get_db()
        cur = db.execute(
            "UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?",
            (CONCLUIDA, task_id, user_id),
        )
        db.commit()
        return cur.rowcount > 0

    @staticmethod
    def delete(task_id, user_id):
        db = get_db()
        cur = db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        )
        db.commit()
        return cur.rowcount > 0
