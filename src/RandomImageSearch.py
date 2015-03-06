import random, urllib, json

fh = open("/home/ironmagma/GehnBot/english.txt", "r")
lis = fh.read()
fh.close()

spl = lis.split("\n")

result=json.loads(urllib.urlopen("http://ajax.googleapis.com/ajax/services/search/images?v=1.0&q="+random.choice(spl) + "%20" + random.choice(spl)).read())

tquote = urllib.urlopen("http://www.quotedb.com/quote/quote.php?action=random_quote").read()[16:].split("<br>")[0]

msg = str(tquote) + " " + str(result["responseData"]["results"][0]["url"])

print msg