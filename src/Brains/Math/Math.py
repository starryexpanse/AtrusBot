PACKAGE_NAME = "Math Functions"
PACKAGE_AUTHOR = "Philip Peterson"
PACKAGE_EMAIL = "carniojack424@gmail.com"



def ABL_math(self, msg, user, args):
    """Usage: math EXPRESSION
    Calculates the result of a mathematical expression.
    Examples: math (4+3)/2 ; math sin(30deg) ; math (4!)
    Note: currently not implemented."""
    # TODO
    
def ABL_dni(self, msg, user, args):
    """Usage: dni INTEGER
    Outputs a text-based D'ni representation of a decimal integer.
    Examples: dni 4 ==> ] ,-[
    Notes: Commas are ignored. Decimal points (or other non-numeric characters) yield an error."""
    
    def ArabicToDni(numb):
        def baseN(num, b):
            return ((num == 0) and  "0") or (baseN(num // b, b).lstrip("0") + "0123456789abcdefghijklmnopqrstuvwxyz"[num % b])
    
        dninumerals = { "0": u" \u00B7 ",
                        "1": u" | ",
                        "2": u")  ",
                        "3": u"K  ",
                        "4": u"  \u2308",
                        "5": u"---",
                        "6": u"-|-",
                        "7": u"B--",
                        "8": u"K--",
                        "9": u"--F",
                        "a": u",-,",
                        "b": u",+,",
                        "c": u")-,",
                        "d": u"\u15d5-,",
                        "e": u",-r",
                        "f": u"\./",
                        "g": u"\|/",
                        "h": u")\/",
                        "i": u"K\/",
                        "j": u"\/+",
                        "k": u" '-",
                        "l": u"|'-",
                        "m": u")'-",
                        "n": u"K'-",
                        "o": u" \u00A6="
                        }
        
        retStr = ""
        
        if numb == 25:
            retStr = u"| X "
        else:
            for digit in baseN(numb, 25):
                if digit in dninumerals:
                    retStr = retStr + u"|" + dninumerals[digit] 
        
        
        
        retStr = u"]" + retStr[1:] + u"["
        return retStr
    
    
    try:
        numtoconvert = int(args[0].replace(",",""))
    except ValueError:
        return (("err", {
                         "kind": "badinput",
                         "function_name": "dni"
                         }),)
    try:
        return (("say", user+": "+ArabicToDni(numtoconvert)),)
    except:
        return (("err", {
                         "kind": "unk",
                         "function_name": "dni"
                         }),)
