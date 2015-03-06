## Define Built-in Commands

try:
    texttable
except NameError:
    import texttable


def ABL_restart(self, msg, user, args):
    
    """Usage: restart
    Chat: Restarts the bot (requires admin privileges).
    Web: Reloads the webpage."""
       
    isadmin = False
    try:
        isadmin=self.AtrusData.isAdmin(user)
    except:
        isadmin=False
       
    if isadmin or self.AtrusData.sqlisdown or self.implementation == "web":
        return (("sys", "reboot"),)
    else:
        return (("err", {
                         "kind" : "notadmin",
                         "function_name": "restart"
                         }),)

def ABL_shutdown(self, msg, user, args):
    
    """Usage: shutdown
    Chat: Shuts down the bot (requires admin privileges, or having the bot's target nick)."""
       
    isadmin = False
    try:
        isadmin=self.AtrusData.isAdmin(user)
    except:
        isadmin=False
       
    if isadmin or self.AtrusData.sqlisdown or self.implementation == "web" or (user == self.AtrusBot.desired_nickname and user is not None):
        return (("sys", "shutdown"),)
    else:
        return (("err", {
                         "kind" : "notadmin",
                         "function_name": "shutdown"
                         }),)
    
def ABL_help(self, msg, user, args):
    """Usage: help [COMMAND]
       Returns documentation about a single command."""
    
    if len(args) == 1:
        if args[0].lower() in self.brainfunctions:
            thefunc = self.brainfunctions[args[0].lower()]
            if thefunc.__doc__ and thefunc.__doc__ != "":
                command_list = []
                thedoc = thefunc.__doc__.split("\n")
                for line in thedoc:
                    command_list.append(["say", line.strip()])
                return command_list
            else:
                return (("say", "Command '%s' has no documentation." % args[0].lower()),)
            
        else:
            return (("say", "I don't know about command '"+args[0].lower()+"'."),)
    elif len(args) == 0:
        return (("say", "Use 'commands' if you don't know what command you want, or 'help <commandname>' for help with a specific command."),)
    else:
        return (("err", {
                         "kind" : "exact_args",
                         "correct_number": 1,
                         "function_name": "help"
                         }),)
    
def ABL_man(self, msg, user, args):
    """Usage: man [COMMAND]
    Alias of 'help [COMMAND]'."""
    
    ABL_DONTLIST = True
    
    return ABL_help(self, msg, user, args)

def ABL_usage(self, msg, user, args):
    """Usage: usage [COMMAND]
    Alias of 'help [COMMAND]'."""
    
    ABL_DONTLIST = True
    
    return ABL_help(self, msg, user, args)

def ABL_commands(self, msg, user, args):
    """Usage: listcommands
       List all commands known by the bot."""
       
    funcs = []
       
    for x, y in self.brainfunctions.items():
        if not "ABL_DONTLIST" in y.__code__.co_varnames:
            funcs.append(x)
       
    cmdnamelist = sorted(funcs)
    
    return (("say", ", ".join(cmdnamelist)),)


def ABL_ping(self, msg, user, args):
    """Usage: ping [RESPONSE]
       Return RESPONSE if specified, or 'pong' if RESPONSE is omitted."""
    
    if len(args) > 0:
        return (("say", " ".join(args[0:])),)
    else:
        return (("say", "pong"),)

def ABL_iamadmin(self, msg, user, args):
    """Usage: iamadmin
    Reserves status as an administrator for the user running the command, if there are no others already holding the status."""
    
    if user == "webuser":
        return (("say", "That feature is not available through the web interface."),)
    elif len(self.AtrusData.getAdminList()) == 0:
        if self.AtrusData.makeAdmin(user):
            return (("say", "I have made you admin, %s." % user),) # Only allowed when there are zero admins.
        else:
            return (("say", "I could not make you admin, %s. Perhaps you are not registered as a user?" % user),)
    else:
        return (("say", "%s, there exists already at least one admin. He/she/they must be the one(s) to grant further admin privileges." % user),)

