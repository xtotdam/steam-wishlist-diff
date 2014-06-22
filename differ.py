from os import listdir, getcwd

try:
    from difflib import context_diff
except ImportError:
    print 'fatal: can\'t import difflib module. Is it installed?'
    exit(21)
from sys import stdout

fl = []

for item in listdir(getcwd()):
    if item[-4:] == 'spdf':
        fl.append(item)

f1 = fl[-2]
f2 = fl[-1]

s1 = open(f1, 'r').readlines()
s2 = open(f2, 'r').readlines()

d1 = '{}-{}-{}, {}:{}'.format(f1[4:6], f1[2:4], f1[:2], f1[6:8], f1[8:10])
d2 = '{}-{}-{}, {}:{}'.format(f2[4:6], f2[2:4], f2[:2], f2[6:8], f2[8:10])

stdout.write('From ' + d1 + ' to ' + d2 + ' there were following changes:\n\n')
diff = context_diff(s1, s2, fromfile=f1, tofile=f2, n=0)

for line in diff:
    stdout.write(line)

stdout.write('If nothing there, no price changes occurred\n')

raw_input()