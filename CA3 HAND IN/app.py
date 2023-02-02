"""
app.py is the main python file used the power the flask application.
It is responsible for managing inputs and outputs to the HTML template as well as
controlling the use of the 'apicalls' file, creation of alarm instances,
and scheduling of these alarms on multiple threads.
Function:
    redirect_user() -> redirect
    display_page() -> render_template
    set_alarm(request) -> redirect
    ring_alarm(Alarm)
    delete_alarm(alarm, fin_ringing, scheduled) -> redirect
    refresh_notifs -> list


Misc variables:
    current_notifs: list
    deleted_notifs: list
    alarm_list: list
    sched_dict: dict
    scheduler: Sched Object
    app: Flask Application
    s: Sched Object
"""

import time
import sched
import threading
import logging
import json
from flask import Flask, request, render_template, redirect
from apicalls import get_covid, get_news, get_weather
from alarm import Alarm

# This section is used to set up the format of the logging file as
# well as the severity of 'urllib3' and 'comtypes'
# events to prevent overcrowding the log file.
logging.basicConfig(filename='sys.log', level=0, format='(%(asctime)s):%(name)s:'
                                                        '%(levelname)s:%(message)s')
logging.getLogger('urllib3').setLevel(40)
logging.getLogger('comtypes').setLevel(40)

# The section below is used to initialise many of the global
# variables and to start the flask application
current_notifs = []
deleted_notifs = []
alarm_list = []
sched_dict = {}

# starting the scheduler
scheduler = sched.scheduler(time.time, time.sleep)

# starting the flask application
app = Flask(__name__)
logging.log(20, '**Project Started**')


@app.route('/')
def redirect_user():
    """
    redirects the user to '/index' url
    :return: redirect: sends the user to the correct required page
    """
    return redirect('/index')


@app.route('/index')
def display_page() -> render_template:
    """
    Display page manages all requests pointing to the /index page for the flask application.
    The main role is to check if alarms need to be created or deleted, or if notifications
    need deleting and to refresh notifications in order to pass up to date info into the template.
    It returns a render template function which is responsible for displaying the page

    :returns render_template: Renders a web pade using the method from flask
    :returns redirect: Redirects the user to a defined web page using the method from flask
    """
    # update the list of notifications for up to date information
    current_notifs = []
    current_notifs += refresh_notifs()

    # check if the request contains alarm data
    if request.args.get('alarm') is not None:
        # alarm has to be set, calls the set_alarm function and passes
        # in all the data from the request
        logging.log(20, 'Page requires an alarm to be set')
        set_alarm(request)

        # redirects the user back to the main page at the end to continue using the app
        return redirect('/index')

    # check ig the request has an alarm_item(this is sent in when an alarm is to be deleted)
    if request.args.get('alarm_item') is not None:
        # alarm has to be deleted, calls the delete_alarm function and passes in the alarm item
        # as well as 'False' which specifies that the alarm has not gone off yet
        print(request.args.get('alarm_item').split(':')[1])
        logging.log(20, 'Page requires an alarm to be deleted')
        id = request.args.get('alarm_item').split(':')[1]
        for alarm in alarm_list:
            if alarm.get_data()['id'] == id:
                print(alarm)
                delete_alarm(str(alarm), False, True)

        # redirects the user back to the main page at the end to continue using the app
        return redirect('/index')

    if request.args.get('notif') is not None:
        # notification has to be deleted, adds the notification to the deleted_notifs
        # array so its isn't used again. As the user deleted it, it is assumed
        # they dont want to see it next time the page is loaded.
        logging.log(20, 'Page requires an notification to be deleted')
        title = request.args.get('notif')
        for element in current_notifs:
            if element['title'] == title:
                index = element['index']
        deleted_notifs.append(current_notifs[index])
        del current_notifs[index]

        # redirects the user back to the main page at the end to continue using the app
        return redirect('/index')
    # if no actions are to be taken, then the page(template) can be rendered, sending in the
    # list of alarms, list of notification and the image that will be used by the template.
    return render_template('template.html', alarms=alarm_list,
                           notifications=current_notifs, image='covid.svg')