def ABL_register(self, msg, user, args):
    """Usage: register EMAILADDRESS DISPLAYNAME...
    Registers the user (and current nickname) with the bot."""
    
    if len(args) >= 2:
        email = args[0]
        displayname = " ".join(args[1:])
        
        result = self.AtrusData.registerUser(user, email, displayname)
        
        
        if result == (True, 2):
            return (("say", "%s, I have registered you." % user),)
        else:
            if result[1] == 0:
                return (("say", "%s: Your current nickname has already been registered." % user),)
            elif result[1] == 1:
                return (("say", "%s: That email address has already been registered." % user),)
    else:
        return (("say", "%s: REGISTER <email address> <display name>" % user),) # TODO make this like everything else



def ABL_makeadmin(self, msg, user, args):
    """Usage: makeadmin USER
    Endows USER with administrative privileges (requires admin privileges)."""
    
    if self.AtrusData.isAdmin(user):
        targetuser = args[0].lower()
        if self.AtrusData.isAdmin(targetuser):
            return (("say", "%s: %s is already an admin." % (user, args[0])),)
        else:
            if self.AtrusData.makeAdmin(targetuser):
                return (("say", "%s: %s has been made an admin." % (user, args[0])),)
            else:
                return (("say", "%s: I could not make %s an admin. Perhaps (s)he is not registered as a user?" % (user, args[0])),)
    else:
        return (("say", "%s: I cannot permit you to do that, as you are not an admin." % user),) # TODO make this an error

def ABL_iamalso(self, msg, user, args):
    """Usage: iamalso NEWNICK
    Link nickname NEWNICK to the account associated with the present nickname."""
    
    if user == "webuser":
        return (("say", "That feature is not available through the web interface."),)
    else:
        newnick = args[0]
        
        retcode = self.AtrusData.makeNewAlias(user, newnick)
        # 3 for success, 2 for unregistered, 1 for already linked with another's, 0 for already linked with yours
        
        
        if retcode == 3:
            return (("say", "%s: I have linked the nickname '%s' with your account." % (user, newnick)),)
        elif retcode == 2:
            return (("say", "%s: This nickname is unregistered. To link nicknames, run this command from an already-registered nick. See 'help iamalso' for usage details." % user),)
        elif retcode == 1:
            return (("say", "%s: That nickname is already linked with another account." % user),)
        elif retcode == 0:
            return (("say", "%s: That nickname is already linked with your account." % user),)
    
def ABL_makepeasant(self, msg, user, args):
    """Usage: makepeasant USER
    Revokes a user's privileges as an administrator (requires admin privileges)."""
    
    targetuser = args[0].lower()
    
    if self.AtrusData.isAdmin(user):
        if self.AtrusData.isAdmin(targetuser):
            if self.AtrusData.makeUnprivUser(targetuser):
                return (("say", "%s is no longer an admin." % targetuser),)
            else:
                return (("say", "An unknown error occurred..."),) # TODO make this an error
        else:
            return (("say", "%s: %s is a peasant already." % (user, targetuser)),)
    else:
        return (("say", "%s: I cannot permit you to do that, as you are but a peasant." % user),) # TODO make this an error

def ABL_admins(self, msg, user, args):
    """Usage: admins
    Lists all users who are admins."""
    
    adminlist = ", ".join(map(lambda x: x[0][0], self.AtrusData.getAdminList(cols="`display_name`")))

    return (("say", "%s: %s" % (user, adminlist) ),) # TODO make this an error


def ABL_abdicate(self, msg, user, args):
    """Usage: abdicate
    Revokes the administrative privileges of the user running the command (requires admin privileges)."""
    
    if self.AtrusData.isAdmin(user):
        self.AtrusData.makeUnprivUser(user)
        return (("say", "%s is no longer an admin." % user),)
    else:
        return (("say", "%s: You have no admin privileges to abdicate." % user),) # TODO make this an error

##########################
##  Factoids & Parsing  ##

