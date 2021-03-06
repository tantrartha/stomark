from yahoofinancials import YahooFinancials
import json
from datetime import datetime, timedelta
from prettytable import PrettyTable
import yagmail
import sys


# Input
assets = [  # these IDs are as per YahooFinance website
]
DMA_DAYS = "50"  # last 50 days

with open("assets.txt") as fr:
    for line in list(fr):
        assets.append(line.split('\n')[0])

# -------------------------------------------
yahoo_financials = YahooFinancials(assets)

today = datetime.today()
end = today.strftime("%Y-%m-%d")
start = (today - timedelta(days=int(DMA_DAYS))).strftime("%Y-%m-%d")

stockdata = yahoo_financials.get_historical_price_data(start_date=start, end_date=end, time_interval="daily")

with open('sto.json', 'w') as f:
    json.dump(stockdata, f)


custom_data = {}
for company, cdata in stockdata.items():
    custom_data[company] = {}
    tmp = []
    for daily_stock_data in cdata["prices"]:
        tmp.append(daily_stock_data["close"])
    dma = round(sum(tmp) / len(tmp), 2)
    custom_data[company]["mean"] = dma
    custom_data[company]["Days>DMA" + DMA_DAYS] = len([above_avg for above_avg in tmp if above_avg > custom_data[company]["mean"]])
    custom_data[company]["Last10days>DMA" + DMA_DAYS] = len([above_avg for above_avg in tmp[-10:] if above_avg > custom_data[company]["mean"]])
    custom_data[company]["Today>DMA" + DMA_DAYS] = "✅" if cdata["prices"][-1]["close"] > dma else "❌"


pt = PrettyTable()

pt.field_names = [
    "Company",
    "DMA"+DMA_DAYS,
    "Today>DMA"+DMA_DAYS,
    "Days>DMA"+DMA_DAYS,
    "Last10days>DMA"+DMA_DAYS
]

for name,data in custom_data.items():
    row = [
        name,
        data["mean"],
        data["Today>DMA" + DMA_DAYS],
        data["Days>DMA" + DMA_DAYS],
        data["Last10days>DMA" + DMA_DAYS]
    ]
    pt.add_row(row)

print(pt)

mail_body = '''
{1}
</br>
<h3>Legend:</h3>
<b>Today>DMA</b>       -> Is yesterday's close price greater than last {0} days average close price?
<b>Days>DMA</b>        -> In the last {0} days, number of days the company's close price is greater than last {0} days average close price.
<b>Last10Days>DMA</b>  -> In the last 10 days, number of days the company's close price is greater than last {0} average close price.
'''.format(DMA_DAYS, pt.get_html_string(format=True))

if len(sys.argv) == 3:
    sender = sys.argv[1]
    receiver = sys.argv[2] if ',' not in sys.argv[2] else sys.argv[2].split(',')
    yag = yagmail.SMTP(sender)
    yag.send(to=receiver, subject=end, contents=mail_body)
