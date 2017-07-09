#! /usr/bin/python3
 
'''
Pull land valuation data from a SQLite database and save plots of
lognormal histograms
'''
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import json

#load db into a dataframe
conn = sqlite3.connect('LR.db')

df = pd.read_sql('SELECT code, assessed, improved, land_val, acres FROM property',con=conn)

#read json with translations for zoning codes
code_file = open('code_key')
codes = json.load(code_file)
code_file.close()


def gen_histogram(srs,title,subtitle,log_flag):
    #Save a histogram plot to graphs folder.
    plt.figure()
    try:
        title_string = codes[title]+' - '+subtitle
    except:
        title_string = title+'-'+subtitle
    if log_flag:
        #bin sizes need logarithmic distribution for legibility
        binvar = np.logspace(0.0,np.log10(srs.max()),num=100)
    else:
        binvar = 10
    srs.plot.hist(bins=binvar,title=title_string,logx=log_flag)
    filename = 'graphs/hist/%s-%s.png' % (title,subtitle)
    plt.savefig(filename)
    plt.close()

#Create series objects of calculated values. This is done for
#legibility rather than efficiency
appraised = pd.Series(df['improved']+df['land_val'])
per_acre = pd.Series(appraised / df['acres'])
tax_ratio = pd.Series(appraised / df['assessed'])

subtitles = ['appraised','per acre value','tax ratio']

#generate histograms for all data

srs_list = [appraised, per_acre, tax_ratio]

#Loop through our series for the entire dataset
for i in range(3):
    gen_histogram(srs_list[i],'general',subtitles[i],True)

#data frame of calculated values

df2 = pd.DataFrame({'code':df['code'],'appraised':appraised,'per acre value':per_acre,'tax ratio':tax_ratio})
grouped = df2.groupby('code')
for code in codes:
    for sub in subtitles:
        #appraised / assessed values shouldn't be plotted to log scale
        if 'tax ratio' in sub:
            flag = False
        else:
            flag = True
        try:
            series = grouped.get_group(code)[sub]
            gen_histogram(series,code,sub,flag)
        except:
            continue


conn.close()
quit()
