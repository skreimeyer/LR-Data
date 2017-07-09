#!/usr/bin/python3

import re
import json
import pdb

data = dict()
infile = open('LandCodes.txt','rb')

#pdb.set_trace()
for line in infile:
    inline = line.decode('unicode_escape').encode('ascii','ignore')
    code_match = re.search('(?<=Value)[A-Z]{2}',inline)
    if code_match:
        code = code_match.group(0)
    desc_match = re.search('(?<=Description)[\D^\\n]+',inline)
    if desc_match:
        data[code] = desc_match.group(0)
print line
infile.close()


outfile = open('code_key','w')
json.dump(data,outfile)
outfile.close()

quit()
