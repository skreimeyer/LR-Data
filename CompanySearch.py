#! /usr/bin/python3.5

import sqlite3
import requests
import bs4
import re
import pdb

class db_handler:

    def __init__(self):
        self.db = ('LR.db')
        self.invalid_names = []
        

    def connect(self):
        #Not sure if this would fly in the init method
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        return conn, cursor

    def fetch_companies(self, cursor):
        #Return a list object of corporate land owners
        cursor_obj = cursor.execute('''SELECT owner FROM property WHERE
                                    owner LIKE "% LLC" OR "% INC" OR
                                    "% CORP%" OR "% CO" GROUP BY owner''')
        list_obj = [str(record[0]) for record in cursor_obj]
        #Strip punctuation and LLC/INC/etc from end of strings
        newlist = [x.split(' ') for x in list_obj]
        for i,y in enumerate(newlist):
            for j,z in enumerate(y):
                newlist[i][j] = z.strip()
                newlist[i][j] = z.strip(',')
                newlist[i][j] = z.strip('.')
            newlist[i] = ' '.join(y[:-1])
        return newlist

    def create_tables(self, cursor):
        #Create tables for companies, people and positions and association tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS company (UID INTEGER PRIMARY KEY ASC,
                       name TEXT, type TEXT, address TEXT, date TEXT, forn_name TEXT,
                       forn_add TEXT, state TEXT)
                       ''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS people (UID INTEGER PRIMARY KEY ASC, last TEXT,
                       first TEXT, mi TEXT)
                       ''')
        cursor.execute('CREATE TABLE IF NOT EXISTS roles (UID INTEGER PRIMARY KEY ASC, title TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS links (corp_id INTEGER, person_id INTEGER, role_id INTEGER)')
        return True

    def load_data(self,cursor, corp_data):
        #Read through our dictionary object and make relevant INSERT statements
        flag_corp = False
        test_corp = cursor.execute('SELECT 1 FROM company WHERE name = ?',(corp_data['Corporation Name'],))
        if test_corp.fetchone() is not None:
            flag_corp = True
        if not flag_corp:
            #making tuple object here for legibility in query statement
            insert_vals = (corp_data['Corporation Name'],corp_data['Filing Type'],
                            corp_data['Principal Address'],corp_data['Date Filed'],
                            corp_data['Foreign Name'],corp_data['Foreign Address'],
                            corp_data['State of Origin'])
            cursor.execute('''INSERT INTO company (name, type, address, date, forn_name, forn_add,
                           state) VALUES (?,?,?,?,?,?,?)''', insert_vals)
        #This case should only happen after if-block fires
        corp_curs_id = cursor.execute('SELECT UID FROM company WHERE name = ?',(corp_data['Corporation Name'],))
        corp_id = corp_curs_id.fetchone()[0]
        #loop through officers and INSERT accordingly
        officers = corp_data['Officers']
        #Whoops, forgot reg agent
        officers.append(('Registered Agent',corp_data['Reg. Agent']))
        for title, name in officers:
            if name == 'SEE FILE':
                continue
            fullname = name.split(' ')
            if len(fullname) >= 3:
                #This should strip off suffixes or stupid 4+-part names
                first, mi, last = fullname[:3]
                mi = mi[:1]
            elif len(fullname) == 2:
                first,last = fullname
                mi = ''
            else:
                self.invalid_names.append(name)
                continue                
            flag_people = False
            test_people = cursor.execute('SELECT 1 FROM people WHERE first = ? AND last = ?',(first,last))
            if test_people.fetchone() is not None:
                flag_people = True
            if not flag_people:
                cursor.execute('INSERT INTO people (last, first, mi) VALUES (?,?,?)',(last, first, mi))
            #TODO: TEST FOR NULL STRING INSERT, SELECT
            person_curs_id = cursor.execute('SELECT UID FROM people WHERE last = ? AND  first = ?',
                                     (last,first))
            person_id = person_curs_id.fetchone()[0]
            flag_role = False
            test_role = cursor.execute('SELECT 1 FROM roles WHERE title = ?',(title,))
            if test_role.fetchone() is not None:
                flag_role = True
            if not flag_role:
                cursor.execute('INSERT INTO roles (title) VALUES (?)',(title,))
            role_curs_id = cursor.execute('SELECT UID FROM roles WHERE title = ?',(title,))
            role_id = role_curs_id.fetchone()[0]
            #Take IDs and insert into link table
            cursor.execute('INSERT INTO links (corp_id, person_id, role_id) VALUES (?,?,?)',
                           (corp_id,person_id,role_id))
        return True

class web_handler:
    
    def __init__(self):
        self.url = 'http://www.sos.arkansas.gov/corps/search_corps.php'
        self.post_dict = {'filing_number': '', 'SEARCH': 'Search', 'agent_city': '',
                          'cmd': '', 'corp_name': '', 'fict_name': '',
                          'agent_search': '', 'corp_type_id': '', 'agent_state': ''}

    def search_corps(self, corp_name):
        #return results page for search query
        post_data = self.post_dict
        post_data['corp_name'] = corp_name
        response = requests.post(self.url, data=post_data)
        code = response.status_code
        response_text = response.text
        return code, response_text

    def fetch_corp(self, URL):
        #return results page for company
        response = requests.get(URL)
        code = response.status_code
        response_text = response.text
        return code, response_text
    
class parser:

    def __init__(self, response_text):
        self.parser = 'lxml'
        self.response = response_text

    def read_table(self):
        soup = bs4.BeautifulSoup(self.response,self.parser)
        #The only data we want is in the main table
        tables = soup.find_all('table')
        #Get rows from main table, this is conveniently
        #the same for query response and corp lookup
        rows = tables[1].find_all('tr')
        return rows

    def get_search_num(self, row):
        #retrieve number of records after passing appropriate table row
        num_records_str = row.get_text()
        num_match = re.search(r'[\d]+',num_records_str)
        num_records = int(num_match.group(0))
        return num_records

    def parse_search_row(self, row):
        #retrieve standing, title and URL
        data = row.find_all('td')
        URL = data[0].a['href']
        #concatenate because search URL is a relative position
        URL = 'http://www.sos.arkansas.gov/corps/'+URL
        standing = data[3].get_text()
        name = data[0].get_text()
        return URL, standing, name

    def fetch_company(self, rows):
        #return dictionary of company data
        out_dict = {}
        for row in rows[1:15]:
            data = row.find_all('td')
            out_dict[data[0].get_text()] = str(data[1].get_text()).strip()
        return out_dict

    def extract_officers(self, out_dict):
        #Create dictionary object in place of nonsense string in the
        #officers row
        #pdb.set_trace()
        officers = out_dict['Officers']
        #Get rid of unicode prefix
        officers = str(officers)
        #get a uniform delimiter between names and titles. Drop punctuation
        officers = re.sub('(?<=[a-z])(?=[A-Z])','|',officers)
        officers = re.sub('\s(?=[A-Z][a-z]+)','|',officers)
        officers = re.sub('[,\.]','',officers)
        officers = officers.split('|')
        officers = [x.strip() for x in officers]
        #Iterate through our list of names and titles, return a list of
        #tuples representing Title:Name pairs. Can't use a dict because
        #one title can map to several names
        officer_list = []
        name_flag = True
        for x in officers:
            if name_flag == True:
                name = x
                name_flag = False
            else:
                officer_list.append((x,name))
                name_flag = True
        return officer_list

#Driver
print('\n'+'#'*20)
db = db_handler()
conn, cur = db.connect()
print('database connection made')
db.create_tables(cur)
corps = db.fetch_companies(cur)
wh = web_handler()
print('web handler initialized')
#create list objects for failed queries
status_error = []
ambiguous = []
not_found = []

for index,corp in enumerate(corps):
    print('%d of %d complete' % (index,len(corps)))
    try:
        code,response = wh.search_corps(corp)
    except:
        print('Connection failed! Check the URL')
        quit()
    if code != 200:
        print('SERVER ERROR FOR %s' % corp)
        status_error.append((corp,code))
        continue
    #parse HTML for table rows
    pars = parser(response)
    rows = pars.read_table()
    if len(rows) == 2:
        not_found.append((corp,'post'))
        continue
    num_records = pars.get_search_num(rows[3])
    if num_records >= 10:
        ambiguous.append(corp)
        continue
    else:
        #Adding 5 because 5 is the first row our data appears on and we
        #want our range to include the last line with valid information
        row_max = 5 + num_records
    row_data = []
    for x in range(5,row_max):
        URL,standing,name = pars.parse_search_row(rows[x])
        row_data.append((URL,standing,name))
    hit_count = 0
    for i,j in enumerate(row_data):
        if 'Good Standing' in j:
            hit_count += 1
            index = i
    #TODO: create method for compare strings for search and result corp names
    if hit_count == 0:
        not_found.append((corp,'DEFUNCT'))
        continue
    elif hit_count >= 2:
        ambiguous.append(corp)
        continue
    try:
        code, response = wh.fetch_corp(row_data[i][0])
    except:
        print('FAILED TO CONNECT AT CORP METHOD!')
        continue
    if code != 200:
        status_error.append((corp,code,'GET'))
        print('SERVER ERROR SECOND BLOCK %s' % corp)
        continue
    #create new parser object and repeat for search results
    pars = parser(response)
    rows = pars.read_table()
    corp_data = pars.fetch_company(rows)
    officer_data = pars.extract_officers(corp_data)
    corp_data['Officers'] = officer_data
    #load into db
    try:
        #pdb.set_trace()
        db.load_data(cur,corp_data)
        conn.commit()
    except:
        print('FAILED TO LOAD DATA FOR %s' % corp)

conn.commit()
conn.close()
#Export all our errors to reports
r1 = open('status_errors.rpt','w')
for i in status_error:
    r1.write(str(i+)'\n')
r1.close()
r2 = open('ambiguous.rpt','w')
for i in ambiguous:
    r2.write(str(i)+'\n')
r2.close()
r3 = open('not_found.rpt','w')
for i in not_found:
    r3.write(str(i))
    r3.write('\n')
r3.close()

print('complete')
quit()
