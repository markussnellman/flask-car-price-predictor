import numpy as np
import os
import pandas as pd
import psycopg2
import sqlalchemy
from selectolax.parser import HTMLParser
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import create_engine
from typing import Callable



# Column datatypes
col_dtype = {'url': str, 
             'price': float, 
             'mileage': float, 
             'hp': float, 
             'gearbox': str, 
             'traffic_date': str, 
             'owners': float, 
             'fuel': str,
             'manufacturer': str,
             'model': str}


### Functions
def get_car_info(url: str, html) -> dict:
    """
    Scrapes car (manufacturer, model) information from a particular car url using corresponding html text.

    Information: 
    - id (from url)
    - url
    - price
    - mileage
    - hp
    - gearbox
    - traffic_date
    - owners
    - fuel
    - manufacturer
    - model
    """

    info = {}
    info['id'] = int(url.split('-')[-1])
    info['url'] = url

    # Car price
    price = int(html.css_first('div.Grid-cell.u-size1of2.u-textRight').css_first('span').text().replace(" ", "")[:-2])
  
    info['price'] = price

    # Car info sits in a ul
    ul = html.css_first('ul.List.List--horizontal.List--bordered.u-sm-size1of1.List--allbordered.u-marginBlg')
    lis = ul.css('li')
    
    # Iterate over list items
    for li in lis:
        # Check titles that contain the data
        title = li.css_first('h5').text()

        if title == "Mil":
            info['mileage'] = int(li.css_first('p').text().replace(" ", ""))

        if title == "Hästkrafter":
            info['hp'] = int(li.css_first('p').text().replace(" ", ""))

        if title == "Växellåda":
            info['gearbox'] = li.css_first('p').text().strip().lower()

        if title == "1:a regdatum":
            info['traffic_date'] = li.css_first('p').text().strip().lower()

        if title == "Antal ägare":
            info['owners'] = int(li.css_first('p').text())

        if title == "Drivmedel":
            info['fuel'] = li.css_first('p').text().strip().lower()

    return info


def save_to_cloud(data: list, table_name: str, path: str, required_cols = ['id', 'url', 'price', 'mileage', 'hp', 'gearbox', 'traffic_date', 'owners', 'fuel', 'manufacturer', 'model']):
    """
    Saves data in df to table with table_name in Render cloud database.

    path is the external url to the Render database.

    required_cols is a list of keys to data that will represent the columns in the table.
    """
    
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
        path,
    )
        
        # Cursor does SQL operations
        cursor = conn.cursor()

        # Create a table in the database, if it does not already exist
        create_query = f"""CREATE TABLE IF NOT EXISTS {table_name}(
            id INT PRIMARY KEY,
            url TEXT,
            price INT,
            mileage INT,
            hp INT,
            gearbox VARCHAR(255),
            traffic_date VARCHAR(255),
            owners INT,
            fuel VARCHAR(255),
            manufacturer VARCHAR(255),
            model VARCHAR(255)
        );
        """
        cursor.execute(create_query)

        # Filter the data such that only entries with all keys will be inserted to table
        filtered_data = [d for d in data if all(key in d for key in required_cols)]

        # Insert into table
        for item in filtered_data:
            values = [item[col] for col in required_cols]
            query = f"""
                    INSERT INTO {table_name} ({', '.join(required_cols)})
                    VALUES ({', '.join(['%s'] * len(required_cols))})
                    ON CONFLICT (id) DO NOTHING;
                    """
            cursor.execute(query, values)

        # Commit changes
        conn.commit()

        print(f"Uploaded data on {filtered_data[0]['manufacturer']} {filtered_data[0]['model']} to {table_name}.")

    except Exception as e:
        print(e)

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def load_from_csv(path: str, col_dtype=col_dtype) -> pd.DataFrame:
    """
    Loads csv file to Pandas Dataframe.
    """
    df = pd.read_csv(path, dtype=col_dtype)
    return df


def load_from_db(path: str, col_dtype=col_dtype, manufacturer='', model='') -> pd.DataFrame:
    """
    Loads from database to Pandas Dataframe using SQLAlchemy.
    """
    # Note that for SQL alchemy, the path address needs to be postgresql
    engine = create_engine(path.replace('postgres', 'postgresql', 1))
    query = f"""
    SELECT *
    FROM cars
    WHERE LOWER(manufacturer) = '{manufacturer.lower()}' AND LOWER(model) = '{model.lower()}';
    """
    df = pd.read_sql(query, engine)
    return df