def ABL_set(self, msg, user, args):
    """Usage: set ASSIGNMENT...
    Stores a factoid according to the instructions contained in ASSIGNMENT.
    !set "hello" is "Hi there."         stores a factoid under the trigger "hello" with the value "Hi there".
    !set "a" and "b" are "c" and "d"    stores two factoids, with triggers "a" and "b", and values "c" and "d" respectively.
    !set "a" is a link to "b"           makes any call to trigger "a" instead trigger a factoid with trigger "b"
    !set "1" is "2" is "a number"       stores trigger "1" with target "a number" and "2" as a link to "1"
    Shortcuts: instead of `and`, use `,`. Instead of `is`/`are`, use `=`. Instead of `is a link to` use `=!`. 
    """
    
    
    ### Begin parseArgs function ####################
    
    def parseArgs(msg, tokens = {}):
        
        class Token(dict):
            def __init__(self, type, value):
                self.type = self["type"] = type
                self.value = self["value"] = value
            def __repr__(self):
                return self["value"]
        
        quote_on = None
        minibuffer = ""
        buffer = []
        escaping = False
        
        def addstringtobuf(inp):
            buffer.append(Token("string", inp))
        
        def addoptobuf(inp):
            inp = inp.translate(string.maketrans("", ""), string.whitespace).lower()
            newvalue = None
            
            for tokenname, tokenlist in tokens.items():
                if inp in tokenlist:
                    newvalue = tokenname
                    
            if newvalue:
                buffer.append(Token("operator", newvalue))
                return True
            
            if not inp == "":
                return False
            else:
                return True
        
        for char in msg:
            if char == "\"" and not escaping:
                if not quote_on:
                    quote_on = char
                    if not addoptobuf(minibuffer):
                        return {
                                "error": {
                                           "kind": "unknownop",
                                           "arg": minibuffer.strip()
                                          }
                                }
                    minibuffer=""
                elif quote_on == "\"":
                    quote_on = None
                    addstringtobuf(minibuffer)
                    minibuffer=""
                else:
                    minibuffer += char
            elif char == "'" and not escaping:
                if not quote_on:
                    quote_on = char
                    if not addoptobuf(minibuffer):
                        return {
                                "error": {
                                           "kind": "unknownop",
                                           "arg": minibuffer.strip()
                                          }
                                }
                    minibuffer=""
                elif quote_on == "'":
                    quote_on = None
                    addstringtobuf(minibuffer)
                    minibuffer=""
                else:
                    minibuffer += char
            else:
                if char == "\\":
                    if not escaping:
                        escaping = True
                    else:
                        escaping = False
                        minibuffer += char
                else:
                    if escaping:
                        if char == "t":
                            minibuffer += "\t"
                        else:
                            minibuffer += char
                        escaping = False
                    else:
                        minibuffer += char
        
        #if quote_on:
        #    quote_on = False
        #    return {
        #                        "error": {
        #                                   "kind": "unterm"
        #                                  }
        #                        }
        #
        #quote_on = False
        return {
                 "parsed": buffer
                }
    
    ### End parseArgs function #############################
    
    
    accessor = self.accessor
    
    msg = msg.partition(" ")[2]
                    
                    
    def isListUnique(test_list):
        for current_index in range(len(test_list)):
            for i in range(len(test_list)):
                compa = test_list[i]
                compb = test_list[current_index]
                
                if not self.casesensitive:
                    compa = compa.lower()
                    compb = compb.lower()
                
                if not i == current_index and compa == compb:
                    return False
        return True
    
    def noEmptyTriggers(test_list):
        for current_index in test_list:
            if len(current_index) == 0 or current_index.startswith("-"):
                return False
        return True
    
    triggers = []
    targets = []
    
    part = 0
    
    laststr = None
    
    waserror = []
    
    parsetree = parseArgs(msg, tokens = {
                                              "LINKING_VERB": ("~>", "islinkto", "links", "linksto", "~~>", "*=", "=!", "isalinkto", "pointsto", "is!"),
                                              "BEING_VERB": ("are", "=", "->", "-->", "=>", "==>", "willbe", "equals", "is"),
                                              "DELIMITER" : (",", "and", "or", ",and", "+", ",+") 
                                              })
    
    if "parsed" in parsetree:
        pattern = ""
        for node in parsetree["parsed"]:
            if node["type"] == "string":
                pattern+="STR "
            if node["type"] == "operator":
                pattern+=node["value"]+" "
            
        pattern = pattern.strip()
           
        matchone = re.match("^(STR DELIMITER )*STR (BEING_VERB|LINKING_VERB) STR$", pattern)
            
        if matchone:
            # "hello" and "hi" are "greetings"
            
            isLinking = (matchone.group(2) == "LINKING_VERB")
            
            for node in parsetree["parsed"]:
                if part == 0:
                    if node["type"] == "string":
                        triggers.append(node["value"])
                    elif node["type"] == "operator":
                        if node["value"] in ("BEING_VERB", "LINKING_VERB"):
                            part=1
                elif part == 1:
                    if node["type"] == "string":
                        targets.append(node["value"])
            
            if isListUnique(triggers):
                if noEmptyTriggers(triggers):
                    self.AtrusData.storeFactoid(triggers[0], targets[0], isLinking)
                    if len(triggers) == 1:
                        return (("say", "%s: Stored%s '%s'." % (user, " link" if isLinking else "", triggers[0])),) # TODO
                    else:
                        for trigger in triggers[1:]:
                            self.AtrusData.storeFactoid(trigger, triggers[0], True)
                        return (("say", "%s: Stored '%s' and %d links." % (user, triggers[0], len(triggers)-1)),) # TODO
                else:
                    return (("say", "%s: Empty triggers and triggers beginning with one or more hyphens are not allowed." % (user)),)
            else:
                return (("say", "%s: You have listed the same trigger more than once. Aborted." % (user)),)
                    
        elif re.match("^(STR BEING_VERB )+STR$", pattern):
            # "trac" is "Trac" is "TRAC" is "that thing" is "http://trac.com/"
            
            
            
            for node in parsetree["parsed"]:
                if node["type"] == "string":
                    triggers.append(node["value"])
                    
            targets.append(triggers.pop()) # move the last trigger to the first target
            
            if isListUnique(triggers):
                if noEmptyTriggers(triggers):
                    self.AtrusData.storeFactoid(triggers[0], targets[0], False)
                    
                    for link in triggers[1:]:
                        self.AtrusData.storeFactoid(link, triggers[0], True)
                    
                    return (("say", "%s: Stored '%s' and %d links." % (user, triggers[0], len(triggers)-1)),)
                else:
                    return (("say", "%s: Empty triggers and triggers beginning with one or more hyphens are not allowed." % (user)),)
            else:
                return (("say", "%s: You have listed the same trigger more than once (note that triggers are not case-sensitive). Aborted." % (user)),)
        
        elif re.match("^(STR DELIMITER )+STR BEING_VERB (STR DELIMITER )+STR$", pattern):
            # "joe" and "Joe" and "joey" are "child" and "adult" and "kangaroo"
            for node in parsetree["parsed"]:
                if part == 0:
                    if node["type"] == "string":
                        triggers.append(node["value"])
                    elif node["type"] == "operator":
                        if node["value"] == "BEING_VERB":
                            part=1
                elif part == 1:
                    if node["type"] == "string":
                        targets.append(node["value"])
            
            if isListUnique(triggers):
                if noEmptyTriggers(triggers):
                    if len(triggers) == len(targets):
                        # print "triggers", triggers
                        # print "targets", targets
                        for x in range(len(triggers)):
                            #print "storing key", triggers[x], "as value", targets[x]
                            self.AtrusData.storeFactoid(triggers[x], targets[x], False)
                        return (("say", "%s: Stored %d triggers and %d values." % (user, len(triggers), len(targets))),) # TODO
                    else:
                        waserror.append({
                                         "kind": "eqnumtrigtarg",
                                         "numtrigs": triggers,
                                         "numtargs": targets
                                         })
                else:
                    return (("say", "%s: Empty triggers and triggers beginning with one or more hyphens are not allowed." % (user)),)
            else:
                return (("say", "%s: You have listed the same trigger more than once (note that triggers are not case-sensitive). Aborted." % (user)),)
            
        else:
            waserror.append({
                                     "kind": "invalidpattern",
                                     "pattern": pattern
                                     })
        
    else:
        waserror.append(parsetree["error"])
    
    if len(waserror) > 0:
        return (("say", user+": There was an error. "+str(waserror)),)

