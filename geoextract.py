#! /usr/bin/python3

import re
import sqlite3
import pdb

con = sqlite3.connect('LR.db')
c = con.cursor()

c.execute('CREATE TABLE IF NOT EXISTS geoloc (gid INTEGER, lat REAL, lon REAL)')

data = list()

#pdb.set_trace()

with open('GeoStor/output.json','r') as infile:
    for i,line in enumerate(infile):
        try:
            re_gid = re.search('(?<=gid\":)[\d]+(?=,)',line)
            gid = re_gid.group(0)
        except:
            print('GID NOT FOUND ON LINE %d' % (i+1))
            continue
        try:
            re_coord = re.search('(?<=coordinates\":\[\[).*(?=\]\])',line)
            coords = re_coord.group(0)
        except:
            print('COORDINATES NOT FOUND ON LINE %d' % (i+1))
            continue
        coord_list = coords.split('],[')
        coord_list = [x.strip('[]') for x in coord_list]
        lat_lon = [x.split(',') for x in coord_list]
        lat_lon = [[float(x) for x in y] for y in lat_lon]
        lat = sum([i[1] for i in lat_lon])/len(lat_lon)
        lon = sum([i[0] for i in lat_lon])/len(lat_lon)
        data.append((gid,lat,lon))

c.executemany('INSERT INTO geoloc VALUES (?,?,?)',data)
con.commit()
con.close()
quit()
        
