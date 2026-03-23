from flask import Flask, render_template

from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.quiz import quiz_bp

    app.register_blueprint(quiz_bp, url_prefix="/quiz")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    app.add_url_rule("/", endpoint="main.index")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
