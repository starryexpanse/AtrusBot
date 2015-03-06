#!/usr/bin/python2.7

#    _____                   ______         
#   (, /  |                 (, /    )       
#     /---| _/_ __      _     /---(  ____/_ 
#  ) /    |_(__/ (_(_(_/_)_) / ____)(_) (__ 
# (_/                     (_/ (     




# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer, ssl
from twisted.python import log

# some imports
import time, sys, cgi, os, random, urllib, re, string
from copy import deepcopy
import MySQLdb

# model
import AtrusData as AtrusDataHelper

# controller
import AtrusLogic as AtrusLogicHelper


# lets us restart/reload the program
import os.path, __main__ 
path = os.path.abspath(__main__.__file__)


execfile(os.path.join(os.path.dirname(path), "AtrusBot.conf.py"))

# pseudo-constants (python doesn't have constants)
IS_TESTING_MODE = False


###!!!!!!!!!!!!!!!!!!###
# NOT for customization.
keeprunning = True # when it becomes false, client will be able to kill itself

class AtrusBot(irc.IRCClient):
    
    def __init__(self):
        global conf_nickname, channel, conf_ckey, conf_npasswd, conf_database_user, conf_database_password, conf_database_host, conf_database, conf_table_prefix, conf_hpassword
        
        self.nickname = conf_nickname
        self.channel = conf_channel
        self.ckey = conf_ckey
        self.npasswd = conf_npasswd
        self.password=conf_hpassword
        
        self.recentmsgtimes = []
        self.pendingmsgs = []
        
        self.shuttingdown = False
        
        # Create AtrusData and AtrusLogic instances
        self.AtrusData = AtrusDataHelper.AtrusData(
                                                    user = conf_database_user,
                                                    password=conf_database_password,
                                                    host=conf_database_host,
                                                    database=conf_database,
                                                    table_prefix=conf_table_prefix,
                                                    channel=self.channel
                                                  )
        self.AtrusLogic = AtrusLogicHelper.AtrusLogic(self.AtrusData) 
                # Pass AtrusData instance to AtrusLogic constructor, providing it
                # with model access.
        

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.AtrusData.log({
                            "kind": "bot_connect"
                            })
        

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.AtrusData.log({
                            "kind": "bot_disconnect"
                            })

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        
        if not IS_TESTING_MODE:
            if self.npasswd:
                self.msg("nickserv", "id "+self.npasswd)
            self.msg("chanserv", "identify "+self.channel+" "+self.npasswd)
            self.msg("chanserv", "op "+self.channel)
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.AtrusData.log({
                            "kind": "bot_join", 
                            "msg": channel
                            })
        self.channel = channel
        self.usersonline = []
        self.askforlist()
        self.loopingmsgdaemon()

    def askforlist(self):
        self._who(self.channel)

    def _who(self, target):
        self._pending_who = []
        self.sendLine('WHO %s' % (target,))
        
    def irc_RPL_WHOREPLY(self, prefix, params):
        ch_name, user, host, server, nick, flags, gecos = params[1:8]
        hops, gecos = gecos.split(' ', 1)
        
        self._pending_who.append(nick)


    def irc_RPL_ENDOFWHO(self, prefix, params):
        self.usersonline = deepcopy(self._pending_who)
        
        reactor.callLater(4.5, self.askforlist)

    def userJoined(self, user, channel):
        # Called when a user joins the channel.
        
        print "user joined", user, channel
        self.AtrusData.log({
                            "kind": "user_join", 
                            "who": user
                            })
        print "done!"
        self.usersonline.append(user)
        print "Appended."


    def userLeft(self, user, channel):
        # Called when a user leaves the channel.
        self.AtrusData.log({
                            "kind": "user_leave", 
                            "who": user
                           })
        
    def userQuit(self, user, quitMessage):
        # Called when a user quits the network.
        self.AtrusData.log({
                            "kind": "user_quit", 
                            "who": user, 
                            "msg": quitMessage
                           })
        
    def noticed(self, user, channel, msg):
        print "***NOTICE", user, channel, msg
        self.AtrusData.log({
                    "kind": "notice", 
                    "who": user, 
                    "msg": msg,
                    "channel": channel
                   })
    
    def privmsg(self, user, channel, msg):
        # Called when the bot receives a message.
        user = user.split('!', 1)[0]
        
        instructions = []
        
        if channel == "AUTH":
            pass
        elif channel.lower() == self.nickname.lower(): # privmsg -- don't log
            if msg.startswith("!"):
                msg = msg[1:]
            instructions = self.AtrusLogic.parseReaction(msg, user)
        elif channel.lower() == self.channel.lower():
            self.AtrusData.log({
                    "kind": "chan_msg", 
                    "who": user, 
                    "msg": msg
                   })
            if msg.startswith("!"):
                instructions = self.AtrusLogic.parseReaction(msg[1:], user)
            elif msg.lower().startswith(self.nickname.lower()+": ") or msg.lower().startswith(self.nickname.lower()+", "):
                instructions = self.AtrusLogic.parseReaction(msg[(len(self.nickname)+2):], user)
            elif msg.lower().startswith(self.nickname.lower()+":") or msg.lower().startswith(self.nickname.lower()+","):
                instructions = self.AtrusLogic.parseReaction(msg[(len(self.nickname)+1):], user)
                
                
        for instruction in instructions:
            if instruction[0] == "say":
                self.bsay(instruction[1], channel)
            elif instruction[0] == "sys":
                if instruction[1] == "reboot":
                    if channel.lower() == self.nickname.lower(): # it's a privmsg
                        if len(self.pendingmsgs) > 0:
                            self.bsay("<waiting on other requests before proceeding with restart>", user, highpriority=True)
                        self.bsay("See you soon.", user)
                    elif channel.lower() == self.channel.lower(): # it's a channel message
                        if len(self.pendingmsgs) > 0:
                            self.bsay("<waiting on other requests before proceeding with restart>", self.channel, highpriority=True)
                    self.bsay("See y'all real soon.", self.channel)
                    self.shuttingdown = True
                    self.shutdownloop()
                    
        
    def shutdownloop(self):
        if self.shuttingdown and len(self.pendingmsgs) == 0:
            global keeprunning
            keeprunning = False
            self.transport.loseConnection()
        else:
            reactor.callLater(1.0, self.shutdownloop)
        
    def bsay(self, msg, channel, highpriority = False):
        if not self.shuttingdown:
            
            if highpriority:
                insertpoint = 0 # Push it to the front of the queue, if it's high-priority.
            else:
                insertpoint = len(self.pendingmsgs)
            
            self.pendingmsgs.insert(insertpoint, (msg, channel))
        
    def msgdaemon(self):
        
        # Asynchronously push pending messages to the server. This
        # allows for throttling (to avoid kicks from the server).
        
        okaytosend = True
        
        while okaytosend and len(self.pendingmsgs) > 0:
            
            self.recentmsgtimes = self.recentmsgtimes[-4:] # truncate the list of recent messages to length 4
        
            okaytosend = False
        
            if len(self.recentmsgtimes) >= 4:
                if time.time()-self.recentmsgtimes[1] > 10.0: # err on the side of caution?
                    okaytosend = True
            else:
                okaytosend = True
                
                
            if okaytosend:
                msg, chan = self.pendingmsgs.pop(0)
                
                self.msg(chan, msg)
                self.recentmsgtimes.append(time.time())
                
                if chan.lower() == self.channel.lower(): # (don't log if it's a privmsg)
                    self.AtrusData.log({
                                "kind": "chan_msg", 
                                "who": self.nickname, 
                                "msg": msg, 
                                "bot_speak": True
                               })
            else:
                pass # Not doing anything until the next call; too many messages in too little time.
        
        
            
    def loopingmsgdaemon(self):
        self.msgdaemon()
        reactor.callLater(1.3, self.loopingmsgdaemon)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an 'action' (say /me blah)."""
        user = user.split('!', 1)[0]
        
        self.AtrusData.log({
                            "kind": "chan_msg", 
                            "who": user, 
                            "msg": "/me %s" % msg
                           })

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.AtrusData.log({
                            "kind": "user_nick_change", 
                            "who": old_nick, 
                            "msg": new_nick
                           })



class AtrusBotFactory(protocol.ClientFactory):
    """A factory for AtrusBots.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = AtrusBot

    def __init__(self):
        global conf_channel
        self.channel = conf_channel

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        global keeprunning, path
        if keeprunning:
            connector.connect()
        else:
            print "nohup "+path+" "+ " ".join(sys.argv[1:]) +" &"
            os.system(path + " " + " ".join(sys.argv[1:]))
            reactor.callLater(2, reactor.stop)

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.callLater(30, connector.connect)


if __name__ == '__main__':
    
    # create factory protocol and application
    f = AtrusBotFactory()

    # connect factory to this host and port
    #reactor.connectSSL("pos.starryexpanse.com", 65003, f, ssl.ClientContextFactory())
    reactor.connectTCP("irc.starryexpanse.com", 6667, f)

    # run bot
    reactor.run()
