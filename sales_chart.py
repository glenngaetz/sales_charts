import sys
import requests
import lxml.html as lh
import getpass
import datetime
import calendar
import matplotlib.pyplot as plt
import pprint


pp = pprint.PrettyPrinter(indent=4)

# get the start year from the command line arguments.
# if it isn't passed, set it to 2016.
try: 
    start_year = int(sys.argv[1])
except IndexError:
    start_year = 2016

# get the end year from the command line arguments.
# if it isn't passed, set it to this year.
try: 
    end_year = int(sys.argv[2])
except IndexError:
    end_year = int(datetime.date.today().strftime('%Y'))

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

result = session_requests.get(login_url)

tree = lh.fromstring(result.text)

payload['form_build_id'] = list(set(tree.xpath("//input[@name='form_build_id']/@value")))[0]

result = session_requests.post(
    login_url,
    data = payload,
    headers = dict(referer=login_url)
)

# prepare the sales dict
sales = {}

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

years = range(start_year, end_year+1)

# get the sales data by scraping the sales report data for each month and year
for year in years:
    sales[year] = {}
    for month, month_name in enumerate(months):
     
        month = month + 1
        sales[year][month] = None
        start = datetime.datetime(year, month, 1).timestamp()
        end = datetime.datetime(year, month, calendar.monthrange(year, month)[1]).timestamp()

        url = f'https://niceshoes.ca/admin/commerce/reports/sales-comparison/ajax/{start}/{end}/{end}/month'

        page = session_requests.get(
            url,
            headers = dict(referer = url)
        )


        doc = lh.fromstring(page.content)

        td_elements = doc.xpath('td')

        for d in td_elements:
            value = d.text_content();
            field = d.attrib.get('id', '')

            try:
                if 'revenue' in field:
                    sales[year][month] = float(d.text_content().replace('$', '').replace(',', ''))
            except ValueError:
                pass
            
print('sales:')
pp.pprint(sales)

# plot the sales data in a chart, one line per year
for year, year_values in sales.items():
    plt.plot(months, [x for y,x in year_values.items()], label = year)

    plt.legend()

plt.show()
