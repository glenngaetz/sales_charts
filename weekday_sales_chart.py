import sys
import requests
import lxml.html as lh
import pandas as pd
import statistics
from datetime import date
import getpass
import calendar
import matplotlib.pyplot as plt

import pprint


pp = pprint.PrettyPrinter(indent=4)

try: 
    start_date = sys.argv[1]
    end_date = sys.argv[2]
except IndexError:
    start_date = '2021-01-01'
    end_date = date.today().strftime('%Y-%m-%d')

sales = {
    'Monday': [],
    'Tuesday': [],
    'Wednesday': [],
    'Thursday': [],
    'Friday': [],
    'Saturday': [],
    'Sunday': []
}

password = getpass.getpass()

payload = {
    "name": "Glenn",
    "pass": password,
    "form_build_id": None,
    "form_id": "user_login"
}

session_requests = requests.session()

login_url = 'https://niceshoes.ca/user/login'

result = session_requests.get(login_url)

tree = lh.fromstring(result.text)

payload['form_build_id'] = list(set(tree.xpath("//input[@name='form_build_id']/@value")))[0]

result = session_requests.post(
    login_url,
    data = payload,
    headers = dict(referer=login_url)
)

for day in pd.date_range(start_date, end_date):
    day_name = calendar.day_name[calendar.weekday(day.year, day.month, day.day)]    

    url = f'https://niceshoes.ca/admin/commerce/reports/sales-range?start_date={day}&end_date={day}&include_order_detail=0&method_totals=0&channel_totals=1&daily_totals=0&period_totals_type=none&quarterly_totals=0'

    page = session_requests.get(
        url,
        headers = dict(referer = url)
    )


    doc = lh.fromstring(page.content)

    rows = doc.xpath('//tbody/tr')

    try: 
        for row in rows:
            if 'In-Store Total' in row.text_content():
                for k, d in enumerate(row.iterchildren()):
                    if k != 4:
                        continue

                    value = d.text_content();

                    sales[day_name].append(float(d.text_content().replace('$', '').replace(',', '')))
    except IndexError:
        pass
        
print('sales:')
pp.pprint(sales)

for day in calendar.day_name:
    for value in sales[day]:
        plt.plot(day, value, 'ro')

    try:
        avg = statistics.mean(sales[day])

        plt.plot(day, avg, 'bo')
    except statistics.StatisticsError:
        pass

plt.show()
