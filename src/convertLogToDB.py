#!/usr/bin/python

import os, os.path, re
import AtrusData as AtrusDataHelper
import time

echo "Sorry. This was a work-in-progress, but I never finished it, and now it's just here for a rainy day. Bugs abound probably."
exit(11)


execfile(os.path.join(os.path.dirname("/home/ironmagma/AtrusBot/"), "AtrusBot.conf.py"))

AtrusData = AtrusDataHelper.AtrusData(
                                                    user = conf_user, 
                                                    password = conf_password, 
                                                    host = conf_host,
                                                    database = conf_database,
                                                    table_prefix = conf_table_prefix,
                                                    channel = conf_channel
                                                  )


files = []

for file in os.listdir("/var/www/irclogs/"):
    if file.endswith(".log"):
        files.append(os.path.join("/var/www/irclogs/",file))
        
files.sort()
files.remove("/var/www/irclogs/current.log")

for file in files:
    h = open(file, "r")
    log = h.read()
    h.close()
    lineno = 0
    for line in re.split("\r?\n", log):
        lineno = lineno+1
        if line.strip() == "":
            continue
        timestamp, line = line.partition(" ")[0:3:2]
        timetoparse = file.rpartition("/")[2].rpartition(".")[0] + " " + timestamp
        if line.startswith("[connected"):
            continue
        elif line.startswith("[disconnected"):
            continue
        #print file, lineno, timestamp
        timetoparse = time.strptime(timetoparse, "%Y-%m-%d [%H:%M:%S]")
        timetoput = time.strftime("%Y-%m-%d %H:%M:%S", timetoparse)
        if line.startswith("<>") or line.startswith("&lt;&gt;"):
            pass
        elif line.startswith("&lt;") or line.startswith("<"):
            if line.startswith("&lt;"):
                secpart = line.split("&gt;")[0].split("&lt;")[1]
            else:
                secpart = line.split(">")[0].split("<")[1]
            actualmsg = line.partition(secpart)[2].partition(" ")[2]
            AtrusData.log({
                    "kind": "chan_msg", 
                    "who": secpart, 
                    "msg": actualmsg
                    }, custTime=timetoput)
        elif line.endswith("left the channel]"):
            secpart = line.partition(" ")[0]
            secpart = secpart.partition("[")[2]
            AtrusData.log({
                    "kind": "user_leave", 
                    "who": secpart
                    }, custTime=timetoput)
        elif line.endswith("joined the channel]"):
            secpart = line.partition(" ")[0]
            secpart = secpart.partition("[")[2]
            AtrusData.log({
                    "kind": "user_join", 
                    "who": secpart
                    }, custTime=timetoput)
        elif line.startswith("* "):
            user = line.partition("* ")[2].partition(" ")[0]
            msg = line.partition(user+" ")[2]
            AtrusData.log({
                            "kind": "chan_msg", 
                            "who": user, 
                            "msg": "/me %s" % msg
                           }, custTime=timetoput)
        elif line.find(" is now known as ") != -1:
            old_nick = line.partition(" ")[0]
            new_nick = line.rpartition(" ")[2]
            AtrusData.log({
                    "kind": "user_nick_change", 
                    "who": old_nick, 
                    "msg": new_nick
                    }, custTime=timetoput)
        elif line.startswith("[I have joined "):
            channel = line.partition("have joined ")[2].rpartition("]")[0]
            AtrusData.log({
                    "kind": "bot_join",
                    "msg": channel
             }, custTime=timetoput)
        elif line.find(" quit the network because: ") != -1:
            #print line
            user = line.partition(" quit the network")[0].partition("[")[2]
            reason = line.partition("because: ")[2].rpartition("]")[0]
            AtrusData.log({
                    "kind": "user_quit", 
                    "who": user, 
                    "msg": reason
                    }, custTime=timetoput)
        else:
            #pass # just blank lines...
            if line.strip() != "":
              print file, line
