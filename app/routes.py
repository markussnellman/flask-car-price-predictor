import os
from flask import Blueprint

from flask import Flask, render_template, request, flash, jsonify
from .ml_models import polynomial_model, random_forest_model
from .utils import get_manufacturers_in_db, get_models_in_db, get_fuels_in_db, get_gearboxes_in_db, load_and_transform_data, transform_new_data, load_from_db
from sklearn.preprocessing import MinMaxScaler, PolynomialFeatures


# Create a Blueprint instance
main_bp = Blueprint('main', __name__)

db_url = os.environ.get('RENDER_TEST_DB_EXTERNAL_URL')

manufacturers = get_manufacturers_in_db()

@main_bp.route('/_update_car_dropdown')
def update_car_dropdown():
    
    """
    Updates car model dropdowns.
    """

    # the value of the first dropdown = maufacturer (selected by the user)
    selected_manufacturer = request.args.get('selected_manufacturer', type=str)

    # get values for the second dropdown
    updated_models = get_models_in_db(selected_manufacturer)

    # create the values in the dropdown as a html string
    html_string_selected = ''
    for entry in updated_models:
        html_string_selected += '<option value="{}">{}</option>'.format(entry, entry)

    return jsonify(html_string_selected=html_string_selected)


@main_bp.route('/_update_fuel_and_gearbox_dropdown', methods=['GET'])
def update_fuel_and_gearbox_dropdown():
    """
    Updates fuel and gearbox dropdowns
    """

    # the value of the first dropdown = maufacturer (selected by the user)
    selected_manufacturer = request.args.get('selected_manufacturer', type=str)
    selected_model = request.args.get('selected_model', type=str)

    # get the fuel and gearboxes from db
    print("Getting stuff from DB.")
    print(f"Manufacturer: {selected_manufacturer}, model: {selected_model}")
    fuels = get_fuels_in_db(selected_manufacturer, selected_model)
    gearboxes = get_gearboxes_in_db(selected_manufacturer, selected_model)

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


@main_bp.route('/_predict_price')
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
    X, y = load_and_transform_data(load_from_db, db_url, manufacturer=selected_manufacturer, model=selected_model)
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

    
@main_bp.route('/')
def index():

    """
    initialize drop down menus
    """

    default_manufacturers = manufacturers
    default_models = get_models_in_db(default_manufacturers[0])

    default_fuels = get_fuels_in_db(default_manufacturers[0], default_models[0])
    default_gearboxes = get_gearboxes_in_db(default_manufacturers[0], default_models[0])

    return render_template('index.html',
                       all_manufacturers = default_manufacturers,
                       all_models = default_models,
                       all_fuels = default_fuels,
                       all_gearboxes = default_gearboxes)