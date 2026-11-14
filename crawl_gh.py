import os, json, time, random, urllib.request, urllib.parse, subprocess, sys

UA='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
CK='hyqv'
GAP=float(os.environ.get('GAP','5'))
MAXREQ=int(os.environ.get('MAXREQ','900'))

TYPES=['喜剧','爱情','动作','科幻','动画','悬疑','犯罪','惊悚','冒险','音乐','历史','奇幻','恐怖','战争','传记','歌舞','武侠','灾难','西部','纪录片','短片']
AREAS=['全部','华语','欧美','韩国','日本','中国大陆','美国','中国香港','中国台湾','英国','法国','德国','意大利','西班牙','印度','泰国','俄罗斯','加拿大','澳大利亚','爱尔兰','瑞典','巴西','丹麦']
YEARS=['全部','2020年代','2026','2025','2024','2023','2022','2021','2020','2019','2010年代','2000年代','90年代','80年代','70年代','60年代','更早']
TVFORMS=['全部','电视剧','综艺']
TVGENRES=['全部','喜剧','爱情','悬疑','动画','武侠','古装','家庭','犯罪','科幻','恐怖','历史','战争','动作','冒险','传记','剧情','奇幻','惊悚','灾难','歌舞','音乐']
PLATFORMS=['全部','腾讯视频','爱奇艺','优酷','湖南卫视','Netflix','HBO','BBC','NHK','CBS','NBC','tvN']
RANKS=['热门','最新','豆瓣高分']
HOT_AREAS=['全部','华语','欧美','韩国','日本']
HOT_TV=['综合','国产剧','欧美剧','日剧','韩剧','动画','纪录片']
HOT_SHOW=['综合','国内','国外']

def get(path, params, tries=3):
    url=f'https://m.douban.com/rexxar/api/v2/{path}?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url, headers={'User-Agent':UA,'Referer':'https://m.douban.com/'})
    for i in range(tries):
        try:
            d=json.loads(urllib.request.urlopen(req,timeout=25).read())
            return d, None
        except Exception as e:
            msg=str(e)[:60]
            if '403' in msg or '429' in msg:
                time.sleep(120); continue
            time.sleep(5); continue
    return None, 'fail'

def parse(items):
    out=[]
    for it in items:
        sub=(it.get('card_subtitle') or '').split(' / ')
        out.append({'n':it.get('title',''),'r':str((it.get('rating') or {}).get('value','') or ''),
                    'p':(it.get('pic') or {}).get('normal',''),
                    'u':'https://movie.douban.com/subject/%s/'%it.get('id'),
                    'y':sub[0] if sub else '','a':sub[1] if len(sub)>1 else '','g':sub[2] if len(sub)>2 else ''})
    return out

def recent(path, cat, typ, limit=20):
    d,err=get(f'subject/recent_hot/{path}', {'start':'0','limit':str(limit),'category':cat,'type':typ,'ck':CK})
    if err: return [], 'fail'
    return parse(d.get('items',[])), None

def recommend(path, tags, sel, limit=20):
    d,err=get(f'{path}/recommend', {'refresh':'0','start':'0','count':str(limit),'uncollect':'false',
        'score_range':'0,10','selected_categories':json.dumps(sel,ensure_ascii=False),'tags':tags,'ck':CK})
    if err: return [], 'fail'
    return parse(d.get('items',[])), None

def build(scope='stage1'):
    data={'version':2,'classes':[],'items':{}}
    data['classes']=[
      {'id':'hot_movie','name':'热播电影','filters':[
          {'key':'rank','name':'排序','values':RANKS},{'key':'area','name':'地区','values':HOT_AREAS}]},
      {'id':'hot_tv','name':'热播电视剧','filters':[{'key':'type','name':'分类','values':HOT_TV}]},
      {'id':'hot_show','name':'热播综艺','filters':[{'key':'type','name':'分类','values':HOT_SHOW}]},
      {'id':'movie_all','name':'全部电影','filters':[
          {'key':'genre','name':'类型','values':TYPES},{'key':'area','name':'地区','values':AREAS}]},
      {'id':'tv_all','name':'全部电视剧','filters':[
          {'key':'form','name':'类型','values':TVFORMS},{'key':'area','name':'地区','values':AREAS}]},
    ]
    req=0
    def tick():
        nonlocal req
        req+=1
        if req>MAXREQ: raise SystemExit('MAXREQ reached')
        time.sleep(GAP+random.random())

    # 热播三页（热门池）
    for area in HOT_AREAS:
        typ='全部' if area=='全部' else area
        items,err=recent('movie','热门',typ); tick()
        if not items: continue
        data['items'][f'hot_movie|热门|{area}']=items
        data['items'][f'hot_movie|最新|{area}']=sorted(items,key=lambda x:x['y'] or '0',reverse=True)
        data['items'][f'hot_movie|豆瓣高分|{area}']=sorted(items,key=lambda x:(float(x['r']) if x['r'] else 0),reverse=True)
    for name,typ in [('综合','tv_hot'),('国产剧','tv_domestic'),('欧美剧','tv_american'),('日剧','tv_japanese'),('韩剧','tv_korean'),('动画','tv_animation'),('纪录片','tv_documentary')]:
        items,err=recent('tv','tv',typ); tick()
        if items: data['items'][f'hot_tv|{name}']=items
    for name,typ in [('综合','show_hot'),('国内','show_domestic'),('国外','show_foreign')]:
        items,err=recent('tv','show',typ); tick()
        if items: data['items'][f'hot_show|{name}']=items

    if scope=='matrix':
        # 全部电影：类型 × 地区
        for g in TYPES:
            for a in AREAS:
                if a=='全部':
                    tags=g; sel={'类型':g,'地区':''}
                else:
                    tags=f'{g},{a}'; sel={'类型':g,'地区':a}
                items,err=recommend('movie', tags, sel); tick()
                if items: data['items'][f'movie_all|{g}|{a}']=items
        # 全部电视剧：形式 × 地区
        for f in TVFORMS:
            if f=='全部': continue
            for a in AREAS:
                tags=(f if a=='全部' else f',{a}')
                sel={'类型':'','形式':f,'地区':'' if a=='全部' else a}
                items,err=recommend('tv', tags, sel); tick()
                if items: data['items'][f'tv_all|{f}|{a}']=items
    return data

if __name__=='__main__':
    scope=os.environ.get('SCOPE','hot')
    data=build(scope)
    out=os.environ.get('OUT','data.json')
    json.dump(data, open(out,'w'), ensure_ascii=False, separators=(',',':'))
    print('items', sum(len(v) for v in data['items'].values()), 'combos', len(data['items']))
