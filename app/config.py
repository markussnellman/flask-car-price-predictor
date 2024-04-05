import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy 

app = Flask(__name__, static_folder='static') 
app.secret_key = os.environ.get('CAR_VALUATION_FLASK_KEY')

# Here we specify location of local SQL database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cars.db"
# We're not gonna track changes to our database for dev purposes
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['EXPLAIN_TEMPLATE_LOADING'] = True

# Create instance of DB
db = SQLAlchemy(app)
