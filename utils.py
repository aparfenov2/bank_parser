import csv,re, datetime
from collections import namedtuple

rec_t = namedtuple('rec_t', ['date', 'op', 'amount', 'currency', 'amount_byn', 'category'])

def read_transactions(filename):
    transactions = []
    # Дата транзакции;Операция;Сумма;Валюта;Дата операции по счету;Комиссия/Money-back;Обороты по счету;Цифровая карта;Категория операции;

    with open(filename, 'r', encoding="windows-1251") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            # ret = re.match(r'Операции по.*?(\d+)', row[0]):
            if len(row) < 10:
                # print(row)
                continue
            ret = re.match(r'(\d\d)\.(\d\d)\.(\d\d\d\d) (\d\d)\:(\d\d)\:(\d\d)', row[0])
            if ret:
                # print(len(row))
                tstamp = datetime.datetime.strptime(row[0], '%d.%m.%Y %H:%M:%S')
                op = row[1]
                amount = float(row[2].replace(',','.').replace(' ',''))
                currency = row[3]
                amount_byn = float(row[-4].replace(',','.').replace(' ',''))
                category = row[-2]
                if len(category.strip()) == 0:
                    category = op
                transactions.append(rec_t(tstamp, op, amount, currency, amount_byn, category))

    return transactions
