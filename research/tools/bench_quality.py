"""Cover features of benchmark top reels/carousels (features only; images are not saved)."""
import json,sys,datetime as dt
sys.path.insert(0,'scripts')
import collect,bench_features
collect.use_backend('benchmark')
ACC=['grappt_','ai.trend.kr','adu.aihub','ai_newpd','gpt_haterz']
cut=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=120)).isoformat()
out={}
for a in ACC:
    try: posts,info=collect._discover(a,2,50)
    except Exception as e: out[a]={'error':str(e)[:120]};continue
    rec=[p for p in posts if p['timestamp']>=cut]
    eng=lambda p:(p.get('like_count') or 0)+(p.get('comments_count') or 0)
    rows=[]
    for kind,flt in (('reel',lambda p:p.get('media_product_type')=='REELS'),('carousel',lambda p:p.get('media_type')=='CAROUSEL_ALBUM')):
        top=sorted([p for p in rec if flt(p)],key=eng,reverse=True)[:3]
        for p in top:
            url=p.get('thumbnail_url') or p.get('media_url')
            try: f=bench_features._image_features(url) if url else {}
            except Exception as e: f={'error':str(e)[:80]}
            f.pop('cover_text',None)
            rows.append({'kind':kind,'date':p['timestamp'][:10],'eng':eng(p),'slides':p.get('slides'),'caption_chars':len(p.get('caption') or ''),**f})
    out[a]={'followers':info.get('followers_count'),'n_recent':len(rec),'reel_share_recent':round(sum(p.get('media_product_type')=='REELS' for p in rec)/max(len(rec),1),2),'top':rows}
json.dump(out,open('research/out/bench_quality.json','w'),ensure_ascii=False,indent=1);print(json.dumps(out,ensure_ascii=False)[:2000])
