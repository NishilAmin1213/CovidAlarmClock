"""
The purpose of the apicalls module is to contain the functions that return the relevant data
from online api's when called. They are responsible for using the config file to gather the
correct keys, URL's and settings as well as prevent the code from crashing by catching and
logging errors while also allowing the main program to continue running.
Functions:
    get_news(quantity, deleted_notifs, addition) -> list
    get_weather -> str
    get_covid -> str
"""

import json
import logging
import socket
import requests
from uk_covid19 import Cov19API


def get_news(quantity: int, deleted_notifs: list, addition: int) -> list:
    """
    get news it tasked with the role of accessing the news API using the data in the config
    file and returning a list of notification dictionaries containing the latest news articles.
    It also uses parameters such as location from the config file.
    :parameter quantity: quantity represents the number of notifications that are required
                by the calling funtion
    :parameter deleted_notifs: a list containing notifications that have been previously
                deleted, so that the function does not return them again
    :parameter addition: addition is the number to add to the index value of the notifications
                if there are already notifications stored that are not going to be deleted
    :returns list: a list of notification dictionaries are returned to the main program
                containing updated data
    """
    try:
        current_notifs = []

        # get settings and info from config file
        with open('config.json') as json_file:
            data = json.load(json_file)
            key = data['data']['notif_data']['key']
            country = data['data']['notif_data']['country']
            base_url = data['data']['notif_data']['base_url']
            depth = data['data']['notif_data']['depth']

        # create a response by requesting data from the url and key specified by the config file
        response = requests.get(base_url + 'country=' + country + '&sortBy=popularity&'
                                + 'apiKey=' + key)

        # iterate through the response and add news articles that haven't been deleted before
        counter = 0
        while len(current_notifs) < quantity:
            article = response.json()['articles'][counter]
            title = article['title']
            desc = article['description']
            notif = {'title': title, 'content': desc, 'index': len(current_notifs)+addition,
                     'depth': depth}
            counter += 1

            # make sure the notification has data in the content section and hasn't been
            # deleted before
            if (notif not in deleted_notifs) and (notif['content'] is not None):
                current_notifs.append(notif)
        logging.log(20, 'News Data Returned')

        # return the list generated, now containing a number of notification dictionaries
        return current_notifs

    # error catch is the API is down or the key is invalid
    except KeyError:
        logging.log(40, 'News API Key Invalid')
        return []
    except socket.error:
        logging.log(40, 'ConnectionError/SocketError - URL/Request Invalid or '
                        'Internet Disconnected')
        return []


def get_weather() -> str:
    """
    get weather has the role of accessing the weather API using the data in the config
    file and returning a string with a pre-defined level of detail(in the config file).
    It also uses parameters such as location from the config file.
    :returns str: Returns a string with updated weather data incorporated in written
                    english which will be able to be spoken efficiently by pyttsx3 or
                    displayed on the page.
    """
    try:
        # get settings and info from config file
        with open('config.json') as json_file:
            data = json.load(json_file)
            key = data['data']['weather_data']['key']
            city = data['data']['weather_data']['city']
            base_url = data['data']['weather_data']['base_url']
            depth = data['data']['weather_data']['depth']

        # create a response by requesting data from the url and key specified by
        # the config file
        response = requests.get(base_url + city + '&units=metric&appid=' + key)

        # extract data from the api and create a string with relevant information.
        data = response.json()
        msg = 'The weather is ' + data['weather'][0]['description'] + ' and it is ' + \
              str(data['main']['temp']) \
              + ' degrees celsius which feels like ' + str(data['main']['feels_like']) \
              + ' degrees celsius. '

        # if the config file specifies an extended message, then add more data to the string.
        if depth == 1:  # extended message
            msg = msg + 'The humidity is ' + str(data['main']['humidity']) + \
                  ' percent and the wind speed' \
                  + str(data['wind']['speed']) + 'kilometers per hour.'
        logging.log(20, 'Weather Data Returned')

        # return a full string about the weather.
        return msg

    # error catch is the API is down or the key is invalid
    except KeyError:
        logging.log(40, 'KeyErrorWeather - API Key Invalid')
        return ''
    except socket.error:
        logging.log(40, 'ConnectionError/SocketError - URL/Request Invalid or '
                        'Internet Disconnected')
        return ''


def get_covid() -> str:
    """
    get weather has the role of accessing UK GOV covid-19 data returning a
    string with a pre-defined level of detail(in the config file).
    It also uses parameters such as location from the config file.
    :returns str: Returns a string with updated weather data incorporated in written english
                which will be able to be spoken efficiently by pyttsx3 or displayed on the page.
    """
    try:
        # get data from config file
        with open('config.json') as json_file:
            data = json.load(json_file)
            area_type = data['data']['covid_data']['area_type']
            area_name = data['data']['covid_data']['area_name']
            depth = data['data']['covid_data']['depth']

        #request data using the covidAPI module
        england_only = ['areaType=' + area_type, 'areaName=' + area_name]
        cases_and_deaths = {
            "date": "date",
            "areaName": "areaName",
            "areaCode": "areaCode",
            "newCasesByPublishDate": "newCasesByPublishDate",
            "cumCasesByPublishDate": "cumCasesByPublishDate",
            "newDeathsByDeathDate": "newDeathsByDeathDate",
            "cumDeathsByDeathDate": "cumDeathsByDeathDate"}
        api = Cov19API(filters=england_only, structure=cases_and_deaths)
        data = api.get_json()

        # extract specific information from the data returned by the covid method.
        yesterday_cases = data['data'][1]['newCasesByPublishDate']
        yesterday_deaths = data['data'][1]['newDeathsByDeathDate']
        today_cases = data['data'][0]['newCasesByPublishDate']
        new_total_cases = data['data'][0]['cumCasesByPublishDate']

        # construct a suitable message to be returned.
        msg = 'Today there have been ' + str(today_cases) + ' new cases bringing the total to ' + \
              str(new_total_cases) + ' . '
        if depth == 1:
            msg = msg + 'Yesterday there was ' + str(yesterday_cases) + ' new cases and ' + str(
                yesterday_deaths) + ' new deaths'
        logging.log(20, 'Covid Data Returned')
        # return the final message
        return msg

    # error catch is the API is down or the key is invalid
    except socket.error:
        logging.log(40, 'ConnectionError/SocketError - URL/Request Invalid or '
                        'Internet Disconnected')
        return ''
