import os, json, time, random, urllib.request, urllib.parse, subprocess

UA='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
CK='hyqv'
GAP=float(os.environ.get('GAP','10'))
MAXREQ=int(os.environ.get('MAXREQ','300'))
SCOPE=os.environ.get('SCOPE','matrix')
DATA='data.json'; PROG='progress.json'

TYPES=['喜剧','爱情','动作','科幻','动画','悬疑','犯罪','惊悚','冒险','音乐','历史','奇幻','恐怖','战争','传记','歌舞','武侠','灾难','西部','纪录片','短片']
AREAS=['全部','华语','欧美','韩国','日本','中国大陆','美国','中国香港','中国台湾','英国','法国','德国','意大利','西班牙','印度','泰国','俄罗斯','加拿大','澳大利亚','爱尔兰','瑞典','巴西','丹麦']
TVFORMS=['电视剧','综艺']
PLATFORMS=['全部','腾讯视频','爱奇艺','优酷','湖南卫视','Netflix','HBO','BBC','NHK','CBS','NBC','tvN']
HOT_AREAS=['全部','华语','欧美','韩国','日本']
HOT_TV=[('综合','tv_hot'),('国产剧','tv_domestic'),('欧美剧','tv_american'),('日剧','tv_japanese'),('韩剧','tv_korean'),('动画','tv_animation'),('纪录片','tv_documentary')]
HOT_SHOW=[('综合','show_hot'),('国内','show_domestic'),('国外','show_foreign')]
RANKS=['热门','最新','豆瓣高分']

def load(path, default):
    try: return json.load(open(path))
    except Exception: return default

def save(path, obj):
    json.dump(obj, open(path,'w'), ensure_ascii=False, separators=(',',':'))

def git_push(msg):
    if os.environ.get('GIT_COMMIT') != '1': return
    run=lambda c: subprocess.run(c, shell=True, capture_output=True)
    run('git config user.name phbox-bot')
    run('git config user.email bot@users.noreply.github.com')
    run('git add data.json progress.json')
    run(f'git commit -m "{msg}"')
    r=run('git pull --rebase origin main && git push')
    print('push', r.returncode, flush=True)

req=0
def get(path, params):
    global req
    if req>=MAXREQ: raise SystemExit('limit')
    url=f'https://m.douban.com/rexxar/api/v2/{path}?'+urllib.parse.urlencode(params)
    r=urllib.request.Request(url, headers={'User-Agent':UA,'Referer':'https://m.douban.com/'})
    for _ in range(3):
        try:
            d=json.loads(urllib.request.urlopen(r,timeout=25).read()); req+=1
            time.sleep(GAP+random.random()*2)
            return d
        except Exception as e:
            time.sleep(60)
    req+=1
    return None

def parse(items):
    out=[]
    for it in items or []:
        sub=(it.get('card_subtitle') or '').split(' / ')
        out.append({'n':it.get('title',''),'r':str((it.get('rating') or {}).get('value','') or ''),
                    'p':(it.get('pic') or {}).get('normal',''),
                    'u':'https://movie.douban.com/subject/%s/'%it.get('id'),
                    'y':sub[0] if sub else '','a':sub[1] if len(sub)>1 else '','g':sub[2] if len(sub)>2 else ''})
    return out

def recent(path,cat,typ,maxitems=500):
    out=[]; start=0; total=None
    while len(out)<maxitems:
        d=get(f'subject/recent_hot/{path}', {'start':str(start),'limit':'20','category':cat,'type':typ,'ck':CK})
        if not d: break
        if total is None: total=d.get('total',0)
        items=d.get('items') or []
        if not items: break
        out+=parse(items); start+=20
        if total and start>=total: break
    return out

def recommend(path,tags,sel):
    d=get(f'{path}/recommend', {'refresh':'0','start':'0','count':'20','uncollect':'false','score_range':'0,10',
        'selected_categories':json.dumps(sel,ensure_ascii=False),'tags':tags,'ck':CK})
    return parse(d.get('items') if d else [])

def main():
    data=load(DATA, {'version':2,'classes':[],'items':{}})
    prog=load(PROG, {'done':{}})
    done=prog['done']
    data['classes']=[
      {'id':'hot_movie','name':'热播电影','filters':[{'key':'rank','name':'排序','values':RANKS},{'key':'area','name':'地区','values':HOT_AREAS}]},
      {'id':'hot_tv','name':'热播电视剧','filters':[{'key':'type','name':'分类','values':[n for n,_ in HOT_TV]}]},
      {'id':'hot_show','name':'热播综艺','filters':[{'key':'type','name':'分类','values':[n for n,_ in HOT_SHOW]}]},
      {'id':'movie_all','name':'全部电影','filters':[{'key':'genre','name':'类型','values':TYPES},{'key':'area','name':'地区','values':AREAS}]},
      {'id':'tv_all','name':'全部电视剧','filters':[{'key':'form','name':'类型','values':['全部']+TVFORMS},{'key':'area','name':'地区','values':AREAS}]},
    ]
    try:
        # 热播三页：每次刷新（15 请求）
        for area in HOT_AREAS:
            typ='全部' if area=='全部' else area
            items=recent('movie','热门',typ)
            if items:
                data['items'][f'hot_movie|热门|{area}']=items
                data['items'][f'hot_movie|最新|{area}']=sorted(items,key=lambda x:x['y'] or '0',reverse=True)
                data['items'][f'hot_movie|豆瓣高分|{area}']=sorted(items,key=lambda x:(float(x['r']) if x['r'] else 0),reverse=True)
        for name,typ in HOT_TV:
            items=recent('tv','tv',typ)
            if items: data['items'][f'hot_tv|{name}']=items
        for name,typ in HOT_SHOW:
            items=recent('tv','show',typ)
            if items: data['items'][f'hot_show|{name}']=items

        if SCOPE=='matrix':
            for g in TYPES:
                for a in AREAS:
                    key=f'movie_all|{g}|{a}'
                    if key in done: continue
                    tags=g if a=='全部' else f'{g},{a}'
                    items=recommend('movie', tags, {'类型':g,'地区':'' if a=='全部' else a})
                    if items:
                        data['items'][key]=items
                    done[key]=int(time.time())
                    save(DATA,data); save(PROG,prog)
                    if len(done)%50==0: git_push(f'partial {len(done)}')
            for f in TVFORMS:
                for a in AREAS:
                    key=f'tv_all|{f}|{a}'
                    if key in done: continue
                    tags=f if a=='全部' else f'{f},{a}'
                    items=recommend('tv', tags, {'类型':'','形式':f,'地区':'' if a=='全部' else a})
                    if items:
                        data['items'][key]=items
                    done[key]=int(time.time())
                    save(DATA,data); save(PROG,prog)
                    if len(done)%50==0: git_push(f'partial {len(done)}')
    except SystemExit:
        print('stopped at MAXREQ')
    finally:
        save(DATA,data); save(PROG,prog); git_push('final')
        print('items', sum(len(v) for v in data['items'].values()), 'combos', len(data['items']), 'done', len(done))

if __name__=='__main__': main()
