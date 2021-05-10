import sys
import requests
import lxml.html as lh
import getpass
import datetime
import calendar
import pandas as pd
import matplotlib.pyplot as plt
import pprint


"""
Script to get raw report data as JSON from 
"""

pp = pprint.PrettyPrinter(indent=4)

# get the start year from the command line arguments.
# if it isn't passed, set it to 2016.
try: 
    start = sys.argv[1]
except IndexError:
    start = f'{datatime.date.today().strftime("%Y")}-01-01'

# get the end year from the command line arguments.
# if it isn't passed, set it to this year.
try: 
    end = sys.argv[2]
except IndexError:
    end = datetime.date.today().strftime('%Y-%m-%d')

# get the site password for login
password = getpass.getpass()

# prepare login data and perform login
payload = {
    "name": "Glenn",
    "pass": password,
    "form_build_id": None,
    "form_id": "user_login"
}

session_requests = requests.session()

login_url = 'https://niceshoes.ca/user/login'

result = session_requests.get(login_url, verify=False)

tree = lh.fromstring(result.text)

payload['form_build_id'] = list(set(tree.xpath("//input[@name='form_build_id']/@value")))[0]

result = session_requests.post(
    login_url,
    data = payload,
    headers = dict(referer=login_url),
    verify=False
)

url = f'https://niceshoes.ca/admin/commerce/reports/data/{start}/{end}/'

result = session_requests.get(
    url,
    headers = dict(referer = url),
    verify=False,
    timeout=None
)

print(f'result: {result}')

data = result.json()['data']

formatted_data = []

for day in pd.date_range(start, end):
    try: 
        for method, method_values in data[day.date().isoformat()].items():
            for channel, channel_values in method_values.items():
                for rev_type, rev_type_values in channel_values.items():
                    for order_id, order_values in rev_type_values.items():
                        #timezone = datetime.timezone(-datetime.timedelta(hours=8))
                        dt = datetime.datetime.fromtimestamp(int(order_values['#meta']['timestamp']))
                        report_values = {
                            'date': day.date().isoformat(),
                            'day_of_week': dt.weekday(),
                            'hour': dt.hour,
                            'channel': channel,
                            'order_id': order_id,
                        }

                        for key in ['order_total', 'revenue', 'subtotal', 'discounts', 'shipping', 'gst_hst', 'pst', 'giftcard_purchase']:
                            try:
                                report_values[key] = int(order_values[key]) / 100
                            except KeyError:
                                report_values[key] = 0
                        formatted_data.append(report_values)
    except KeyError:
        pass

date_total_data = {}

for item in formatted_data:
    try:
        date_total_data[item['date']]
    except KeyError:
        date_total_data[item['date']] = []
        for i in range(0, 24):
            date_total_data[item['date']].append(0)

    try:
        date_total_data[item['date']][item['hour']]
    except IndexError:
        date_total_data[item['date']][item['hour']] = 0

    if 'instore' in item['channel']:
        date_total_data[item['date']][item['hour']] = item['revenue'] + date_total_data[item['date']][item['hour']]

report_data = []
for hour in range(0, 24):
    report_data.append([[],[],[],[],[],[],[]])

for d in pd.date_range(start, end):
    for hour, hdata in enumerate(report_data):
        for day, ddata in enumerate(hdata):
            found = False
            for item_date, item_date_values in date_total_data.items():
                for item_hour, item_hour_value in enumerate(item_date_values):
                    dt = datetime.date(*[int(x) for x in item_date.split('-')])
                    if item_hour == hour and dt.weekday() == day and d.date().isoformat() == item_date:
                        report_data[hour][day].append(float(item_hour_value))
                        found = True
            if found == False:
                report_data[hour][day].append(0.00)

for i, h in enumerate(report_data):
    for j, d in enumerate(h):
        try:
            report_data[i][j] = float(sum(d) / len(d))
        except ZeroDivisionError:
            report_data[i][j] = float(0.00)

 
#pp.pprint(report_data)

idx = [f'{x}:00-{x+1}:00' for x in range(0, 24)]
cols = [x for x in calendar.day_name]

chart_data = pd.DataFrame(report_data, columns=cols, index=idx)

pp.pprint(chart_data)

# plot the sales data in a chart

plt.imshow(chart_data, cmap='Greens', aspect='auto')

plt.colorbar()

plt.xticks(range(len(cols)), chart_data.columns)

plt.yticks(range(len(idx)), chart_data.index)

plt.suptitle(f'Avg Hourly Instore Sales {start} - {end}', fontsize=16)

plt.show()
