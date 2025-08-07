from flask import Flask
from app.routes import ui
from app.api import api

def create_app():
    app = Flask(__name__)
    app.register_blueprint(api)
    app.register_blueprint(ui)
    return app
