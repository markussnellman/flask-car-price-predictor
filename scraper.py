import os
import pandas as pd
import requests
import time
from selectolax.parser import HTMLParser
from utils import get_car_info

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
    manufacturer = 'hyundai'
    model = 'tucson'
    print(scrape(manufacturer, model))
