#! /usr/bin/env python

'''
Generate hexbin plots of property values to better visualize
property value trends. We need to join on coordinates and also
create plots for different land types
'''

import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.colors as color
import json

#Connect
con = sqlite3.connect('LR.db')

query = '''
    SELECT code, assessed, improved, land_val, acres, lat, lon
    FROM property
    INNER JOIN geoloc ON geoloc.gid = property.GID
    '''

df = pd.read_sql(query, con)
#Create calculated values that we will plot
df['appraised'] = df['improved']+df['land_val']
df['appraised per acre'] = df['appraised']/df['acres']
df['tax rate'] = df['assessed']/df['appraised']

subtitles = ['appraised','appraised per acre','tax rate']

#read json with translations for zoning codes
code_file = open('code_key')
codes = json.load(code_file)
code_file.close()

def gen_hexbin(dataframe, title, subtitle, log_flag):
    plt.figure()
    fig_size = (12,9)
    plt.rcParams["figure.figsize"] = fig_size
    try:
        title_string = codes[title]+' - '+subtitle
    except:
        title_string = title+'-'+subtitle
    if log_flag:
        dataframe.plot.hexbin(x='lon',y='lat',C=subtitle,norm=color.LogNorm(),
                              title=title_string, cmap='inferno')
    else:
        dataframe.plot.hexbin(x='lon',y='lat',C=subtitle,title=title_string,cmap='inferno')
    filename = 'graphs/hexbin/%s.png' % (title_string)
    plt.savefig(filename)
    plt.clf()
    return True

#writing a for-loop with conditions for just three loops seemed unnecessary
gen_hexbin(df,'Total',subtitles[0],True)
gen_hexbin(df,'Total',subtitles[1],True)
gen_hexbin(df,'Total',subtitles[2],False)

#Group our data by zoning code and create a plot for each
grouped = df.groupby('code')
for code in codes:
    for sub in subtitles:
        #appraised / assessed values shouldn't be plotted to log scale
        if 'tax rate' in sub:
            flag = False
        else:
            flag = True
        try:
            new_df = grouped.get_group(code)
            gen_hexbin(new_df,code,sub,flag)
        except:
            continue

    
con.close()
quit()
