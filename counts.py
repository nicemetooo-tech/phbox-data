import os, json, time, random, urllib.request, urllib.parse, subprocess

UA='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
CK='hyqv'
GAP=float(os.environ.get('GAP','4'))
OUT='counts.json'

TYPES=['喜剧','爱情','动作','科幻','动画','悬疑','犯罪','惊悚','冒险','音乐','历史','奇幻','恐怖','战争','传记','歌舞','武侠','灾难','西部','纪录片','短片']
AREAS=['华语','欧美','中国大陆','美国','日本','韩国','中国香港','中国台湾','英国','法国','德国','意大利','西班牙','印度','泰国','俄罗斯','加拿大','澳大利亚','爱尔兰','瑞典','巴西','丹麦']
YEARS=['2020年代','2026','2025','2024','2023','2022','2021','2020','2019','2010年代','2000年代','90年代','80年代','70年代','60年代','更早']
TVGENRES=['喜剧','爱情','悬疑','动画','武侠','古装','家庭','犯罪','科幻','恐怖','历史','战争','动作','冒险','传记','剧情','奇幻','惊悚','灾难','歌舞','音乐']
SHOWGENRES=['真人秀','脱口秀','音乐','歌舞']
PLATFORMS=['腾讯视频','爱奇艺','优酷','湖南卫视','Netflix','HBO','BBC','NHK','CBS','NBC','tvN']

def get(path, params):
    url=f'https://m.douban.com/rexxar/api/v2/{path}?'+urllib.parse.urlencode(params)
    r=urllib.request.Request(url, headers={'User-Agent':UA,'Referer':'https://m.douban.com/'})
    for _ in range(2):
        try:
            d=json.loads(urllib.request.urlopen(r,timeout=20).read())
            return d.get('total',0)
        except Exception:
            time.sleep(30)
    return None

def rec_total(tags, sel):
    t=get('movie/recommend',{'refresh':'0','start':'0','count':'1','uncollect':'false','score_range':'0,10',
        'selected_categories':json.dumps(sel,ensure_ascii=False),'tags':tags,'ck':CK})
    time.sleep(GAP+random.random())
    return t

def tv_total(tags, sel):
    t=get('tv/recommend',{'refresh':'0','start':'0','count':'1','uncollect':'false','score_range':'0,10',
        'selected_categories':json.dumps(sel,ensure_ascii=False),'tags':tags,'ck':CK})
    time.sleep(GAP+random.random())
    return t

def main():
    old={}
    try: old=json.load(open(OUT))
    except Exception: pass
    now=int(time.time()); out={}
    jobs=[]
    for g in TYPES: jobs.append((f'movie|genre|{g}', lambda g=g: rec_total(g,{'类型':g,'地区':''})))
    for a in AREAS: jobs.append((f'movie|area|{a}', lambda a=a: rec_total(a,{'类型':'','地区':a})))
    for y in YEARS: jobs.append((f'movie|year|{y}', lambda y=y: rec_total(y,{'类型':'','地区':''})))
    for g in TVGENRES: jobs.append((f'tv|genre|{g}', lambda g=g: tv_total(f'{g},电视剧',{'类型':g,'形式':'电视剧'})))
    for g in SHOWGENRES: jobs.append((f'tv|show|{g}', lambda g=g: tv_total(f'{g},综艺',{'类型':g,'形式':'综艺'})))
    for a in AREAS: jobs.append((f'tv|area|{a}', lambda a=a: tv_total(f',{a}',{'类型':'','地区':a})))
    for p in PLATFORMS: jobs.append((f'tv|platform|{p}', lambda p=p: tv_total(f',{p}',{'类型':'','地区':''})))
    changed={}
    for key, fn in jobs:
        t=fn()
        out[key]={'total': t, 'at': now}
        prev=(old.get(key) or {}).get('total')
        if prev is not None and t is not None and t!=prev:
            changed[key]={'old': prev, 'new': t, 'at': now}
            print(key, prev, '->', t, flush=True)
    json.dump(out, open(OUT,'w'), ensure_ascii=False, indent=0)
    json.dump(changed, open('changes.json','w'), ensure_ascii=False, indent=0)
    print('done jobs', len(jobs), 'changed', len(changed))
    if os.environ.get('GIT_COMMIT')=='1':
        run=lambda c: subprocess.run(c,shell=True,capture_output=True)
        run('git config user.name phbox-bot'); run('git config user.email bot@users.noreply.github.com')
        run('git add counts.json changes.json || true'); run('git commit -m "counts"'); run('git push')

if __name__=='__main__': main()
