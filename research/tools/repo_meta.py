import json,os,urllib.request
out=[]
H={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json'}
for r in open('research/tools/repos.txt').read().split():
    try:
        d=json.load(urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/'+r,headers=H),timeout=20))
        out.append({'repo':d['full_name'],'stars':d['stargazers_count'],'license':(d.get('license') or {}).get('spdx_id'),'pushed':d['pushed_at'][:10],'archived':d['archived'],'desc':(d.get('description') or '')[:140],'lang':d.get('language')})
    except Exception as e: out.append({'repo':r,'error':str(e)[:80]})
json.dump(out,open('research/out/repo_meta.json','w'),ensure_ascii=False,indent=1)
print(len(out))
