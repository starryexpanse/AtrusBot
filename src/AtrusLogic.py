##### AtrusLogic.py



if __name__ == '__main__':
    from sys import exit
    exit("AtrusLogic is a module and should be used as such.")

import sys, os, os.path, string, re, json

## Import packaged modules

sys.path.append( os.path.join(os.path.dirname( os.path.abspath(__file__) ), 'Modules')  )
import texttable

## Delete .pyc files (disables caching of the module)

thispath = os.path.abspath(__file__+"c")
if os.path.isfile(thispath):
    os.remove(thispath)

class AtrusLogic():
    def __init__(self, AtrusDataInstance, implementation=None, accessor = "!", casesensitive = False, AtrusBotInstance = None):
        self.AtrusData = AtrusDataInstance
        self.AtrusBot = AtrusBotInstance
        self.implementation = implementation
        self.accessor = accessor
        self.casesensitive = casesensitive
        
        self.moduledata = {}
        
        ### Parse Add-ons
        
        dirname = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Brains")
        self.braindir = dirname
        
        for file in os.listdir(dirname):
            #print "Found file", file
            if os.path.isdir(os.path.join(dirname, file)) and os.path.isfile(os.path.join(dirname, file, file+".py")):
                #print "Found executable", file+".py"
                execfile(os.path.join(dirname, file, file+".py"))
            
        self.brainfunctions = {}
        
            
        for name, local in locals().items():
            if name.upper().startswith("ABL_"):
                self.brainfunctions[name[4:].lower()] = local
        
    ## Argument Parsing/Tokenizing
    
    def getArgumentsFromCall(self, msg):
    
        class TruthyBuffer(list): # A list that is not falsy when empty
            def __nonzero__(self):
                return True
        
        quote_on = None
        minibuffer = ""
        buffer = TruthyBuffer()
        escaping = False
        
        decision = None
        
        def addstringtobuf(inp):
            buffer.append(inp)
        
        lastchar = ""
        
        for char in msg+" ":
            if char == "\"" and not escaping:
                if not quote_on:
                    quote_on = char
                elif quote_on == "\"":
                    quote_on = None
                else:
                    minibuffer += char
            elif char == "'" and not escaping:
                if not quote_on:
                    quote_on = char
                elif quote_on == "'":
                    quote_on = None
                else:
                    minibuffer += char
            elif char == " " and not quote_on and not escaping:
                if len(minibuffer) > 0 or lastchar in ("'", '"'):
                    addstringtobuf(minibuffer)
                minibuffer=""
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
                        elif char == " ":
                            minibuffer += " "
                        elif char == '"' and ((not quote_on) or quote_on == '"'):
                            minibuffer += "\""
                        elif char == "'" and ((not quote_on) or quote_on == "'"):
                            minibuffer += "'"
                        else:
                            minibuffer += "\\"+char
                        escaping = False
                    else:
                        minibuffer += char
            lastchar = char
        
        if quote_on:
            quote_on = False
            decision = {
                                "error": {
                                           "kind": "unterm"
                                          }
                                }
        
        else:
            quote_on = False
            decision = {
                 "parsed": buffer
                }
        
        if "parsed" in decision:
            return decision["parsed"]
        else:
            return None # If there's an error, it's going to be that there was an unterminated string literal
    
    	
    	
    def parseReaction(self, msg, user, disallowSetAsDetfault = False):
        instruction_list = []
        
        msg = msg.strip()
        
        cmd = msg.split(" ")[0].lower()
        
        # Nifty function by Bruno Desthuilliers at http://bytes.com/topic/python/answers/514838-how-test-if-object-sequence-iterable
        # Renders falsy when object is not a sequence
        isiterable = lambda obj: isinstance(obj, basestring) or getattr(obj, '__iter__', False)
        
        if len(cmd) >= 1 and cmd.strip()[0] in ('"', "'") and not disallowSetAsDetfault:
            cmd = "set"
            msg = "set "+msg # Allows easy setting of factoids; !"hello" is "hi there." rather than !set "hello" is "hi there."
        
        args = self.getArgumentsFromCall(msg.partition(" ")[2])
        
        if cmd in self.brainfunctions.keys():
            fn=self.brainfunctions[cmd]
            
            if fn.__code__.co_argcount < 4:
                instruction_list.append(("err", {"kind": "malformedcmd", "function_name": fn.__name__}))
            else:
                if args or "ABL_UNTERM_ALLOWED" in fn.__code__.co_varnames:
                    func_output = fn(self, msg, user, args)
                    if isiterable(func_output):
                        for instruction in func_output:
                            instruction_list.append(instruction)
                else:
                    instruction_list.append(("err", { "kind" : "unterm" }))
        
        return instruction_list
    
    def parseFactoids(self, msg, user, accessor="!"):
        """
        Searches `msg` for entries in the factoids database.
        Always returns the result for the longest match.
        
        !"foo" is "bar"     
        !"food" is "yum"    
        
        !foo                yields "bar"
        !food               yields "yum"
        I like !food a lot  yields "yum"
        
        !"a" is "A"
        !"b" is !a
        
        !a                  yields "A"
        !b                  yields "A"
        """
        
        keepsearching = True
        match = None
        
        while msg.find(accessor) != -1 and keepsearching:
            msg = msg.partition(accessor)[2]
            match = self.AtrusData.getFactoidMatching(msg)
            if len(match) == 1:
                keepsearching = False
            else:
                match = None
            
        if match:
            et = self.AtrusData.getEventualTarget(match[0][0][0])
            
            
            if et.found:
                if et["infiniteloop"] == False:
                    return (("say", et.value),)
                else:
                    return (("err", {
                                              "kind": "linkinfinite",
                                              "atuser": user,
                                              "path": et.path,
                                              "accessor": accessor
                                              }),)
            else:
                if et.redirects > 0:
                    return (("err", {
                                              "kind": "linkbadtarget",
                                              "atuser": user,
                                              "target": et.trigger,
                                              "accessor": accessor
                                              }),)
        
        return ()
