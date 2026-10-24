import json, sys
t = open("template.html", encoding="utf-8").read()
data = open("cards.json", encoding="utf-8").read().replace("</", "<\\/")
out = t.replace("/*CARD_DATA*/", data).replace("/*SNAPSHOT_DATE*/", sys.argv[1])
open(sys.argv[2], "w", encoding="utf-8").write(out)
print(len(out.encode()) // 1024, "KB")
