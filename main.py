import os
import pandas as pd

from scraper import scrape
from utils import col_dtype, save_to_cloud, load_from_db, get_manufacturers_in_db, get_models_in_db, get_fuels_in_db, get_gearboxes_in_db

url = os.environ.get('RENDER_TEST_DB_EXTERNAL_URL')

cars = {'Audi': ['A6', 'A4', 'A3', 'A5', 'Q5'],
        'BMW': ['520', '320', 'X3', 'X5', '118', 'X1'],
        'Citroen': ['C3', 'C4', 'C5'],
        'Dacia': ['Sandero', 'Duster'],
        'Fiat': ['500'],
        'Honda': ['CR-V', 'Jazz'],
        'Hyundai': ['i10', 'i30', 'Bayon'],
        'Mazda': ['CX-60', '2', 'CX-30', 'MX-30'],
        'Mercedes': ['E300'],
        'Mitsubishi': ['Outlander'],
        'Volvo': ['V60', 'V70', 'XC90', 'V40', 'V90', 'S60'],
        'Volkswagen': ['Tiguan', 'Touran', 'ID-4', 'T-Roc'],
        'Kia': ['Niro', 'Sorento'],
        'Toyota': ['RAV4', 'C-HR', 'Corolla-Verso', 'Auris', 'Yaris', 'Proace'],
        'Nissan': ['Qashqai', 'Juke'],
        'Opel': ['Vivaro', 'Corsa'],
        'Peugeot': ['3008', '308', '2008'],
        'Renault': ['Clio', 'Captur', 'Kangoo'],
        'Seat': ['Leon', 'Ibiza', 'Arona'],
        'Ford': ['Kuga', 'Focus', 'Fiesta', 'Mondeo', 'Mustang'],
        'Skoda': ['Octavia', 'Superb'],
        'Subaru': ['Outback']}

"""
VW ID-4 probably not inserted to DB. Error: List index out or range (How's that possible?)
Skoda enyaq same problem
Wonder if it's something with the electric cars
"""
manufacturers = ['Skoda', 'Subaru']

for manufacturer in manufacturers:
    for model in cars[manufacturer]:
        result = scrape(manufacturer, model)
        save_to_cloud(result, 'cars', url)

