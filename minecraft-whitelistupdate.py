#!/usr/bin/python3

import yaml
import json
import sqlite3
import vanillabean
import sys
import queue
import threading

with open('/minecraft/host/config/server.yaml', 'r') as configfile:
    config = yaml.load(configfile)


dbfile = config['dbfile']
mcfolder = config['mcdata']


whitelist = {each["uuid"]: each["name"] for each in json.load(open(mcfolder + "/whitelist.json"))}

# print(whitelist)

q = queue.Queue()

def writeToDB():
    global q
    while True:
        DBWriter(q.get())
        q.task_done()


def DBWriter(queryArgs):
    global dbfile
    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()
    
    fail = True
    while(fail):
        try:
            cur.execute(*queryArgs)
            conn.commit()
            fail = False
        except sqlite3.OperationalError:
            print("Locked")
            fail = True
            

            
threadDBWriter = threading.Thread(target=writeToDB)
threadDBWriter.setDaemon(True)
threadDBWriter.start()
                                                                                                





conn = sqlite3.connect(dbfile)
cur = conn.cursor()

cur.execute('select name, UUID from (select * from (select * from joins order by date asc) group by UUID) where date < datetime("now", "-120 day") group by UUID')
old = [each[1] for each in cur.fetchall()]

cur.execute('select name, UUID from (select * from (select * from joins order by date asc) group by UUID) group by UUID')
active = [each[1] for each in cur.fetchall()]
# print(current)

cur.execute('select * from whitelist where ts < datetime("now", "-14 days")')
twoWeeksOnList = [each[1] for each in cur.fetchall()]

didntlogin = [each for each in twoWeeksOnList if each not in active]



expired = [each[1] for each in list(whitelist.items()) if each[0] in old or each[0] in didntlogin]


print(expired)

delete = False

if len(sys.argv) > 1:
    delete = True if sys.argv[1] == "delete" else False

for name in expired:
    if delete:
        vanillabean.send("/whitelist remove " + name)
    else:
        print(name)


cur.execute("DELETE FROM whitelist")

for each in list(whitelist.items()):

    q.put(("INSERT OR IGNORE INTO whitelist (name, UUID) VALUES (?,?)", (each[1], each[0])))

conn.commit()
conn.close()



