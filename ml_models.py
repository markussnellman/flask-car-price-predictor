import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm

from sklearn import linear_model, metrics
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures


def random_forest_model(X, y, test_size=0.2, n_estimators=1000, random_state=1):
    """
    Does random forest regression with sklearn. 

    Returns regressor, mean absolute error (MAE) and mean absolute percentage error (MAPE).
    """

    # Split into training and validation sets
    X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=test_size)

    # Train model
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
    model.fit(X_train, y_train)

    # Test model
    y_pred = model.predict(X_valid)

    # Compute important error metrics
    MAE = metrics.mean_absolute_error(y_valid, y_pred)
    MAPE = metrics.mean_absolute_percentage_error(y_valid, y_pred)

    return model, MAE, MAPE


def polynomial_model(X, y, test_size=0.2):
    """
    Does polynomial regression with sklearn. 

    Returns regressor, mean absolute error (MAE) and mean absolute percentage error (MAPE).
    """

    # Polynomial regression
    # Create polynomial features of degree 2. Higher degrees will likely overfit.
    poly = PolynomialFeatures(2)

    # Split into training and validation sets
    X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=test_size)
    X_train_poly, X_valid_poly = poly.fit_transform(X_train), poly.fit_transform(X_valid)

    model = linear_model.LinearRegression()
    model.fit(X_train_poly, y_train)

    y_pred = model.predict(X_valid_poly)

    MAE = metrics.mean_absolute_error(y_valid, y_pred)
    MAPE = metrics.mean_absolute_percentage_error(y_valid, y_pred)

    return model, MAE, MAPE