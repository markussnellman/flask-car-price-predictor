from flask import render_template, request, jsonify, Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os

from .models import Car
from sklearn.preprocessing import MinMaxScaler, PolynomialFeatures
from .ml_models import polynomial_model, random_forest_model
from .utils import load_and_transform_data, transform_new_data, load_from_db, load_from_internal_db

app = Flask(__name__, static_folder='static') 
app.secret_key = os.environ.get('CAR_VALUATION_FLASK_KEY')

# Here we specify location of local SQL database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cars.db"
# We're not gonna track changes to our database for dev purposes
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['EXPLAIN_TEMPLATE_LOADING'] = True

# Create instance of DB
db = SQLAlchemy(app)


@app.route('/')
def index():

    """
    initialize drop down menus
    """

    # Query all manufacturers. Returns like a list of one element tuples.
    manufacturers = db.session.query(Car.manufacturer).distinct().all()
    # A tuple is returned so use list comprehension to extract
    default_manufacturers = [manufacturer[0] for manufacturer in manufacturers]

    # Query models from the first manufacturer
    models = db.session.query(Car.model).filter_by(manufacturer=default_manufacturers[0]).distinct().all()
    # Extract model names to a list
    default_models = [model[0] for model in models]

    # Query the fuels
    fuels = db.session.query(Car.fuel).filter_by(manufacturer=default_manufacturers[0],
                                                 model=default_models[0]).distinct().all()
    default_fuels = [fuel[0] for fuel in fuels]

    # Query the gearboxes
    gearboxes = db.session.query(Car.gearbox).filter_by(manufacturer=default_manufacturers[0],
                                                 model=default_models[0]).distinct().all()
    default_gearboxes = [gearbox[0] for gearbox in gearboxes]

    return render_template('index.html',
                       all_manufacturers = default_manufacturers,
                       all_models = default_models,
                       all_fuels = default_fuels,
                       all_gearboxes = default_gearboxes)


@app.route('/_update_car_dropdown')
def update_car_dropdown():
    
    """
    Updates car model dropdowns on changing manufacturer.
    """

    # the value of the first dropdown = maufacturer (selected by the user)
    selected_manufacturer = request.args.get('selected_manufacturer', type=str)
    print(selected_manufacturer)

    # get values for the second dropdown
    models = db.session.query(Car.model).filter_by(manufacturer=selected_manufacturer).distinct().all()
    # Extract model names to a list
    updated_models = [model[0] for model in models]
    print(updated_models)
    # create the values in the dropdown as a html string
    html_string_selected = ''
    for entry in updated_models:
        html_string_selected += '<option value="{}">{}</option>'.format(entry, entry)

    print(html_string_selected)

    return jsonify(html_string_selected=html_string_selected)


@app.route('/_update_fuel_and_gearbox_dropdown', methods=['GET'])
def update_fuel_and_gearbox_dropdown():
    """
    Updates fuel and gearbox dropdowns upon changing model.
    """

    # the value of the first dropdown = maufacturer (selected by the user)
    selected_manufacturer = request.args.get('selected_manufacturer', type=str)
    selected_model = request.args.get('selected_model', type=str)

    # get the fuel and gearboxes from db
     # Query the gearboxes
    gearboxes = db.session.query(Car.gearbox).filter_by(manufacturer=selected_manufacturer,
                                                 model=selected_model).distinct().all()
    gearboxes = [gearbox[0] for gearbox in gearboxes]

    # Query the fuels
    fuels = db.session.query(Car.fuel).filter_by(manufacturer=selected_manufacturer,
                                                 model=selected_model).distinct().all()
    fuels = [fuel[0] for fuel in fuels]


    # create the values in the dropdowns as a html string
    html_fuels = ''
    for fuel in fuels:
        html_fuels += '<option value="{}">{}</option>'.format(fuel, fuel)

    html_gearboxes = ''
    for gearbox in gearboxes:
        html_gearboxes += '<option value="{}">{}</option>'.format(gearbox, gearbox)
   
    response_data = {
        'html_fuels': html_fuels,
        'html_gearboxes': html_gearboxes
    }

    return jsonify(response_data)


@app.route('/_predict_price')
def predict_price():

    # Get all data from user input
    selected_manufacturer = request.args.get('selected_manufacturer', type=str)
    selected_model = request.args.get('selected_model', type=str)

    mileage = request.args.get('mileage', type=int)
    hp = request.args.get('hp', type=int)
    traffic_date = request.args.get('traffic_date', type=str)
    selected_fuel = request.args.get('selected_fuel', type=str)
    selected_gearbox = request.args.get('selected_gearbox', type=str)
    owners = request.args.get('owners', type=int)

    # Load the training data from DB
    X, y = load_and_transform_data(load_from_internal_db, '', manufacturer=selected_manufacturer, model=selected_model, db=db, table=Car)
    n_cars = X.shape[0]

    # Scale the numerical variables with a min-max scaler
    scaler = MinMaxScaler()
    X[['mileage', 'hp', 'car_age', 'owners']] = scaler.fit_transform(X[['mileage', 'hp', 'car_age', 'owners']])

    # Transform input data to appropriate format
    new_data = {
        'mileage': [mileage],
        'hp': [hp],
        'traffic_date': [traffic_date],
        'fuel': [selected_fuel],
        'gearbox': [selected_gearbox],
        'owners': [owners],
    }
    df_new_data = transform_new_data(new_data, X, scaler)

    #Apply ML models to test data
    test_size = 0.15 # this is somewhat arbitrary
    rfm, MAE_rf, MAPE_rf = random_forest_model(X, y, test_size=test_size)
    pm, MAE_pm, MAPE_pm = polynomial_model(X, y, test_size=test_size)

    # Use the best performing model based on mean absolute percentage error
    if MAPE_rf < MAPE_pm:
        MAPE = MAPE_rf
        predicted_price = rfm.predict(df_new_data)[0]
        model_type = 'random forest-modell'
    else:
        MAPE = MAPE_pm
        poly = PolynomialFeatures(2)
        df_new_data = poly.fit_transform(df_new_data)
        predicted_price = pm.predict(df_new_data)[0]
        model_type = 'polynom-modell'

    result = {'predicted_price': round(predicted_price, -3),
              'error': round(predicted_price * MAPE, -2),
              'n_cars': n_cars,
              'model_type': model_type}
    return jsonify(result)
