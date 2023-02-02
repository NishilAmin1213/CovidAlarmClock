"""
This Module holds the code for the Alarm class along with the getter function and its other methods.
It is used to represent alarms within them main app and allow actions to be carried out based on the
instances data.
Classes:
    Alarm
"""

import time
import logging
from datetime import datetime
import pyttsx3
from apicalls import get_covid, get_news, get_weather


class Alarm:
    """
    A Class to represent an Alarm which will be used within the flask application

    Attributes
    ----------
    message : str
        the message the user requires to be spoken when the alarm rings
    content : list
        a list contaning the time and date of when the alarm is due to ring
    news : int
        an integer of either 1 or 0 to decide if the news should be spoken when the alarm rings
    weather : int
        an integer of either 1 or 0 to decide if the weather should be spoken when the alarm rings
    total_alarms : int
        an integer of the total number of alarms that have been created, this is used to assign a
        unique id to the alarm
    alarm_list : list
        a list of all active alarms, this is used to decide if there are any coinciding alarms and
        hence change the
        priority of this alarm (newer alarms ring first and are assigned a higher priority)

    Methods
    -------
    get_data():
        Gets relevant data of the alarm and collates it into a dictionary to be returned
    ring():
        Gathers the up to date information about covid data, and the news and weather if needed to
        create a well spoken string which will be spoken by pyttsx3 to ring the alarm.
    get_seconds():
        get_seconds takes the time and date of when the alarm is due to go off and the current time
        and date, to calculate the number of seconds until the alarm is due to ring. This integer is
        then returned so the alarm can be scheduled.
    """
    def __init__(self, message, content, news, weather, alarm_list):
        """
        The init function takes all the parameters of the alarm, and is responsible for
        instantiating the correct alarm with the correct priority and id.
        :param message: str
        :param content: list
        :param news: int
        :param weather: int
        :param alarm_list: list
        """
        self.title = message + ':' + str(len(alarm_list))
        self.content = "Time = " + content[1] + ", Date = " + content[0]
        self.date_time = content
        self.news = news
        self.weather = weather
        self.id = str(len(alarm_list))
        coinciding_alarms = 1
        for alarm in alarm_list:
            if alarm.get_data()['date_time'] == content:
                coinciding_alarms += 1
        self.priority = coinciding_alarms
        dat = 'Alarm Instance ' + str(len(alarm_list)) + ' Created'
        logging.log(20, dat)

    def get_data(self):
        """
        Gets relevant data of the alarm and collates it into a dictionary to be returned
        :returns dict: Returns a dictionary holding all the relevant data of the alarm
                (not required in python as data belonging to an object can be directly accessed,
                however good practise to use it to prevent unauthorised access of data variables)
        """
        dat = 'Alarm Data Requested for alarm ' + str(self.id)
        logging.log(20, dat)
        return {'title': self.title, 'content': self.content, 'news': self.news,
                'weather': self.weather, 'id': self.id, 'priority': self.priority, 'date_time': self.date_time}

    def ring(self):
        """
        Gathers the up to date information about covid data, and the news and weather if needed
        to create a well spoken string which will be spoken by pyttsx3 to ring the alarm.
        :return: None
        """
        # create the base of the message
        msg = 'its ' + self.date_time[1] + ' and your reminder is ' + self.title.split(':')[0]

        # add any extra information to the message if required
        # add news information if required
        if self.news == 1:
            news = get_news(1, [], 0)[0]
            msg = msg + '. ' + news['title']

            # add even more information is required
            if news['depth'] == 1:
                msg = msg + '. ' + news['content']

        # add weather information if required
        if self.weather == 1:
            msg = msg + '. ' + get_weather()

        # add covid data to the message
        msg = msg + '. ' + get_covid()

        # speak the message using pyttsx3 - if pyttsx3 is busy, attempt every 5 seconds until
        # the alarm can be spoken.
        done = False
        while not done:
            try:
                pyttsx3.speak(msg)
                done = True
            except RuntimeError:
                # pyttsx3 is already in use, wait for 5 seconds
                dat = 'TTS for Alarm Instance ' + str(self.id) + ' Collision - Waiting(5 Seconds)'
                logging.log(30, dat)
                time.sleep(5)
            except KeyError:
                # pyttsx3 is already in use, wait for 5 seconds
                dat = 'TTS for Alarm Instance ' + str(self.id) + ' Collision - Waiting(5 Seconds)'
                logging.log(30, dat)
                time.sleep(5)
        dat = 'Alarm Instance ' + str(self.id) + ' Has finished ringing'
        logging.log(20, dat)

    def get_seconds(self):
        """
        get_seconds takes the time and date of when the alarm is due to go off and the
        current time and date, to calculate the number of seconds until the alarm is due to ring.
        This integer is then returned so the alarm can be scheduled.
        :return: int
        """
        # get the date and time out of the alarm and turn it into a datetime object
        alarm_data = self.get_data()
        alarm_date = datetime(int(alarm_data['date_time'][0].split('-')[0]),
                              int(alarm_data['date_time'][0].split('-')[1]),
                              int(alarm_data['date_time'][0].split('-')[2]),
                              int(alarm_data['date_time'][1].split(':')[0]),
                              int(alarm_data['date_time'][1].split(':')[1]))
        dat = 'Seconds until Alarm Instance ' + str(self.id) + ' is due has been Returned'
        logging.log(20, dat)
        # return the seconds difference between the 2 times.
        return int((alarm_date - datetime.now()).total_seconds())

    def __del__(self):
        """
        the  __del__ function is run when the alarm is deleted, and is used to log this event
        """
        dat = ' Alarm Instance ' + str(self.id) + ' Has been Deleted'
        logging.log(20, dat)

