#!/usr/bin/python

__author__ = 'xtotdam'

import os
import pickle
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime
from sys import stdout, argv
try:
    from xtermcolor import colorize
except ImportError:
    def colorize(s, ansi):
        return s

dbfile = 'steam_db.pkl'
showmoves = False
nowrite = False
salesonly = False


def get_db():
    try:
        db = open(dbfile, 'rb')
        records = pickle.load(db)
    except (IOError, EOFError):
        records = []
    return records


def push_to_db(record):
    records = get_db()

    db = open(dbfile, 'wb')
    records.append(record)
    pickle.dump(records, db)


def clear_last_records(n=1):
    records = get_db()
    print len(records), n

    db = open(dbfile, 'wb')
    for i in range(n):
        try:
            del records[-1]
        except IndexError:
            print 'Cannot delete last record: db seems to be empty'

    print len(records)
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
        if price:
            price = float(price.replace(',', '.'))
        else:
            price = None

        try:
            discount = soup.findAll(
                'div', attrs={'class': 'discount_pct'})[0].string
            discount = discount.strip().split(' ')[0][1:-1]
            discount = float(discount.replace(',', '.'))

            rr = requests.get('http://store.steampowered.com/app/' + str(gameId))
            dsoup = BeautifulSoup(rr.text)
            countdown = dsoup.findAll('p', attrs={'class': 'game_purchase_discount_countdown'})[0].string
        except IndexError:
            discount = 0.
            countdown = ''           

        try:
            sale = soup.findAll(
                'div', attrs={'class': 'discount_final_price'})[0].string
            sale = sale.strip().split(' ')[0]
            sale = float(sale.replace(',', '.'))
        except IndexError:
            sale = price

        record[name] = {'num': num, 'id': gameId, 'price': price,
                        'discount': discount, 'sale': sale, 'countdown': countdown}

    return record


def colored_change(old, new, unit='', inverse=False):
    condition = old > new
    if inverse: condition = not condition
    if condition:
        return colorize(str(old) + unit, ansi=9) + ' -> ' + colorize(str(new) + unit, ansi=2)
    else:
        return colorize(str(old) + unit, ansi=2) + ' -> ' + colorize(str(new) + unit, ansi=9)


def print_diff(old, new, stream=stdout, offset=25, showmoves=False, salesonly=False):
    oldk = set(old.keys())
    newk = set(new.keys())

    if not salesonly:
        stream.write(colorize('From ' + str(datetime.fromtimestamp(old['date'])) +
                     ' to ' + str(datetime.fromtimestamp(new['date'])) + '\n', ansi=12))

        adds = newk - oldk
        if adds:
            stream.write(colorize('Games added:\n', ansi=11))
            for item in adds:
                stream.write(item.rjust(offset) + '\n')

        removes = oldk - newk
        if removes:
            stream.write(colorize('Games removed:\n', ansi=11))
            for item in removes:
                stream.write(item.rjust(offset) + '\n')
    else:
        stream.write(colorize(str(datetime.fromtimestamp(new['date'])) + '\n', ansi=12))

    inboth = oldk & newk - set(['date'])
    moves, price_changes, discount_changes, sales = [], [], [], []

    for item in inboth:
        if old[item]['num'] != new[item]['num']:
            moves.append((item, old[item]['num'], new[item]['num']))

        if old[item]['price'] != new[item]['price']:
            price_changes.append(
                (item, old[item]['price'], new[item]['price']))

        if old[item]['discount'] != new[item]['discount']:
            discount_changes.append(
                (item, old[item]['discount'], new[item]['discount'], new[item]['countdown']))

        if new[item]['discount']:
            sales.append((item, new[item]['discount'], new[item]['price'],
                         new[item]['sale'], new[item]['countdown']))

    if not salesonly:
        if showmoves:
            if moves:
                stream.write(colorize('Games moved:\n', ansi=11))
                for item in moves:
                    stream.write(
                        item[0].rjust(offset) + ':  ' + str(item[1]) + ' -> ' + str(item[2]) + '\n')

        if price_changes:
            stream.write(colorize('Price changes:\n', ansi=11))
            for item in price_changes:
                stream.write(
                    item[0].rjust(offset) + ':  ' + colored_change(item[1], item[2]) + '\n')

        if discount_changes:
            stream.write(colorize('Discount changes:\n', ansi=11))
            for item in discount_changes:
                stream.write(item[0].rjust(offset) + ':  ' +
                             colored_change(item[1], item[2], unit='%', inverse=True) + '  ' + item[3] + '\n')

    if sales:
        stream.write(colorize('Sales right now:\n', ansi=11))
        for item in sales:
            stream.write(item[0].rjust(offset) + ':  ' + str(item[1]) + 
                         '%  (' + colored_change(item[2], item[3]) + ')  ' + item[4] + '\n')


if __name__ == '__main__':

    if '--moves' in argv: showmoves = True
    if '--nowrite' in argv: nowrite = True
    if '--salesonly' in argv: salesonly = True
    if '--deletelast' in argv: 
        clear_last_records(n=1)
        print 'Cleared last record'
        exit()
    if '--help' in argv:
        print 'Usage: [--moves | --nowrite | --salesonly | --deletelast | --help]'
        exit()

    if os.path.exists('account.txt'):
        with open('account.txt', 'r') as f:
            account_name = f.readline().strip()
    else:
        account_name = raw_input('Input your SteamCommunity account name: ')

    records = get_db()
    try:
        old_record = records[-1]
    except IndexError:
        print len(records)
        print 'Database contains only one record. It is too early to compare anything.'
        exit()

    new_record = get_data_from_steam(account_name)
    if not nowrite:
        push_to_db(new_record)

    maxLen = max([len(x) for x in new_record.keys()])
    if maxLen < 25:
        maxLen = 25
    else:
        maxLen += 10

    print_diff(old_record, new_record, offset=maxLen, showmoves=showmoves, salesonly=salesonly)
