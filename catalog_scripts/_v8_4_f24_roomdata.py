# -*- coding: utf-8 -*-
import json, io
s = io.open(r"C:\Users\t2262\aritomo-memo\room.html", encoding="utf-8").read()
i = s.index("var ROOM_DATA = ")
j = s.index("\n", i)
raw = s[i+len("var ROOM_DATA = "):j].rstrip().rstrip(";")
data = json.loads(raw)
print("version", data["meta"]["version"])
for f in data.get("fixtures",[]):
    if f.get("id") in ("F-24","F-25","F-11","F-12"):
        print(json.dumps(f, ensure_ascii=False)); print("---")
for o in data.get("openings",[]):
    if o.get("id") in ("WIN-02","D-02","D-04","D-11"):
        print(json.dumps(o, ensure_ascii=False)); print("===")
