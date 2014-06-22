try:
    import urllib2
except ImportError:
    print 'fatal: can\'t import urllib2 module. Is it installed?'
    exit(11)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print 'fatal: can\'t import bs4 (BeautifulSoup) module. Is it installed?'
    exit(12)

from time import strftime, localtime
from sys import argv

if len(argv) > 1:
    account_name = argv[1]
else:
    account_name = raw_input('Input your SteamCommunity account name: ')

page = urllib2.urlopen('http://steamcommunity.com/id/' + account_name + '/wishlist')
soup = BeautifulSoup(page)

x = soup.body.findAll('div', attrs={'class': 'wishlistRowItem'})

cnt = 0
dt = strftime("Timestamp   %d-%m-%y %H-%M", localtime())
fn = strftime("%y%m%d%H%M", localtime())

name = []
discount = []
orig_price = []
final_price = []
max_len = 0

for item in x:
    cnt += 1
    soup = BeautifulSoup(str(item))
    nm = soup.find_all('h4')[0].string
    if len(nm) > max_len:
        max_len = len(nm)

    try:
        dsc = int(soup.find_all('div', attrs={'class': 'discount_pct'})[0].string[1:-1])
    except IndexError:
        dsc = 0

    try:
        op = float(
            soup.find_all('div', attrs={'class': 'discount_original_price'})[0].string.split()[0].replace(',', '.'))
    except IndexError:
        op = float(soup.find_all('div', attrs={'class': 'price'})[0].string.strip().split()[0].replace(',', '.'))

    try:
        fp = float(soup.find_all('div', attrs={'class': 'discount_final_price'})[0].string.split()[0].replace(',', '.'))
    except IndexError:
        fp = op

    name.append(nm)
    discount.append(dsc)
    orig_price.append(op)
    final_price.append(fp)

out = open(fn+'.spdf','w')
# out.write('{}\n'.format(dt))

for i in xrange(len(name)):
    l = len(name[i])
    out.write('{0:02d}  {1}{2}:  {3:7.2f} - {4:02d}% = {5:7.2f}\n'.format(
        i + 1,
        ' ' * (max_len - l + 2),
        name[i],
        orig_price[i],
        discount[i],
        final_price[i]))
out.close()

import differ