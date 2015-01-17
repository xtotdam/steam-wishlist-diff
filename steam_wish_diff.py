__author__ = 'xtotdam'

import os
import pickle
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime
from sys import stdout
try:
    from xtermcolor import colorize
except ImportError:
    def colorize(s, arg):
        return s

dbfile = 'steam_db.pkl'


def get_db():
    try:
        db = open(dbfile, 'rb')
        records = pickle.load(db)
    except (IOError, EOFError):
        records = []
    return records


def push_to_db(record):
    try:
        db = open(dbfile, 'rb')
        records = pickle.load(db)
    except (IOError, EOFError):
        records = []

    db = open(dbfile, 'wb')
    records.append(record)
    pickle.dump(records, db)


def get_data_from_steam(account_name):
    r = requests.get(
        'http://steamcommunity.com/id/' + account_name + '/wishlist')
    soup = BeautifulSoup(r.text)
    rowDivs = soup.body.findAll('div', attrs={'class': 'wishlistRow '})

    record = {}
    record['date'] = time.mktime(datetime.now().timetuple())

    for item in rowDivs:
        soup = BeautifulSoup(str(item))

        gameId = item.get('id')[5:]
        gameId = int(gameId)

        num = soup.findAll(
            'div', attrs={'class': 'wishlist_rank_ro'})[0].string
        num = int(num)

        name = soup.findAll('h4')[0].string
        name = ''.join([i if ord(i) < 128 else '_' for i in name])

        try:
            price = soup.findAll('div', attrs={'class': 'price'})[0].string
        except IndexError:
            price = soup.findAll(
                'div', attrs={'class': 'discount_original_price'})[0].string
        price = price.strip().split(' ')[0]
        price = int(price)

        try:
            discount = soup.findAll(
                'div', attrs={'class': 'discount_pct'})[0].string
            discount = discount.strip().split(' ')[0][1:-1]
            discount = int(discount)
        except IndexError:
            discount = 0

        try:
            sale = soup.findAll(
                'div', attrs={'class': 'discount_final_price'})[0].string
            sale = sale.strip().split(' ')[0]
            sale = int(sale)
        except IndexError:
            sale = price

        record[name] = {'num': num, 'id': gameId,
                        'price': price, 'discount': discount, 'sale': sale}

    return record


def colored_change(old, new, unit=''):
    if old > new:
        return colorize(str(old) + unit, ansi=1) + ' -> ' + colorize(str(new) + unit, ansi=2)
    else:
        return colorize(str(old) + unit, ansi=2) + ' -> ' + colorize(str(new) + unit, ansi=1)


def print_diff(old, new, stream=stdout, offset=25):
    oldk = set(old.keys())
    newk = set(new.keys())

    stream.write('From ' + str(datetime.fromtimestamp(old['date'])) +
                 ' to ' + str(datetime.fromtimestamp(new['date'])) + '\n')

    stream.write('Games added:\n')
    for item in newk - oldk:
        stream.write(item.rjust(offset) + '\n')

    stream.write('Games removed:\n')
    for item in oldk - newk:
        stream.write(item.rjust(offset) + '\n')

    inboth = oldk & newk - set(['date'])
    moves, price_changes, discount_changes = [], [], []

    for item in inboth:
        if old[item]['num'] != new[item]['num']:
            moves.append((item, old[item]['num'], new[item]['num']))

        if old[item]['price'] != new[item]['price']:
            price_changes.append(
                (item, old[item]['price'], new[item]['price']))

        if old[item]['discount'] != new[item]['discount']:
            discount_changes.append(
                (item, old[item]['discount'], new[item]['discount']))

    stream.write('Games moved:\n')
    for item in moves:
        stream.write(
            item[0].rjust(offset) + ':  ' + str(item[1]) + ' -> ' + str(item[2]) + '\n')

    stream.write('Price changes:\n')
    for item in price_changes:
        stream.write(
            item[0].rjust(offset) + ':  ' + colored_change(item[1], item[2]) + '\n')

    stream.write('Discount changes:\n')
    for item in discount_changes:
        stream.write(item[0].rjust(offset) + ':  ' +
                     colored_change(item[1], item[2], unit='%') + '\n')

if __name__ == '__main__':

    if os.path.exists('account.txt'):
        with open('account.txt', 'r') as f:
            account_name = f.readline().strip()
    else:
        account_name = raw_input('Input your SteamCommunity account name: ')

    record = get_data_from_steam(account_name)
    push_to_db(record)

    try:
        old, new = get_db()[-2:]
        print_diff(old, new)
    except ValueError:
        print 'Database contains only one record. It is too early to compare anything.'

    raw_input('___________________\nPress Enter to exit\n')
