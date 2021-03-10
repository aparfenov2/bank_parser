import csv,re, datetime
import pandas as pd
from tabulate import tabulate
from collections import namedtuple, defaultdict
import matplotlib.pyplot as plt
import numpy as np
import argparse

from utils import read_transactions

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_file')
    parser.add_argument('--out_file', default="plot.png")
    parser.add_argument('--end_balance', default=0)

    args = parser.parse_args()

    transactions = read_transactions(args.csv_file)


    df = pd.DataFrame.from_records(transactions, columns=rec_t._fields)
    df = df.sort_values('date')

    print("start_date", df['date'].min())
    print("end_date", df['date'].max())

    df['year'] = df.apply(lambda row: row['date'].year, axis=1)
    df['week'] = df.apply(lambda row: row['date'].isocalendar()[1], axis=1)
    df['sec'] = df.apply(lambda row: row['date'].timestamp(), axis=1)
    by_week = df.groupby(['year', 'week']) #['amount_byn'].sum()

    end_balance = float(args.end_balance)
    df['balance'] = df['amount_byn'].cumsum()    
    to_add = end_balance - df.iloc[-1]['balance']
    df['balance'] += to_add

    # plt.plot(df['balance'].to_numpy())
    # plt.show()

    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df)

    weeks_total = len(by_week)
    X = np.arange(weeks_total)
    width = 1

    categories = list(df.groupby('category').groups.keys())
    cat_ids    = {cat : i for i, cat in enumerate(categories)}
    # cat_offsets = np.linspace(-width/2, +width/2, len(categories))
    # cat_offsets = {categories[i] : cat_offsets[i] for i in range(len(categories))}

    start_dates = []

    cat_sums_by_week = defaultdict(lambda: [0]*weeks_total) # category : list
    for i, (_week, grp) in enumerate(by_week):
        start_date = grp['date'].min().strftime("%d.%m")
        # print(_week)
        start_dates.append(start_date)
        by_cat = grp.groupby(['category'])['amount_byn'].sum().to_dict()
        for cat, _sum in by_cat.items():
            cat_sums_by_week[cat][i] = _sum

    # Start plt
    fig, ax = plt.subplots(ncols=2, figsize=(25, 25), gridspec_kw={'width_ratios': [10, 1]})
    ax3 = ax[1]
    ax = ax[0]
    bottoms_pos = [0]*weeks_total
    bottoms_neg = [0]*weeks_total
    for cat, _sums in cat_sums_by_week.items():
        if max(_sums) > 0:
            bottoms = bottoms_pos
            # print(cat, bottoms, _sums)
        else:
            bottoms = bottoms_neg
        rects = ax.bar(X-width/2, _sums, width, bottom=bottoms, label=f"{cat_ids[cat]}. {cat}")
        for rect in rects:
            rect.category = cat
        for week in range(len(_sums)):
            bottoms[week] += _sums[week]

    def print_ids(ax):
        for p in ax.patches:
            width, height = p.get_width(), p.get_height()
            x, y = p.get_xy()
            if abs(height) < 20:
                continue 
            ax.text(x+width/2, 
                    y+height/2, 
                    f'{cat_ids[p.category]}:{abs(height):.0f}', 
                    horizontalalignment='center', 
                    verticalalignment='center')
    print_ids(ax)

    ax.set_ylabel('BYN')
    ax.set_title('Expendables by week by category')
    ax.set_xticks(X)
    ax.set_xticklabels(start_dates, rotation='vertical')
    ax.grid()

    handles, labels = ax.get_legend_handles_labels()
    # sort both labels and handles by labels
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    ax.legend(handles, labels)


    ax2 = ax.twiny()
    ax2.plot(df['sec'].to_numpy(), df['balance'].to_numpy())
    # ax2.set_xticks(range(len(df)))
    # ax2.set_xticklabels(start_dates, rotation='vertical')


    # Summary
    by_cat = df.groupby(['category'])['amount_byn'].sum().to_dict()
    bottoms_pos = [0]
    bottoms_neg = [0]
    for cat, _sums in by_cat.items():
        if _sums > 0:
            bottoms = bottoms_pos
        else:
            bottoms = bottoms_neg
        rects = ax3.bar(width/2, _sums, width, bottom=bottoms, label=f"{cat_ids[cat]}. {cat}")
        for rect in rects:
            rect.category = cat
            bottoms[0] += _sums
    print_ids(ax3)
    # plt.show()
    plt.savefig(args.out_file)

# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#     print(by_week)