def ABL_cleanfactoids(self, msg, user, args):
    """Usage: cleanfactoids [--auto [--purge] [--reduce]] 
    Removes erroneous or winding-path factoids from the database.
    Options: 
    -a --auto   : Automatically carry out maintenance instead of reporting problems (requires elevated privileges).
    -r --reduce : Move >1-depth links to point directly to their eventual targets.
    -p --purge  : Remove links to nonexistent targets."""
    #TODO

def ABL_about(self, msg, user, args):
    """Usage: about -[wuIiknerRxm] FACTOID1 [FACTOID2 [...]]
    Gets information about factoids.
    
    Options:
    -w Wildcard search; Not yet implemented.
    
    Flags (flags define output; default is "-mix"):
    -u Ultimate target (`undef` for infinite loops, `null` for targetless links)
    -I Immediate value (for links, the name of the factoid it points to).
    -i like -I, but with the accessor prepended in the case of a link
    -k Kind of factoid (link, value, or void [for no match])
    -n Number of redirects
    -e Whether the target exists
    -r Whether the factoid is real (defined)
    -R like -r, but a true/false value
    -x List of links pointing to the factoid
    -m Normalized name of the factoid (if factoid is real, otherwise requested name)"""
    
    #TODO -w Wildcard search; match factoids using * as a wildcard (use \* for literal asterisk)
    
    instruction_list = []
    
    options = []
    flags = []
    
    
    outputtable = [
                   [] # Header row.
                   ]
                
    if len(args) < 1:
        return (("err", {
                         "kind": "atleastargs",
                         "correct_number": 1,
                         "function_name": "about"
                         }),)
    
    if args[0].startswith("-"): # Parse options/flags
        for bit in args.pop(0)[1:]:
            if bit in ("u","I","i","k","n","e","r","R","x","m"):
                flags.append(bit)
            elif bit in ("w"):
                options.append(bit)
            else:
                return (("err", {
                         "kind": "unknownflag",
                         "flag": bit,
                         "function_name": "about"
                         }),)
    
    if len(flags) == 0:
        flags = ["m","i","x"]
    
    if len(args) < 1:
        return (("err", {
                         "kind": "missingarg",
                         "argument_name": "FACTOID1",
                         "function_name": "about"
                         }),)
    
    factoidlist = []
    
    for factoid in args:
        if "w" in options:
            pass # TODO
        else:
            factoidlist.append(factoid)
       
    for flag in flags:
        if flag == "m":
            outputtable[0].append("Factoid Name")
        if flag == "I":
            outputtable[0].append("Immediate Value")
        if flag == "i":
            outputtable[0].append("Formatted Immediate Value")
        if flag == "k":
            outputtable[0].append("Kind")
    
    for factoid in factoidlist:
        frow = []
        outputtable.append(frow)
        
        srchresult = self.AtrusData.getFactoidValue(factoid)
        for flag in flags:
            if flag == "m":
                normname = srchresult[0][0][0] if len(srchresult) >= 1 else factoid
                frow.append(normname)
            if flag == "I":
                imval = srchresult[0][0][1] if len(srchresult) >= 1 else ""
                frow.append(imval)
            if flag == "i":
                imval = srchresult[0][0][1] if len(srchresult) >= 1 else ""
                if imval:
                    imval = self.accessor+imval if srchresult[0][0][2] == 1 else imval
                frow.append(imval)
            if flag == "k":
                imval = ("link" if srchresult[0][0][2]==1 else "value") if len(srchresult) >= 1 else "void"
                frow.append(imval)
         
    
    table = texttable.Texttable()
    table.add_rows(outputtable)

    return (("say", self.AtrusData.getTextAssetURLFromID(self.AtrusData.publishRichTextAsset(table.draw()))),)
    
    # TODO produce some output! :P
    #print options
    #print flags
    
    #for factoid in args:
    #    myret = self.AtrusData.getFactoidsLinkingTo(factoid)
    #    print myret
    #    instruction_list.append(("say", ",".join(myret)))
        
    #return instruction_list

def ABL_remove(self, msg, user, args):
    """Usage: remove [-nL] [FACTOID1 [FACTOID2 [...]]]
    Deletes each mentioned factoid from the database."""
    
    
    
    for x in args:
        pass
    
def ABL_argize(self, msg, user, args):
    """Usage: argize [ARG1 [ARG2 [...]]]
    Returns AtrusBot's interpretation of the arguments provided.
    Useful for troubleshooting input for another command."""
    return (("say", user+": "+str(args)),)
