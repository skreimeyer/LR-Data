#!/usr/bin/python3.5

#Looks like you can't just load data one column at at ime for SQLITE,
#so new table it is.

import sqlite3
import re

conn = sqlite3.connect('LRland.db')
c = conn.cursor()

#gid integer, pid text, owner text, own_add text, st_num integer,
#st_dir text, st_name text, st_type text, city text, state text,
#zip integer, code text, assessed_val int, improvement_val int,
#land_val int, acres integer, total_acres REAL

#array for our query and modified values
master = []

#Function to strip excess characters and return integer
def format_int(val):
    match = re.search(r'[\d]+',val)
    try:
        outval = int(match.group(0))
    except:
        outval = 0
    return outval

#Function to strip excess characters and return float
def format_real(val):
    match = re.search(r'[\d]+\.[\d]+',val)
    try:
        outval = float(match.group(0))
    except:
        outval = 0.0
    return outval

c.execute('SELECT * FROM source')

#Iterate and insert tuples into master array. Lot of shit to debug if it fails . . .
for row in c:
    master.append((format_int(row[0]),row[2],row[6],row[7],format_int(row[9]),\
                   row[10],row[11],row[12],row[14],row[15],format_int(row[16]),\
                   row[18],format_int(row[19]),format_int(row[20]),format_int(row[21]),\
                   format_real(row[28])))
print('for loop passed')

#create new table, load data with some dumb looking queries. Probably should divide
#this among multiple tables for the sake of manageability
c.execute('''CREATE TABLE property
(GID INTEGER, PID TEXT, owner TEXT, own_add TEXT, prop_stnum INTEGER, prop_stdir TEXT,
prop_stname TEXT, prop_stype TEXT, city TEXT, state TEXT, zip INTEGER, code TEXT,
assessed INTEGER, improved INTEGER, land_val INTEGER, acres REAL)''')
print('created table')

c.executemany('INSERT INTO property VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', master)
print('SQLite table populated')
conn.commit()
conn.close()
print('no going back now')
quit()
