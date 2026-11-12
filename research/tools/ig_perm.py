import os,json,urllib.request,urllib.parse
out={}
def get(url):
    try:
        r=urllib.request.urlopen(url,timeout=20);return r.status,json.load(r)
    except urllib.error.HTTPError as e:
        try: body=json.load(e)
        except Exception: body={}
        return e.code,body
    except Exception as e: return 0,{'err':str(e)[:120]}
def scrub(d):
    if isinstance(d,dict): return {k:scrub(v) for k,v in d.items() if k not in('access_token',)}
    if isinstance(d,list): return [scrub(x) for x in d]
    return d
fb=os.environ.get('IG_ACCESS_TOKEN');ig=os.environ.get('IG_IGLOGIN_TOKEN') or os.environ.get('IG_LOGIN_TOKEN')
if fb:
    s,d=get('https://graph.facebook.com/v23.0/me/permissions?access_token='+urllib.parse.quote(fb))
    out['facebook_login_permissions']={'status':s,'granted':[p['permission'] for p in d.get('data',[]) if p.get('status')=='granted'],'declined':[p['permission'] for p in d.get('data',[]) if p.get('status')!='granted'],'error':(d.get('error') or {}).get('message')}
if ig:
    s,d=get('https://graph.instagram.com/v23.0/me?fields=user_id,username,account_type&access_token='+urllib.parse.quote(ig))
    out['instagram_login_me']={'status':s,'username':d.get('username'),'account_type':d.get('account_type'),'error':(d.get('error') or {}).get('message')}
    s,d=get('https://graph.instagram.com/v23.0/me/permissions?access_token='+urllib.parse.quote(ig))
    out['instagram_login_permissions']={'status':s,'data':scrub(d.get('data')),'error':(d.get('error') or {}).get('message')}
    s,d=get('https://graph.instagram.com/v23.0/me/media?fields=id,comments_count,media_product_type,timestamp&limit=20&access_token='+urllib.parse.quote(ig))
    media=d.get('data',[]);out['own_media']={'status':s,'count':len(media),'with_comments':sum(1 for m in media if m.get('comments_count')),'error':(d.get('error') or {}).get('message')}
    cm=[m for m in media if m.get('comments_count')]
    if cm:
        s,d=get(f"https://graph.instagram.com/v23.0/{cm[0]['id']}/comments?fields=id,timestamp&access_token="+urllib.parse.quote(ig))
        out['comments_read']={'status':s,'n':len(d.get('data',[])),'error':(d.get('error') or {}).get('message')}
    else:
        s,d=get(f"https://graph.instagram.com/v23.0/{media[0]['id']}/comments?fields=id&access_token="+urllib.parse.quote(ig)) if media else (0,{})
        out['comments_read']={'status':s,'n':len(d.get('data',[])) if isinstance(d,dict) else 0,'error':(d.get('error') or {}).get('message') if isinstance(d,dict) else None}
    s,d=get('https://graph.instagram.com/v23.0/me/conversations?platform=instagram&access_token='+urllib.parse.quote(ig))
    out['messages_conversations_read']={'status':s,'n':len(d.get('data',[])) if isinstance(d,dict) else 0,'error':(d.get('error') or {}).get('message') if isinstance(d,dict) else None}
json.dump(out,open('research/out/ig_perm.json','w'),ensure_ascii=False,indent=1);print(json.dumps(out,ensure_ascii=False,indent=1))
