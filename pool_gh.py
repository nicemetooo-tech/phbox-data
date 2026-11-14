import os, json, time, random, urllib.request, urllib.parse, subprocess

UA='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
CK='hyqv'
GAP=float(os.environ.get('GAP','6'))
MAXREQ=int(os.environ.get('MAXREQ','200'))
DATA='data.json'; PROG='pool_progress.json'

TYPES=['喜剧','爱情','动作','科幻','动画','悬疑','犯罪','惊悚','冒险','音乐','历史','奇幻','恐怖','战争','传记','歌舞','武侠','灾难','西部','纪录片','短片']
AREAS=['华语','欧美','中国大陆','美国','日本','韩国','中国香港','中国台湾','英国','法国','德国','意大利','西班牙','印度','泰国','俄罗斯','加拿大','澳大利亚','爱尔兰','瑞典','巴西','丹麦']
YEARS=['2020年代','2026','2025','2024','2023','2022','2021','2020','2019','2010年代','2000年代','90年代','80年代','70年代','60年代','更早']
TVGENRES=['喜剧','爱情','悬疑','动画','武侠','古装','家庭','犯罪','科幻','恐怖','历史','战争','动作','冒险','传记','剧情','奇幻','惊悚','灾难','歌舞','音乐']
SHOWGENRES=['真人秀','脱口秀','音乐','歌舞']
PLATFORMS=['腾讯视频','爱奇艺','优酷','湖南卫视','Netflix','HBO','BBC','NHK','CBS','NBC','tvN']
HOT_AREAS=['全部','华语','欧美','韩国','日本']
HOT_TV=[('综合','tv_hot'),('国产剧','tv_domestic'),('欧美剧','tv_american'),('日剧','tv_japanese'),('韩剧','tv_korean'),('动画','tv_animation'),('纪录片','tv_documentary')]
HOT_SHOW=[('综合','show_hot'),('国内','show_domestic'),('国外','show_foreign')]

def load(p,d):
    try: return json.load(open(p))
    except Exception: return d
def save(p,o):
    json.dump(o, open(p,'w'), ensure_ascii=False, separators=(',',':'))

req=0
def get(path, params):
    global req
    if req>=MAXREQ: raise SystemExit('limit')
    url=f'https://m.douban.com/rexxar/api/v2/{path}?'+urllib.parse.urlencode(params)
    r=urllib.request.Request(url, headers={'User-Agent':UA,'Referer':'https://m.douban.com/'})
    wait=60
    for a in range(3):
        try:
            d=json.loads(urllib.request.urlopen(r,timeout=25).read()); req+=1
            time.sleep(GAP+random.random()*2); return d,None
        except Exception as e:
            print('retry',path,str(e)[:50],flush=True); time.sleep(wait); wait*=2
    req+=1; return None,'fail'

def parse(items, kind=''):
    out=[]; seen=set()
    for it in items or []:
        i=it.get('id') or ''
        if not i.isdigit() or i in seen: continue
        sub=(it.get('card_subtitle') or '').split(' / ')
        if not sub or not (sub[0] or '').strip().isdigit(): continue
        seen.add(i)
        out.append({'n':it.get('title',''),'r':str((it.get('rating') or {}).get('value','') or ''),
                    'p':(it.get('pic') or {}).get('normal',''),
                    'u':'https://movie.douban.com/subject/%s/'%i,
                    'y':sub[0] if sub else '','a':sub[1] if len(sub)>1 else '','g':sub[2] if len(sub)>2 else '',
                    'k':kind})
    return out

def recent(path,cat,typ):
    out=[]; start=0; total=0
    while True:
        d,err=get(f'subject/recent_hot/{path}',{'start':str(start),'limit':'20','category':cat,'type':typ,'ck':CK})
        if err: return out,'fail'
        items=d.get('items') or []
        if not items: break
        total=d.get('total',0); out+=parse(items); start+=20
        if total and start>=total: break
    return out,None

def rec(path,tags,sel,pages=1):
    out=[]
    for p in range(pages):
        d,err=get(f'{path}/recommend',{'refresh':'0','start':str(p*20),'count':'20','uncollect':'false',
            'score_range':'0,10','selected_categories':json.dumps(sel,ensure_ascii=False),'tags':tags,'ck':CK})
        if err: return out,'fail'
        items=d.get('items') or []
        if not items: break
        out+=parse(items)
    return out,None

def merge(pool, items):
    seen={x['u'] for x in pool}
    for it in items:
        if it['u'] in seen: continue
        pool.append(it); seen.add(it['u'])

def git_push(msg):
    if os.environ.get('GIT_COMMIT')!='1': return
    run=lambda c: subprocess.run(c,shell=True,capture_output=True)
    run('git config user.name phbox-bot'); run('git config user.email bot@users.noreply.github.com')
    run('git add data.json pool_progress.json fail.json remaining.txt || true')
    run(f'git commit -m "{msg}"'); r=run('git pull --rebase origin main && git push'); print('push',r.returncode,flush=True)

