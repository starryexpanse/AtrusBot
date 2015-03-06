##### AtrusData.py

if __name__ == '__main__':
    from sys import exit
    exit("AtrusData is a helper and should be used as such.")

import MySQLdb

import os, os.path, copy, __main__

# load config
path = os.path.abspath(__main__.__file__)
execfile(os.path.join(os.path.dirname(path), "AtrusBot.conf.py"))

## Delete .pyc files (disables caching of the module)
thispath = os.path.abspath(__file__+"c")
if os.path.isfile(thispath):
    os.remove(thispath)

##### AtrusBot's Model (database-handling functions)

class AtrusData():
    def __init__(self, user = "", password = "", host = "localhost", table_prefix = "", database = "AtrusBot", channel = None, casesensitive = False):
        self.user = user
        self.password = password
        self.host = host
        self.table_prefix = table_prefix
        self.database = database
        self.channel = channel
        self.dbhandle = None
        self.casesensitive = casesensitive

        self.sqlisdown = False # for one-time error messaging

    ## Logging
        
    def log(self, parms, custTime = None):
        print "log:", parms
        try:
            self.__runQueryAndForget(
                            "INSERT INTO `%s` (`kind`, `who`, `when`, `msg`, `bot_speak`, `channel`) VALUES (%s, %s, %s, %s, %s, %s)" % 
                                     (
                                       self.__table("logs"), # prefix_logs
                                       self.__f(parms.get("kind")), 
                                       self.__f(parms.get("who")),
                                       "NOW()" if not custTime else self.__f(custTime),
                                       self.__f(parms.get("msg")),
                                       self.__f(parms.get("bot_speak", False)),
                                       self.__f(parms.get("channel", self.channel))
                                     )
                )
        except MySQLdb.OperationalError:
            pass
        
  
    ## Text Assets

    def publishRichTextAsset(self, text):
       return self.publishTextAsset(text, ext="html", before="""
<HTML>
<HEAD>
   <TITLE>Rich Text Asset</TITLE>
   <META http-equiv="Content-Type" content="text/html;charset=utf-8">
</HEAD>
<BODY>
<tt><pre>""", after = """</pre></tt>
</BODY>
</HTML>
""")

    def publishTextAsset(self, text, ext="txt", before="", after=""):
       global conf_webtextassets_path

       ind = 0

       while os.path.exists(os.path.join(conf_webtextassets_path, str(ind))+"."+ext):
           ind += 1

       h = open(os.path.join(conf_webtextassets_path, str(ind))+"."+ext, "w", )
       h.write((before+text+after).encode("utf-8"))
       h.close()

       return (ind, ext)

    def getTextAssetURLFromID(self, tup):
       global conf_webtextassets_uri
       return conf_webtextassets_uri+str(tup[0])+"."+str(tup[1])

    ## Lower-level MySQL abstraction
        
    def __table(self, table):
        # Prepends a table name with a prefix, if there is one
        return self.table_prefix+table if self.table_prefix else table
        
    def __f(self, val):
        self.__renewConnectionIfNeeded()
        # Serializes Python variables to MySQL-acceptable format.
        #         (prevents SQL injections)
        # __f(True)        -->    1
        # __f("hello")     -->   'hello'
        # __f(u"hello")    -->   'hello'
        # __f(None)        -->    NULL
        # __f(3.3)         -->   '3.3'
        # __f(float("inf)) -->   'infinity'
        
        if val == None:
            return "NULL"
        elif isinstance(val, str) or isinstance(val, unicode):
            return "'"+self.dbhandle.escape_string(val)+"'"
        elif val is True or val is False:
            return "'"+('1' if val else '0')+"'" # 0 if False, 1 if True. nifty :-)
        elif isinstance(val, float) or isinstance(val, int) or isinstance(val, long):
            if val == float("inf"):
                return "'infinity'"
            else:
                return "'"+str(val)+"'"
        
    def __callErrHandler(self, msg):
        if "__call__" in dir(self.errhandler):
            self.errhandler(msg)
        
    def __renewConnectionIfNeeded(self, custom_db = None):
        
        doRenew = False
        
        if not isinstance(self.dbhandle, MySQLdb._mysql.connection):
            doRenew = True
        elif self.dbhandle.stat() == "MySQL server has gone away":
            doRenew = True
        else:
            if self.sqlisdown:
                self.sqlisdown = False
                self.__callErrHandler("[[ DB is now available. ]]")
            
        if doRenew:
            print "connecting with", self.user, self.password, self.host
            self.dbhandle = MySQLdb.connect(user = self.user, passwd = self.password, host = self.host)
            if custom_db:
                self.dbhandle.select_db(custom_db)
            elif self.database:
                self.dbhandle.select_db(self.database)

            self.dbhandle.set_character_set("utf8")
        
        # If after having renewed the connexion, it's still down...
        
        if self.dbhandle.stat() == "MySQL server has gone away":    
            if not self.sqlisdown:
                    self.sqlisdown = True
                    self.__callErrHandler("[[ DB has become unavailable. Please try again later. ]]")
        else:
            self.sqlisdown = False
    
    def __closeConnection(self):
        if isinstance(self.dbhandle, MySQLdb._mysql.connection):
            self.dbhandle.close()
    
    def finished(self):
        self.__CloseConnection()
    
    def __query(self, query, custom_db = None):
        print query
        self.__renewConnectionIfNeeded(custom_db = custom_db)
        self.dbhandle.query(query)
        self.dbhandle.commit()

    def __getResultFromQuery(self, query, custom_db = None):
        self.__query(query = query, custom_db = custom_db)
        resobj = self.dbhandle.store_result()
        
        result_list = []
        
        keepgoing = True
        
        while keepgoing:
            j = resobj.fetch_row()
            if not j == ():
                result_list.append(j)
            else:
                keepgoing = False
            del j
        
        return result_list
    
    def __runQueryAndForget(self, query, custom_db = None):
        self.__query(query = query, custom_db = custom_db)
        self.dbhandle.store_result()
    
    ### General Userlist Bookkeeping
    
    def registerUser(self, nick, email, displayname):
        nick = nick.lower()
        user = self.__getListOfAliasesMatchingNick(nick)
        if len(user) == 0:
            if self.__getResultFromQuery("SELECT COUNT(*) from `%s` WHERE LOWER(`email`) = LOWER(%s)" % (
                                                                            self.__table("users"),
                                                                            self.__f(email.lower())
                                                                                )
            )[0][0][0] == 0:
                self.__runQueryAndForget("INSERT INTO `%s` (`display_name`, `email`, `permissions_level`) VALUES (%s, %s, 0)" % (
                                                                                                                 
                                                                                                        self.__table("users"),
                                                                                                        self.__f(displayname),
                                                                                                        self.__f(email.lower())
                                                                                                        
                                                                                                        ))
                
                userid = self.__getResultFromQuery("SELECT LAST_INSERT_ID()")[0][0][0]
                
                self.__runQueryAndForget("DELETE FROM `%s` WHERE `real_id` = %s" % (self.__table("aliases"), self.__f(userid)))
                self.__runQueryAndForget("INSERT INTO `%s` (`real_id`, `nick`) VALUES (%s, %s)" % (self.__table("aliases"), self.__f(userid), self.__f(nick)))
                        # Populate aliases table with a new alias.
                
                return (True, 2) # Code 2: Success
            else:
                return (False, 1) # Code 1: E-mail already registered.
        else:
            return (False, 0) # Code 0: Nick already registered as user.
    
    def makeNewAlias(self, curnick, newnick):
        newnick = newnick.lower()
        curnick = curnick.lower()
        
        userid = self.getUserIDFromNick(curnick)
        if userid:
            newnickid = self.getUserIDFromNick(newnick)
            if newnickid:
                if newnickid == userid:
                    return 0
                else:
                    return 1
            else:
                self.__runQueryAndForget("INSERT INTO `%s` (`real_id`, `nick`) VALUES (%s, %s)" % 
                                         (self.__table("aliases"), self.__f(userid), self.__f(newnick))
                                         )
                return 3
            return True
        else:
            return 2
    
    def __getListOfAliasesMatchingNick(self, user):
        return self.__getResultFromQuery("SELECT `real_id` from `%s` WHERE LOWER(`nick`) = LOWER(%s)" % (
                                                                                          self.__table("aliases"), 
                                                                                          self.__f(user))
                                                                                                                    )
    
    def doesUserIdExist(self, userid):
        
        if not userid:
            return False
        
        return self.__getResultFromQuery("SELECT COUNT(*) from `%s` WHERE `userid` = %s" % (
                                                                            self.__table("users"),
                                                                            self.__f(userid)
                                                                                )
            )[0][0][0] == 1
    
    ### User/Nick Equivalence
    
    def getUserIDFromNick(self, nick):
        user = self.__getListOfAliasesMatchingNick(nick) # TODO truncate to 1
        if len(user) == 0:
            return None
        else:
            return user[0][0][0]
        
    def getUserDataFieldFromNick(self, nick, fieldname):
        userid = self.getUserIDFromNick(nick)
        if self.doesUserIdExist(userid):
            return self.__getResultFromQuery("SELECT `"+fieldname+"` from `%s` WHERE `userid` = %s" % (
                                                                            self.__table("users"),
                                                                            self.__f(userid)
                                                                                )
            )[0][0][0]
        else:
            return None

    def getUserDataFieldFromID(self, id, fieldname):
        return self.__getResultFromQuery("SELECT `"+fieldname+"` from `%s` WHERE `userid` = %s" % (
                                                                            self.__table("users"),
                                                                            self.__f(id)
                                                                                )
            )[0][0][0]

    def getUsernameFromNick(self, nick):
        return self.getUserDataFieldFromNick(nick, "display_name")
        
    def getUsernameFromID(self, id):
        return self.getUserDataFieldFromID(id, "display_name")
    
    def getIDListOfUsernames(self, usernames):
        return self.__getResultFromQuery("SELECT `nick`, `real_id` from `%s` WHERE BINARY LOWER(`nick`) IN (%s)" % (
                                                                            self.__table("aliases"),
                                                                            ", ".join(map(self.__f, map(str.lower, usernames)))
                                                                                )
            )
    
    ### User Privileges
    
    def getAdminList(self, cols="*"):
        return self.__getResultFromQuery("SELECT "+cols+" from `%s` WHERE `permissions_level` >= 1" % self.__table("users"))
    
    def isAdmin(self, nick=None, id=None):
        
        if not id:
            userid = self.getUserIDFromNick(nick)
        else:
            userid = id
        
        if self.doesUserIdExist(userid):
            return self.__getResultFromQuery("SELECT `permissions_level` from `%s` WHERE `userid` = %s" % (
                                                                            self.__table("users"),
                                                                            self.__f(userid)
                                                                                )
            )[0][0][0] == 1
        else:
            return False
    
    def makeAdmin(self, nick):
        return self.__setPermissionsLevel(level = 1, nick = nick)
        
    def makeUnprivUser(self, nick):
        return self.__setPermissionsLevel(level = 0, nick = nick)
    
    def __setPermissionsLevel(self, level=0, nick=None, id=None):
        if not id:
            userid = self.getUserIDFromNick(nick)
        else:
            userid = id
        
        if self.doesUserIdExist(userid):
            self.__runQueryAndForget("UPDATE `%s` SET `permissions_level` = %s WHERE `userid` = %s" % (
                                                                            self.__table("users"),
                                                                            self.__f(level),
                                                                            self.__f(userid)
                                                                                )
                                            )
            return True
        else:
            return False
        
    ### Online/Offline
    
    #def markUserOnline(self, nick=None, id=None, online=True):
    #    if not id:
    #        userid = self.getUserIDFromNick(nick)
    #    else:
    #        userid = id
    #    
    #    if userid:
    #        self.__runQueryAndForget(
    #                        "UPDATE `%s` SET `last_ping` = NOW(), `online` = 1 WHERE `userid` = %s" % 
    #                                 (
    #                                   self.__table("users"), # prefix_logs
    #                                   self.__f(userid)
    #                                 )
    #            )
    
    #def isUserOnline(self, id):
    #    return self.__getResultFromQuery("SELECT `online` FROM `%s` WHERE `userid` = %s LIMIT 1" % (
    #                                                                        self.__table("users"),
    #                                                                        self.__f(id)       ))[0][0][0] == 1
    
    #def getOfflineUserMatchingNick(self, nick):
    #    
    #    userid = self.getUserIDFromNick(nick)
    #    
    #    if userid:
    #        if not self.isUserOnline(id=userid):
    #            return userid
    #        else:
    #            return None
    #    else:
    #        return None
    #    
    #    results = self.__getResultFromQuery("SELECT `real_id` FROM `%s` WHERE LOWER(`nick`) = %s LIMIT 1" % (
    #                                                                        self.__table("aliases"),
    #                                                                        self.__f(nick.lower()))       )
    #    if len(results) == 0:
    #        return None
    #    else:
    #        return results[0][0][0]
            
    #def markAllOfflineExcept(self, idlist):
    #    self.__runQueryAndForget(
    #                    "UPDATE `%s` SET `online` = (`userid` IN (%s))" % 
    #                                    (
    #                                        self.__table("users"), # prefix_logs
    #                                        ",".join(map(self.__f, map(str, idlist)))
    #                                    )
    #    )
    
    
    ### Offline Messages
    

    def isNickWantingOffMsgs(self, nick):
        res = self.__getResultFromQuery(
                        ("SELECT `wants_offmsgs` from `%s` WHERE LOWER(`nick`) = LOWER(%s)") % (self.__table("aliases"), self.__f(nick)))
        if len(res) == 0:
           return False
        else:
           return res[0][0][0]

    def saveOfflineMessage(self, from_user, to_user, message, timestmp = None):
        self.__runQueryAndForget(
                        "insert into `%s` (`from`, `to`, `when`, `text`, `unread`) values (%s, %s, %s, %s, 1)" % 
                                        (
                                            self.__table("offmsgs"),
                                            self.__f(from_user),
                                            self.__f(to_user),
                                            self.__f(timestmp) if timestmp is not None else "now()",
                                            self.__f(message)
                                        )
        )
        
    def getOfflineMessages(self, nick = None, id = None):
        if id is None:
            if nick is None:
                return ()
            id = self.getUserIDFromNick(nick)
        
        if id is None:
            return ()
        
        return self.__getResultFromQuery(
                        "select `from`, `text`, `msgid` from %s where `unread` = 1 and `to` = %s order by `when`" % 
                                        (
                                            self.__table("offmsgs"),
                                            self.__f(id)
                                        )
        )
        
    def markMessagesAsRead(self, msgidlist):
        if len(msgidlist) > 0:
            self.__runQueryAndForget(
                            "update `%s` set `unread` = 0 where `msgid` in (%s)" % 
                                            (
                                                self.__table("offmsgs"),
                                                ", ".join(map(self.__f, msgidlist))
                                            )
            )
    
    ### factoids
    
    def getFactoidsList(self):
        ret_dict = {}
        for factoid in self.__getResultFromQuery("select `trigger`, `value`, `is_symlink` from `%s` order by length(`trigger`) desc" % (
                                                                            self.__table("factoids")
                                                                                )
                                            ):
            lookupkey = factoid[0][0]
            if not self.casesensitive:
                lookupkey = lookupkey.lower()
            ret_dict[lookupkey] = { "value": factoid[0][1], "symlink": factoid[0][2] }
        return ret_dict
    
    def getFactoidMatching(self, mention):
        cs = "binary " if self.casesensitive else ""
        
        
        return self.__getResultFromQuery( ("select `trigger` from `%s` where "+cs+"substring(%s, 1, length(`trigger`)) = "+cs+"`trigger` order by length(`trigger`) desc limit 1") % (
                                                                            self.__table("factoids"),
                                                                            self.__f(mention)
                                                                                ))
    
    def getFactoidValue(self, trigger):
        cs = "binary " if self.casesensitive else ""
        
        return self.__getResultFromQuery( ("select `trigger`, `value`, `is_symlink` from `%s` where "+cs+"`trigger` = "+cs+"%s order by length(`trigger`) desc limit 1") % (
                                                                            self.__table("factoids"),
                                                                            self.__f(trigger)
                                                                                ))
    
    def isFactoidAlready(self, trigger):
        cs = "binary " if self.casesensitive else ""
        
        return self.__getResultFromQuery( ("select count(*) from `%s` where "+cs+"`trigger` = "+cs+"%s") % (
                                                                            self.__table("factoids"),
                                                                            self.__f(trigger)
                                                                                ))[0][0][0] > 0
    def storeFactoid(self, trigger, target, symlink):
        cs = "binary " if self.casesensitive else ""
        
        if self.isFactoidAlready(trigger):
            self.__runQueryAndForget(
                            ("update `%s` set `trigger` = %s, `value` = %s, `is_symlink` = %s where "+cs+"`trigger` = "+cs+"%s") % 
                                     (
                                       self.__table("factoids"),
                                       self.__f(trigger),
                                       self.__f(target),
                                       self.__f(symlink),
                                       self.__f(trigger)
                                     )
                )
        else:
            self.__runQueryAndForget(
                            "insert into `%s` (`trigger`, `value`, `is_symlink`) values (%s, %s, %s)" % 
                                     (
                                       self.__table("factoids"),
                                       self.__f(trigger),
                                       self.__f(target),
                                       self.__f(symlink)
                                     )
                )
            
    def getFactoidsLinkingTo(self, trigger, countonly = False):
        cs = "binary " if self.casesensitive else ""
        matches = self.__getResultFromQuery( ("select "+
                                           
                                                ("count(" if countonly else "")+
                                           
                                           "`trigger`"+
                                                
                                                (")" if countonly else "")+
                                                
                                           " from `%s` where `is_symlink` = 1 and "+
                                                    cs+"`value` = "+cs+"%s") % (
                                                                                                           
                                                                                                            self.__table("factoids"),
                                                                                                            self.__f(trigger)
                                                                                                            
                                                                                                                                      )
                                            )
        
        
        if len(matches) >= 1:
            return map(lambda x: x[0][0], matches)
        else:
            return []
    
    def getEventualTarget(self, trigger, redirects=0, seensofar = None, casesensitive = False):
        
        if seensofar is None:
            seensofar = []
        
        class Target(dict):
            def __init__(self, found=False, trigger=None, redirects=0, value=None, infiniteloop=False, path=[]):
                self.found = self["found"] = found
                self.trigger = self["trigger"] = trigger
                self.redirects = self["redirects"] = redirects
                self.value = self["value"] = value
                self.infiniteloop = self["infiniteloop"] = infiniteloop
                self.path = self["path"] = path
        
        target = self.getFactoidValue(trigger)
        
        if len(target) == 1: # the model found the trigger
            target = target[0][0]
            if target[2] == 0: # the factoid is not a link
                #print "factoid is not a link. right now seensofar is", seensofar, ". appending", trigger
                seensofar.append(trigger)
                #print "now seensofar is", seensofar, ". returning value.\n\n"
                return Target(found = True,
                              trigger = trigger,
                              redirects = redirects,
                              value = target[1],
                              path = seensofar)
            else:
                #print "factoid is a link. seensofar is", seensofar
                if not target[1].lower() in map(lambda x: x.lower(), seensofar):
                    #print "apparently", target[1], "isn't in seensofar, so, adding that now, and recursing with new value", target[1]
                    seensofar.append(trigger)
                    return self.getEventualTarget(target[1], redirects=redirects+1, seensofar=seensofar)
                else:
                    #print "we've already seen", target[1], "so i'm going to say this is an infinite loop. adding target[1] to seensofar."
                    #print "before adding, seensofar is", seensofar
                    seensofar.append(trigger)
                    seensofar.append(target[1])
                    #print "now, it's", seensofar
                    return Target(found = True,
                              trigger = trigger,
                              redirects = redirects,
                              value = target[1],
                              path = seensofar,
                              infiniteloop = True)
        else:
            seensofar.append(trigger)
            return Target(found=False,
                          trigger=trigger,
                          redirects = redirects,
                          path = seensofar)
