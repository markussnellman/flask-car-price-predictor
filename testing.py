import os
import pandas as pd
import psycopg2
from ml_models import random_forest_model, polynomial_model
from sklearn.preprocessing import MinMaxScaler, PolynomialFeatures
from utils import load_and_transform_data, load_from_db, transform_new_data


db_url = os.environ.get('RENDER_TEST_DB_EXTERNAL_URL')
manufacturer = 'nissan'
model = 'micra'
test_size = 0.1

X, y = load_and_transform_data(load_from_db, db_url, manufacturer=manufacturer, model=model)

# Scale the numerical variables with a min-max scaler
scaler = MinMaxScaler()
X[['mileage', 'hp', 'car_age', 'owners']] = scaler.fit_transform(X[['mileage', 'hp', 'car_age', 'owners']])

#Apply ML models
rfm, MAE_rf, MAPE_rf = random_forest_model(X, y, test_size=test_size)
pm, MAE_pm, MAPE_pm = polynomial_model(X, y, test_size=test_size)

if MAPE_rf < MAPE_pm:
    print(f"Random forest gave best results with MAPE: {MAPE_rf}")
    MAPE = MAPE_rf
else:
    print(f"Polynomial model gave best results with MAPE: {MAPE_pm}")
    MAPE = MAPE_pm

"""
Challenge: give new data the same categorical structure as the old data.
"""

mileage = 11000
hp = 80
traffic_date = '2011-01-01'
owners = 2
fuel = 'bensin'
gearbox = 'manuell'

new_data = {
    'mileage': [mileage],
    'hp': [hp],
    'traffic_date': [traffic_date],
    'fuel': [fuel],
    'gearbox': [gearbox],
    'owners': [owners],
}

df_new_data = transform_new_data(new_data, X, scaler)

# Make prediction
if MAPE_rf < MAPE_pm:
    predicted_price = rfm.predict(df_new_data)
else:
    # Transform w\ polynomial features
    poly = PolynomialFeatures(2)
    df_new_data = poly.fit_transform(df_new_data)
    predicted_price = pm.predict(df_new_data)

print(f"Price prediction: {round(predicted_price[0], -3)} +- {round(predicted_price[0] * MAPE, -2)} kr")