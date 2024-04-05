# import os
# import pandas as pd
# import psycopg2
# from .ml_models import random_forest_model, polynomial_model
# from sklearn.preprocessing import MinMaxScaler, PolynomialFeatures
# from .utils import load_and_transform_data, load_from_db, transform_new_data


from app.routes import app, db
from app.models import Car

def test_database_population():
    # Query the Car table to retrieve all car records
    with app.app_context():
        cars = Car.query.limit(10).all()

        # Print the retrieved car data
        for car in cars:
            print(f"Car ID: {car.id}, URL: {car.url}, Price: {car.price}, Mileage: {car.mileage}, HP: {car.hp}")

def test_getters():
    with app.app_context():
        # Query all manufacturers
        manufacturers = db.session.query(Car.manufacturer).distinct().all()
        # A tuple is returned so use list comprehension to extract
        default_manufacturers = [manufacturer[0] for manufacturer in manufacturers]

        print(default_manufacturers)

if __name__ == "__main__":
    # Call the test function to check database population

    with app.app_context():
        db.create_all()
    
    path = 'app/car_db_backup.csv'
    test_database_population()
    # test_getters()