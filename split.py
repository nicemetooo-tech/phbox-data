import json, hashlib

def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return {}

def ver(o):
    return hashlib.sha1(json.dumps(o, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]

d = load("data.json")
items = d.get("items", {})
hot_items = {k: v for k, v in items.items() if k.startswith("hot_")}
matrix_items = {k: v for k, v in items.items() if not k.startswith("hot_")}

hot = {"classes": d.get("classes", []), "items": hot_items}
matrix = {"items": matrix_items}
pool = {"pools": d.get("pools", {})}
for o in (hot, matrix, pool):
    o["v"] = ver(o)
    n = sum(len(v) for v in o.get("items", {}).values()) if "items" in o else len(o.get("pools", {}))
    print("%s entries=%d v=%s" % (list(o.keys())[0], n, o["v"]))
for name, o in [("hot.json", hot), ("matrix.json", matrix), ("pool.json", pool)]:
    json.dump(o, open(name, "w"), ensure_ascii=False, separators=(",", ":"))
