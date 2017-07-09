#! /usr/bin/python3.5

#Sanitize names in the owner field of the property table of LR.db

import re
import sqlite3

#connect to db
conn = sqlite3.connect('LR.db')
c = conn.cursor()
print('connected')
#GID is the only unique, non-null variable
in_list = c.execute('SELECT gid, owner FROM property')

print('in_list assigned')
#container for query results
out_list = []
counter = 0
#Iterate rows from query, REGEX sub, append tuple to out_list
for row in in_list.fetchall():
    a,b = row
    b_original = b
    b = re.sub(r'\sAND\s',' & ',b)
    b = re.sub(r'/',' & ',b)
    b = re.sub(r'[\s]+',' ',b)
    b = re.sub(r'\.',' ',b)
    b = re.sub(r'(^TR(?=\s))|((?<=\s)TR$)','TRUST',b)
    b = re.sub(r'(?<=\s)BAPT(?=\s)','BAPTIST',b)
    b = re.sub(r'(?<=\s)METH(?=\s)','METHODIST',b)
    b = re.sub(r'(?<=\s)CH$','CHURCH',b)
    if b != b_original:
        out_list.append((b,a))
    else:
        continue
    if counter % 25 == 0:
        print('ROW %s COMPLETE' % counter)
    counter += 1

#repopulate our table
print('REGEX loop complete. Updating table')
c.executemany('UPDATE property SET owner=? WHERE gid=?',out_list)
print('>\n>\n> CLOSING!')
conn.commit()
conn.close()

quit()
