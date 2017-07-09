#!/usr/bin/env python

'''
This script identifies outliers within the Little Rock property database.
For each property inverse distance weighted distributions are determined
for appraised and assessed values. Outliers are identified and owner names
are placed in a report for further analysis. Known registered agents and
officers are queried for companies.
'''

import sqlite3
import json
import pandas as pd
import numpy as np
import pdb
import pickle

###Global variables###

#list of variables we want to test for
test_vars = ['total_val','appraised_per_acre',]
#number of neighbors to analyze
neighbors = 20
#Exponent for inverse distance weighting
power = 2
#set threshold for maximum neighbor distance
max_dist = 0.5 #km
#Z-score threshold for reporting
global_threshold = 6
local_threshold = 4

###Global variables###

#connect
con = sqlite3.connect('LR.db')

#read codes
code_file = open('code_key')
codes = json.load(code_file)
code_file.close()

###Data prep###

query = '''
SELECT owner, prop_stnum, prop_stdir, prop_stname, prop_stype,
code, assessed, improved, land_val, acres, geoloc.lat, geoloc.lon
FROM property INNER JOIN geoloc ON property.gid = geoloc.gid
'''

#Populate pandas dataframe with our query
df = pd.read_sql(query,con)
#close SQLite connection
con.close()
#Calculate total appraised value, appraised value per acre, and
#ratio of assessed to appraised value
df['total_val'] = df['improved']+df['land_val']
#Drop zero values. These are a significant source of noise.
df = df[df['total_val'] > 0]
df['appraised_per_acre'] = df['total_val']/df['acres']

#df['tax_ratio'] = df['assessed']/df['total_val']
######################################################################
#The ratio of assessed to appraised values is no longer measured. Doing so
#created a huge number of false positives from rounding errors and there
#are only a about 10 outliers in the entire dataset. Analyzing this rate
#should be handled in a separate script. Rant complete.
######################################################################
#We will need aggregate stats for each later
#Because the values are lognormally distributed, we need
#to scale our aggregate statistics to make them useful
global_stats = dict()
for var in df.columns: 
    #Create empy dictionary object to store stats later
    global_stats[var] = dict()
    try:
        global_stats[var]['mean'] = np.log10(df[var]).mean()
        global_stats[var]['std'] = np.log10(df[var]).std()
    except:
        print('Summary stats not generated for column %s' % var)
        continue

###Data prep###

def get_code_group(dataframe, code):
    '''
    Take a subset of our dataframe based on zoning code.
    '''
    code_df = dataframe[dataframe['code']==code]
    return code_df

def find_neighbors(frame, row_index):
    '''
    This method takes a pandas dataframe and an index value as arguments
    and returns a seriess of the closest neighbors to our target
    '''
##    pdb.set_trace()
    #get coordinates
    lat = frame['lat'][row_index]
    lon = frame['lon'][row_index]
    #calculate distance between coordinates
    distance = haversine(lat,frame['lat'],lon,frame['lon'])
    #Exclude values greater than our search radius
    distance = distance[distance < max_dist]
    #Sort_values defaults to ascending order
    distance = distance.sort_values()
    #pandas series preserve index values from the dataframe which is
    #what we really want. Exclude the first result, which is the target
    #coordinate
    dist_neighbors = distance[1:neighbors]
    #pandas handles out of index errors for slicing! Lucky!
    return dist_neighbors

def haversine(lat1,lat2,lon1,lon2):
    '''
    This function calculates the haversine distance between coordinates.
    Coordinates should be passed as a list of tuples. This isn't strictly
    necessary, but is technically more accurate than a flat projection.
    '''
    #convert to radians, the pinnacle of angular representation.
    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    lon1 = np.radians(lon1)
    lon2 = np.radians(lon2)
    #Radius of Earth
    radius = 6378 #km
    #The following lines are components of haversine broken out
    #to make the distance formula more legible
    a = np.sin((lat2-lat1)/2)**2
    b = np.sin((lon2-lon1)/2)**2
    c = np.cos(lat1)*np.cos(lat2)
    distance = 2*radius*np.arcsin(np.sqrt(a+c*b))
    return distance

def gen_local_stats(frame, dist_neighbors, test_var):
    '''
    Generate inverse distance weighted statistics for a neighbor group.
    Return Z scores for target property's distance from these means.
    '''
    #Debugging break in case of indexing errors
##    pdb.set_trace()
    weights = 1/dist_neighbors**power
    indices = dist_neighbors.index.tolist()
    #New dataframes keep their row names, but not indices
    #We need to reference our original dataframe
    tmp_frame = df[test_var][indices]
    mean = np.sum(weights*tmp_frame)/np.sum(weights)
    stdev = np.std(tmp_frame)

    ##########################################################
    #I'm leaving these comments as a cautionary tale. Distance weighting standard
    #deviation will make your std score way too narrow. Take heed.
    ##########################################################
    #Standard deviation should be distance weighted, so we roll our own
    #sqr_diff = (tmp_frame-mean)**2
    #stdev = np.sqrt(np.sum(sqr_diff*weights)/np.sum(weights)/len(tmp_frame))
    
    return mean,stdev

#Driver
output = dict()
for n,code in enumerate(codes):
    print('-'*50)
    print('Processing %d of %d zoning codes' % (n,len(codes)))
    codename = codes[code].strip('\n')
    output[codename] = ''
    cdf = get_code_group(df,code)
    result_list = list()
    print('%d properties to analyze' % len(cdf.index.tolist()))
    for i in cdf.index.tolist():
        nbrs = find_neighbors(cdf,i)
##        if len(nbrs) > 1:
##            pdb.set_trace()
        try:
            for var in test_vars:
                mean, stdev = gen_local_stats(cdf,nbrs,var)
                target_var = df[var][i]
                local_Z_score = (target_var - mean)/stdev
                global_Z_score = (np.log10(target_var) - global_stats[var]['mean'])/global_stats[var]['std']
                if abs(local_Z_score) > local_threshold or abs(global_Z_score) > global_threshold:
                    prop_data = df.loc[i,'owner':'prop_stype'].tolist()
                    report_item = dict()
                    report_item['property data'] = prop_data
                    report_item['metric'] = var
                    report_item['quantity'] = target_var
                    report_item['local Z score'] = local_Z_score
                    report_item['global Z score'] = global_Z_score
                    report_item['local stats'] = [mean, stdev]
                    result_list.append(report_item)
        except:
            continue
    output[codename]=result_list

#Autopsy this madness
with open('output_dict', 'wb') as f:
    pickle.dump(output,f, pickle.HIGHEST_PROTOCOL)

print('Writing out')
#Generate report file
outfile = open('Outlier Report','w')
for key in output:
    outfile.write('\n'+key+'\n'+'-'*40)
    for item in output[key]:
        for item_key in item:
            outfile.write('\n'+item_key+':'+str(item[item_key]))
        outfile.write('\n')
outfile.close()

quit()                