def set_alarm(req: request) -> redirect:
    """
    set_alarm takes in the request send by the HTML file when the form was
    submitted and is responsible for
    creating and scheduling the alarm.
    It returns a redirect to the index page so the user can continue using the application
    :parameter req: A flask request is a data type that contains the data passed in with the URL
               when the request is made
    :returns redirect: Redirects the user to a defined web page using the method from flask
    """
    # take details(alarm time, message and if news or weather are required to be announced)
    # out of the request
    alarm = req.args.get('alarm').split('T')  # gets time and date form the request
    message = req.args.get("two")  # gets the message from the request
    # sets news and weather to 0 by default
    news = 0
    weather = 0
    # if the request specifies the news is required in the announcement,
    # then the news token is set to 1
    if req.args.get('news') == 'news':
        news = 1
    # if the request specifies the weather is required in the announcement,
    # then the weather token is set to 1
    if req.args.get('weather') == 'weather':
        weather = 1

    # the data above is then used to create an alarm object using the Alarm class
    # defined separately, this alarm is then appended to alarm_list - a list containing all
    # the alarm instances.
    alarm_object = Alarm(message, alarm, news, weather, alarm_list)
    alarm_list.append(alarm_object)

    # the counter for the total number of alarms is incremented

    # check if alarm_object is set for the future
    if alarm_object.get_seconds() < 0:
        # too late to set the alarm, delete it amd specify 'True' as the
        # alarm schedule has not yet been created
        delete_alarm(str(alarm_object), True, False)
        # the user can be redirected to the main page from here as the
        # schedule should not be created
        return redirect('/index')

    # as the time is set for the future, the schedule can be created for
    # the alarm, and therefore the last component of the alarm can be created
    alarm_data = alarm_object.get_data()
    my_sched = s.enter(alarm_object.get_seconds(), alarm_data['priority'],
                       ring_alarm, [alarm_object])
    sched_dict[alarm_data['id']] = my_sched

    # run the schedule for the alarm in a separate thread to ensure it goes
    # off correctly and is uninterrupted and also allows the web page to
    # continue running to other alarms can be created or deleted...
    threading.Thread(target=s.run).start()

    # redirect the user back to the main page to allow the to continue using the application.
    return redirect('/index')


def ring_alarm(alarm: Alarm) -> None:
    """
    The ring_alarm function takes in ana alarm and is responsible for calling its ring() method and
    deleting itonce it has finished rining. As its called from the display_page function, it returns
    None, as the page will be redirected from the delete_alarm function.
    :parameter alarm: the alarm sent in is an instance of an Alarm object
    :returns None: Returns None as the delete_alarm function called from here is
    responsible to redirect the user.
    """
    alarm.ring()
    # true is passed in from here as the alarm has finished ringing
    delete_alarm(str(alarm), True, True)
    return None


def delete_alarm(alarm: str, fin_ringing: bool, scheduled: bool) -> redirect:
    """
    The delete_alarm function makes sure all aspects of the alarm are deleted
    It removes the alarm from alarm_list, and the schedule from the sched_dict
    As well as cancelling the schedule if necessary and deleting the alarm instance.
    The user is then redirected to the /index page to continue using the application
    :parameter alarm: this parameter is the string representation of an alarm object
    :parameter fin_ringing: Boolean used to determine if the alarm in question has finished
               ringing or not
    :parameter scheduled: Boolean used to determine if a shced entry has been made for this alarm
    :returns redirect: Redirects the user to a defined web page using the method from flask
    """

    print(sched_dict)
    print(alarm_list)
    # Looks for the correct alarm in the alarm_list
    for instance in alarm_list:

        if str(instance) == alarm:
            # if it is found, its data is found and it is removed from the list
            alarm_data = instance.get_data()

            # if it has not finished ringing, the schedule needs to be cancelled
            if not fin_ringing:
                logging.log(20, 'Sched for ' + alarm_data['id'] + ' has been deleted')
                s.cancel(sched_dict[alarm_data['id']])

            # if it was scheduled at some point, the event needs to be removed from the sched_dict
            if scheduled:
                sched_dict.pop(alarm_data['id'])
            alarm_list.remove(instance)

            # no more identical alarms can be found,so the for loop can be exited using continue
            continue
    print(sched_dict)
    print(alarm_list)
    # redirect the user back to the main page to allow the to continue using the application.
    return redirect('/index')


def refresh_notifs() -> list:
    """
    Uses the apicalls module to return a list of the latest notifications, and if required the
    weather or covid data. The number of notifications and the decision to add weather and covid
    can be specified in the config file
    :returns list: Returns a list of new notifications that have been updated from live data.
    """
    new_notifs = []
    logging.log(20, 'Notifications being refreshed')

    # get data form the config file
    with open('config.json') as json_file:
        data = json.load(json_file)
        quantity = data['data']['notif_data']['quantity']
        extras = data['data']['notif_data']['extras']

    # If the weather and covid data is wanted on the notification panel, is is done here
    if extras == 1:

        # an addition is set to 2 as there are already 2 notification in the list
        addition = 2

        # the 2 fields are added as notifications
        new_notifs = [{'title': 'Covid Info', 'content': get_covid(), 'index': 0, 'depth': 0},
                      {'title': 'Weather Info', 'content': get_weather(), 'index': 1, 'depth': 0}]
    else:
        # no elements are in the lest
        addition = 0
    # the notifications from the apicalls function are appended to the end of the weather
    # and covid date *if present
    new_notifs += get_news(quantity, deleted_notifs, addition)
    return new_notifs


if __name__ == '__main__':
    app.run()

# the code below is responsible for defining the scheduler and assigning it the
# time and sleep attributes.
s = sched.scheduler(time.time, time.sleep)
s.run()
s.run(blocking=False)

# this will allow us to run the scheduler without it sleeping,
# however this requires the run function to be called intermittently
