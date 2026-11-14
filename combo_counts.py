import os, json, time, random, urllib.request, urllib.parse, subprocess

UA='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
CK='hyqv'
GAP=float(os.environ.get('GAP','5'))
OUT='combo_counts.json'

TYPES=['喜剧','爱情','动作','科幻','动画','悬疑','犯罪','惊悚','冒险','音乐','历史','奇幻','恐怖','战争','传记','歌舞','武侠','灾难','西部','纪录片','短片']
AREAS=['华语','欧美','中国大陆','美国','日本','韩国','中国香港','中国台湾','英国','法国','德国','意大利','西班牙','印度','泰国','俄罗斯','加拿大','澳大利亚','爱尔兰','瑞典','巴西','丹麦']
TVFORMS=['电视剧','综艺']

def total(path, tags, sel):
    url=f'https://m.douban.com/rexxar/api/v2/{path}/recommend?'+urllib.parse.urlencode({
        'refresh':'0','start':'0','count':'1','uncollect':'false','score_range':'0,10',
        'selected_categories':json.dumps(sel,ensure_ascii=False),'tags':tags,'ck':CK})
    r=urllib.request.Request(url, headers={'User-Agent':UA,'Referer':'https://m.douban.com/'})
    for _ in range(2):
        try:
            d=json.loads(urllib.request.urlopen(r,timeout=20).read())
            time.sleep(GAP+random.random()); return d.get('total',0)
        except Exception:
            time.sleep(30)
    return None

def main():
    old={}
    try: old=json.load(open(OUT))
    except Exception: pass
    now=int(time.time()); out={}; changes={}
    jobs=[]
    for g in TYPES:
        for a in AREAS:
            jobs.append((f'movie|{g}|{a}', 'movie', f'{g},{a}', {'类型':g,'地区':a}))
    for f in TVFORMS:
        for a in AREAS:
            jobs.append((f'tv|{f}|{a}', 'tv', f'{f},{a}', {'类型':'','形式':f,'地区':a}))
    for key, path, tags, sel in jobs:
        t=total(path, tags, sel)
        out[key]={'total': t, 'at': now}
        prev=(old.get(key) or {}).get('total')
        if prev is not None and t is not None and t!=prev:
            changes[key]={'old': prev, 'new': t, 'at': now}
            print(key, prev, '->', t, flush=True)
    json.dump(out, open(OUT,'w'), ensure_ascii=False, indent=0)
    json.dump(changes, open('combo_changes.json','w'), ensure_ascii=False, indent=0)
    print('done', len(jobs), 'changed', len(changes))
    if os.environ.get('GIT_COMMIT')=='1':
        run=lambda c: subprocess.run(c,shell=True,capture_output=True)
        run('git config user.name phbox-bot'); run('git config user.email bot@users.noreply.github.com')
        run('git add combo_counts.json combo_changes.json || true')
        run('git commit -m "combo counts"'); run('git push')

if __name__=='__main__': main()
