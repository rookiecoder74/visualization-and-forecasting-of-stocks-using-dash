import pandas as pd
import datetime
from datetime import timedelta

end_date = datetime.date.today()
start_date = end_date - timedelta(days=5)

dat = pd.date_range(start=start_date, end=end_date, freq='B')

header_written = False

for d in dat:
    dmy = d.strftime('%d%m%Y')
    url1 = 'https://archives.nseindia.com/content/nsccl/fao_participant_oi_' + dmy + '.csv'
    data1 = pd.read_csv(url1, skiprows=1)
    data1.insert(0, 'Date', d)
    data1.columns = [c.strip() for c in data1.columns.values.tolist()]
    data1 = data1.iloc[:, :6]

    if header_written:
        data1.to_csv('open.csv', index=False, mode='a', header=False)
    else:
       data1.to_csv('open.csv', index=False, mode='a', header=True)
       header_written = True

print('done')