def load_and_transform_data(strategy: Callable, path: str, **kwargs):
    """
    Reads car data and returns two dataframes X, y. X is the feature data containing price, mileage, hp, gearbox, car_age, owners, and fuel.
    car_age is calculated in years from traffic_date. NaN rows and redundant columns (manufacturer, model) are dropped. 
    
    gearbox and fuel are categorical variables and are converted to numerical dummy variables.
    
    y is the target price data.
    """

    df = strategy(path, **kwargs)

    # Drop id, url, manufacturer, model
    df = df.drop(columns=['id', 'url', 'manufacturer', 'model'])

    # Convert traffic_date to age in years
    df['traffic_date'] = pd.to_datetime(df['traffic_date'])
    current_date = pd.to_datetime('today')
    df['car_age'] = (current_date - df['traffic_date']).dt.days / 365
    
    # Drop NaNs and split dataframe to X, y.
    df = df.dropna()
    X = df[['mileage', 'hp', 'gearbox', 'car_age', 'owners', 'fuel']]
    y = df['price']

    # Check if there are more than one type in the categorical variables.
    # If so, we need to create appropriate dummy variables, and drop
    # the original categorical variable.
    num_categories_gearbox = df['gearbox'].nunique()
    num_categories_fuel = df['fuel'].nunique()

    if num_categories_gearbox > 1:
        X = pd.get_dummies(X, columns=['gearbox'], drop_first=True, dtype=int)
    else:
        X = X.drop(columns = ['gearbox'])

    if num_categories_fuel > 1:
        X = pd.get_dummies(X, columns=['fuel'], drop_first=True, dtype=int)
    else:
        X = X.drop(columns = ['fuel'])

    return X, y


def transform_new_data(new_data: dict, X: pd.DataFrame, scaler: MinMaxScaler) -> pd.DataFrame:
    """
    Transforms a new dataset (dict) to an appropriately formatted
    dataframe. 

    The dict is expected to have the following columns:
    - mileage: int
    - hp: int
    - gearbox: str
    - traffic_date: str
    - owners: int
    - fuel: str

    X is the original dataset and is required to transform the 
    columns of the new data to the same format.

    The scaler is assumed to have been applied to X and is used
    to scale the numerical columns in the new data in the same way.
    """
    df_new_data = pd.DataFrame(new_data)

    # Convert traffic_date to age in years
    df_new_data['traffic_date'] = pd.to_datetime(df_new_data['traffic_date'])
    current_date = pd.to_datetime('today')
    df_new_data['car_age'] = (current_date - df_new_data['traffic_date']).dt.days / 365
    df_new_data.drop(columns=['traffic_date'], inplace=True)

    # Fix dummy columns so df identical to training data
    df_new_data = pd.get_dummies(df_new_data, columns=['gearbox', 'fuel'])
    df_new_data = df_new_data.reindex(columns=X.columns, fill_value=0)

    # Transform numerical data
    df_new_data[['mileage', 'hp', 'car_age', 'owners']] = scaler.transform(df_new_data[['mileage', 'hp', 'car_age', 'owners']])

    return df_new_data


### Database functions
db_url = os.environ.get('RENDER_TEST_DB_EXTERNAL_URL')

def database_interaction(path):
    def decorator(func):
        def wrapper(*args, **kwargs):
            connection = None
            cursor = None
            result = []

            try:
                # Connect to the database
                connection = psycopg2.connect(path)
                cursor = connection.cursor()

                # Call the original function
                result = func(cursor, *args, **kwargs)

                # Add capitalization
                result = [r.capitalize() for r in result]

            except Exception as e:
                print(e)

            finally: 
                # Close the cursor and connection
                if cursor is not None:
                    cursor.close()

                if connection is not None:
                    connection.close()

                return result
        return wrapper
    return decorator

@database_interaction(db_url)
def get_manufacturers_in_db(cursor):
    """
    Returns a list of all unique car manufacturers in table_name. 

    Path is the url to the Postgres database.
    """
    manufacturers = []
    
    select_query = f"""SELECT DISTINCT LOWER(manufacturer)
                    FROM cars
                    ORDER BY LOWER(manufacturer);"""
    cursor.execute(select_query)

    for row in cursor.fetchall():
        manufacturers.append(*row)

    manufacturers = [m.capitalize() for m in manufacturers]

    return manufacturers

@database_interaction(db_url)
def get_models_in_db(cursor, manufacturer):

    models = []

    # Get query
    # select_query = f"""SELECT DISTINCT model
    #                 FROM cars
    #                 WHERE LOWER(manufacturer) = '{manufacturer.lower()}';"""
    select_query = f"""SELECT model
                    FROM cars
                    WHERE lower(manufacturer) = '{manufacturer.lower()}'  
                    GROUP BY model
                    HAVING COUNT(*) > 30;"""
    cursor.execute(select_query)

    for row in cursor.fetchall():
        models.append(*row)

    return models

@database_interaction(db_url)
def get_fuels_in_db(cursor, manufacturer,  model):

    fuels = []

    # Get query
    select_query = f"""SELECT DISTINCT fuel
                    FROM cars
                    WHERE LOWER(manufacturer) = '{manufacturer.lower()}' AND LOWER(model) = '{model.lower()}';"""
    cursor.execute(select_query)
    
    for row in cursor.fetchall():
        fuels.append(*row)

    return fuels


@database_interaction(db_url)
def get_gearboxes_in_db(cursor, manufacturer, model):

    gearboxes = []

    # Get query
    select_query = f"""SELECT DISTINCT gearbox
                    FROM cars
                    WHERE LOWER(manufacturer) = '{manufacturer.lower()}' AND LOWER(model) = '{model.lower()}';"""
    cursor.execute(select_query)
    
    for row in cursor.fetchall():
        gearboxes.append(*row)

    return gearboxes

if __name__=="__main__":
    db_url = os.environ.get('RENDER_TEST_DB_EXTERNAL_URL')
    manufacturer = 'volvo'
    model = 'xc60'

    X, y = load_and_transform_data(load_from_db, db_url, manufacturer=manufacturer, model=model)

    print('\n\n')
    print(X.head())