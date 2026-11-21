import json, os, hashlib

def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return None

d = load("data.json") or {}
hot = {"classes": d.get("classes", []), "items": d.get("items", {})}
pool = {"pools": d.get("pools", {})}

def ver(o):
    return hashlib.sha1(json.dumps(o, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]

hot["v"] = ver(hot)
pool["v"] = ver(pool)
json.dump(hot, open("hot.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(pool, open("pool.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("hot items=%d classes=%d v=%s" % (sum(len(v) for v in hot["items"].values()), len(hot["classes"]), hot["v"]))
print("pool combos=%d v=%s" % (len(pool["pools"]), pool["v"]))