def main():
    data=load(DATA,{'version':3,'classes':[],'items':{},'pools':{}})
    prog=load(PROG,{'done':{}}); done=prog['done']; fail=load('fail.json',{})
    data['version']=3
    data['classes']=[
      {'id':'hot_movie','name':'热播电影','filters':[{'key':'rank','name':'排序','values':['热门','最新','豆瓣高分']},{'key':'area','name':'地区','values':HOT_AREAS}]},
      {'id':'hot_tv','name':'热播电视剧','filters':[{'key':'type','name':'分类','values':[n for n,_ in HOT_TV]}]},
      {'id':'hot_show','name':'热播综艺','filters':[{'key':'type','name':'分类','values':[n for n,_ in HOT_SHOW]}]},
      {'id':'movie_all','name':'全部电影','filters':[
          {'key':'genre','name':'类型','values':['全部']+TYPES},
          {'key':'area','name':'地区','values':['全部']+AREAS},
          {'key':'year','name':'年代','values':['全部']+YEARS},
          {'key':'sort','name':'排序','values':['近期热度','首映时间','高分优先']}]},
      {'id':'tv_all','name':'全部电视剧','filters':[
          {'key':'type','name':'类型','values':['全部','电视剧','综艺']},
          {'key':'genre','name':'题材','values':['全部']+TVGENRES},
          {'key':'area','name':'地区','values':['全部']+AREAS},
          {'key':'platform','name':'平台','values':['全部']+PLATFORMS}]},
    ]
    pools=data.setdefault('pools',{})
    pools.setdefault('movie_all',[]); pools.setdefault('tv_all',[])
    mv=pools['movie_all']; tv=pools['tv_all']

    def job(key, fn):
        if key in done: return
        items,err=fn()
        if err or not items:
            fail[key]=int(time.time()); save('fail.json',fail); return
        merge(mv,items) if key.startswith('movie') else merge(tv,items)
        fail.pop(key,None); done[key]=int(time.time())
        save(DATA,data); save('pool_progress.json',prog)
        if len(done)%40==0: git_push(f'pool {len(done)}')

    today=time.strftime('%Y-%m-%d')
    SCOPE=os.environ.get('SCOPE','pool')
    do_hot=SCOPE in ('hot','all')
    do_pool=SCOPE in ('pool','all')
    try:
        for area in (HOT_AREAS if do_hot else []):
            typ='全部' if area=='全部' else area
            items,err=recent('movie','热门',typ)
            if items:
                data['items'][f'hot_movie|热门|{area}']=items
                data['items'][f'hot_movie|最新|{area}']=sorted(items,key=lambda x:x['y'] or '0',reverse=True)
                data['items'][f'hot_movie|豆瓣高分|{area}']=sorted(items,key=lambda x:(float(x['r']) if x['r'] else 0),reverse=True)
        for name,typ in (HOT_TV if do_hot else []):
            items,err=recent('tv','tv',typ)
            if items: data['items'][f'hot_tv|{name}']=items
        for name,typ in (HOT_SHOW if do_hot else []):
            items,err=recent('tv','show',typ)
            if items: data['items'][f'hot_show|{name}']=items

        data['hot_date']=today
        for g in (TYPES if do_pool else []):
            job(f'movie|genre|{g}', lambda g=g: rec('movie',g,{'类型':g,'地区':''},2))
        for a in (AREAS if do_pool else []):
            job(f'movie|area|{a}', lambda a=a: rec('movie',a,{'类型':'','地区':a},2))
        for y in (YEARS if do_pool else []):
            job(f'movie|year|{y}', lambda y=y: rec('movie',y,{'类型':'','地区':''},2))
        for g in (TVGENRES if do_pool else []):
            job(f'tv|genre|{g}', lambda g=g: rec('tv',f'{g},电视剧',{'类型':g,'形式':'电视剧'},2))
        for g in (SHOWGENRES if do_pool else []):
            job(f'tv|show|{g}', lambda g=g: rec('tv',f'{g},综艺',{'类型':g,'形式':'综艺'},2))
        for a in (AREAS if do_pool else []):
            job(f'tv|area|{a}', lambda a=a: rec('tv',f',{a}',{'类型':'','地区':a},2))
        for p in (PLATFORMS if do_pool else []):
            job(f'tv|platform|{p}', lambda p=p: rec('tv',f',{p}',{'类型':'','地区':''},2))
    except SystemExit:
        print('stopped at MAXREQ')
    finally:
        save(DATA,data); save('pool_progress.json',prog); save('fail.json',fail); git_push('pool final')
        total_jobs=len(TYPES)+len(AREAS)+len(YEARS)+len(TVGENRES)+len(SHOWGENRES)+len(AREAS)+len(PLATFORMS)
        rem=max(0,total_jobs-len([k for k in done]))
        open('remaining.txt','w').write(str(rem))
        print('items',sum(len(v) for v in data['items'].values()),'pool',len(mv),len(tv),'remaining',rem)

if __name__=='__main__': main()
