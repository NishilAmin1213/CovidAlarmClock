import unittest
import app, apicalls, alarm, json
from datetime import datetime, timedelta


class ProjectTest(unittest.TestCase):

    # Test API Calls
    def test_get_news(self):
        with open('config.json') as json_file:
            data = json.load(json_file)
            quantity = data['data']['notif_data']['quantity']
        result = apicalls.get_news(quantity, [], 0)
        self.assertNotEqual(result, [])

    def test_get_weather(self):
        result = apicalls.get_weather()
        self.assertNotEqual(result, '')

    def test_get_covid(self):
        result = apicalls.get_covid()
        self.assertNotEqual(result, '')

    # Test Alarm Creation and Functionality
    def test_alarm(self):
        # test that a basic alarm can be created without an error
        # time format = ['2020-12-01', '12:59']
        current_time = [str(datetime.now().date()), str(datetime.now().time().strftime('%H:%M'))]
        test_time = [str(datetime.now().date()), str((datetime.now() + timedelta(minutes=2)).time().strftime('%H:%M'))]

        test_alarm = alarm.Alarm('This is a message',
                                 test_time,
                                 0,
                                 0,
                                 0,  # as there are no other alarms, the id is expected to be 0
                                 [])  # as there are no other alarms, there are no coinciding alarms, # hence the
        # priority is expected to be 1

        # test that the data from the above step is accessible correctly via get_data()
        expected_result = {'title': 'This is a message',
                           'content': test_time,
                           'news': 0,
                           'weather': 0,
                           'id': '0',
                           'priority': 1}
        result = test_alarm.get_data()
        self.assertEqual(result['title'], expected_result['title'])
        self.assertEqual(result['content'], expected_result['content'])
        self.assertEqual(result['news'], expected_result['news'])
        self.assertEqual(result['weather'], expected_result['weather'])
        self.assertEqual(result['id'], expected_result['id'])
        self.assertEqual(result['priority'], expected_result['priority'])

        # test that the get_seconds() method is correct (cannot test exactly equal to 120 as
        # some time is taken up running the program which changes every time its run)
        self.assertGreater(test_alarm.get_seconds(), 0)
        self.assertLess(test_alarm.get_seconds(), 120)

    def test_alarm_1(self):
        # test that the ID and Priority of alarms are correctly updated if there are multiple alarms
        test_time = [str(datetime.now().date()), str((datetime.now() + timedelta(minutes=2)).time().strftime('%H:%M'))]
        test_alarm = alarm.Alarm('This is a message',
                                 test_time,
                                 0,
                                 0,
                                 0,  # as there are 0 other alarms, the id is expected to be 0
                                 [])  # priority is expected to be 1

        colliding_alarm = alarm.Alarm('This is a message',
                                      test_time,
                                      1,
                                      1,
                                      1,  # there is already 1 other alarm as passed in, so id expected to be 1
                                      [test_alarm])  # priority is expected to be 2 as the colliding alarm is present
        result = colliding_alarm.get_data()
        # in the alarm list being passed in
        expected_result = {'id': '1',
                           'priority': 2}
        self.assertEqual(result['id'], expected_result['id'])
        self.assertEqual(result['priority'], expected_result['priority'])


# the code below allows us to run the test.py file and unittest to work, as
# opposed to having to enter "python -m unittest test.py" in the terminal
if __name__ == '__main__':
    unittest.main()
