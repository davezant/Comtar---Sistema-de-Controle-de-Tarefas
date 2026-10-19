import os
from datetime import date
from functools import wraps
from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from models import STATUS_VALIDOS, close_db, init_db
from task_services import TaskService, UserService, ValidationError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-troque-esta-chave")
    app.config["DATABASE"] = os.path.join(BASE_DIR, "comtar.db")
    if config:
        app.config.update(config)

    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                flash("Faça login para continuar.", "erro")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    @app.before_request
    def load_user():
        user_id = session.get("user_id")
        g.user = UserService.get(user_id) if user_id else None

    @app.context_processor
    def inject_globals():
        return {"STATUS_VALIDOS": STATUS_VALIDOS, "hoje": date.today().isoformat()}

    @app.route("/")
    def index():
        return redirect(url_for("tarefas" if g.user else "login"))

    @app.route("/cadastro", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            try:
                UserService.register(
                    request.form.get("name"),
                    request.form.get("email"),
                    request.form.get("password"),
                )
            except ValidationError as e:
                flash(str(e), "erro")
            else:
                flash("Cadastro realizado. Faça login.", "ok")
                return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            user = UserService.authenticate(
                request.form.get("email"), request.form.get("password")
            )
            if user:
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("tarefas"))
            flash("E-mail ou senha incorretos.", "erro")
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        flash("Sessão encerrada.", "ok")
        return redirect(url_for("login"))

    @app.route("/tarefas")
    @login_required
    def tarefas():
        status = request.args.get("status", "")
        lista = TaskService.list(g.user["id"], status)
        return render_template("tasks.html", tarefas=lista, filtro=status)

    @app.route("/tarefas/nova", methods=["GET", "POST"])
    @login_required
    def nova_tarefa():
        form = request.form
        if request.method == "POST":
            try:
                TaskService.create(
                    g.user["id"],
                    form.get("title"),
                    form.get("description"),
                    form.get("deadline"),
                )
            except ValidationError as e:
                flash(str(e), "erro")
            else:
                flash("Tarefa criada.", "ok")
                return redirect(url_for("tarefas"))
        return render_template("task_form.html", tarefa=None, form=form)

    @app.route("/tarefas/<int:task_id>/editar", methods=["GET", "POST"])
    @login_required
    def editar_tarefa(task_id):
        tarefa = TaskService.get(task_id, g.user["id"])
        if tarefa is None:
            abort(404)
        form = request.form
        if request.method == "POST":
            try:
                TaskService.update(
                    task_id,
                    g.user["id"],
                    form.get("title"),
                    form.get("description"),
                    form.get("deadline"),
                    form.get("status"),
                )
            except ValidationError as e:
                flash(str(e), "erro")
            else:
                flash("Tarefa atualizada.", "ok")
                return redirect(url_for("tarefas"))
        return render_template("task_form.html", tarefa=tarefa, form=form)

    @app.route("/tarefas/<int:task_id>/concluir", methods=["POST"])
    @login_required
    def concluir_tarefa(task_id):
        if not TaskService.complete(task_id, g.user["id"]):
            abort(404)
        flash("Tarefa concluída.", "ok")
        return redirect(request.referrer or url_for("tarefas"))

    @app.route("/tarefas/<int:task_id>/excluir", methods=["POST"])
    @login_required
    def excluir_tarefa(task_id):
        if not TaskService.delete(task_id, g.user["id"]):
            abort(404)
        flash("Tarefa excluída.", "ok")
        return redirect(request.referrer or url_for("tarefas"))

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
