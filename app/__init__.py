# import os
# from flask import Flask
# from .routes import main_bp


# def create_app():
#     app = Flask(__name__, static_folder='static') 
#     app.secret_key = os.environ.get('CAR_VALUATION_FLASK_KEY')

#     # Register the Blueprint
#     app.register_blueprint(main_bp)

#     return app