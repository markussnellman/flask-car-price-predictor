import os
import pandas as pd
import requests
import time
from selectolax.parser import HTMLParser
from .utils import get_car_info

base_url = os.environ.get('CAR_VALATION_BASE_URL')

def scrape(manufacturer: str, model: str) -> list[dict]:
    """
    Scrapes car data using the manufacturer and model strings in the url.

    Returns a list of dictionaries containing information about each car.
    """

    # get number of cars from inital request
    start_url = f"{base_url}/{manufacturer}/{model}"
    response = requests.get(start_url)
    start_html = HTMLParser(response.text)
    # number of cars at top of page inside span of div
    n_cars = int(start_html.css_first('div.u-textCenter.u-marginTmd').css_first('span').text().replace(" ", ""))

    # get full html using number of cars
    url = f"{base_url}/{manufacturer}/{model}?limit={n_cars}"
    response = requests.get(url)
    html = HTMLParser(response.text)

    # get url to all cars
    car_urls = []
    for i, link in enumerate(html.css('a.go_to_detail')[0:n_cars]):
        car_urls.append(link.attributes['href'])

    result = []
    # iterate over cars 
    for i in range(0, n_cars):
        # sleep for short time to not overload server
        time.sleep(0.1)
        
        print(f"Fetching car #{i+1} of {n_cars}")
        
        url = car_urls[i]
        response = requests.get(url)
        html = HTMLParser(response.text)

        try:
            result.append(get_car_info(url, html))
            
            # Append manufacturer and model to each dict.
            result[i]['manufacturer'] = manufacturer
            result[i]['model'] = model

        except (AttributeError, ValueError) as error:
            print(f'Car #[i] could not load url, due to {error}')
            result.append({})

    return result


if __name__ == "__main__":
    import os
    from utils import save_to_cloud

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
