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
pools = d.get("pools", {})

hot = {"classes": d.get("classes", []),
       "items": {k: v for k, v in items.items() if k.startswith("hot_")}}
big = {"items": {k: v for k, v in items.items() if not k.startswith("hot_")},
       "pools": {k: v for k, v in pools.items() if k in ("movie_all", "tv_all")}}
hot["v"] = ver(hot); big["v"] = ver(big)
json.dump(hot, open("hot.json", "w"), ensure_ascii=False, separators=(",", ":"))
json.dump(big, open("big.json", "w"), ensure_ascii=False, separators=(",", ":"))
print("hot items=%d classes=%d" % (sum(len(v) for v in hot["items"].values()), len(hot["classes"])))
print("big items=%d pools=%s" % (sum(len(v) for v in big["items"].values()), list(big["pools"])))
