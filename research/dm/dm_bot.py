"""댓글 키워드 → 자료 DM(Private Reply) 자동 발송 — 실험 브랜치용.
기본은 보내지 않는 모드(--dry-run). 실제 발송은 --send 와 data/dm/ENABLED 파일이 모두 있어야 한다.

흐름: 내 게시물 목록 → 게시물별 댓글 → 키워드 일치 → (보낸 기록 확인) → 문구 생성 → 발송 또는 기록만.
Meta 조건(2026-11-12 확인): POST /{ig-user-id}/messages, recipient.comment_id, 댓글 작성 7일 안, 댓글당 1번.
필요 권한: Facebook 로그인 경로 instagram_basic + instagram_manage_comments + instagram_manage_messages + pages_read_engagement.
"""
import argparse, json, os, sys, time, datetime as dt, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, 'campaigns.json'), encoding='utf-8'))
STATE = os.path.join(HERE, 'state.json')
LOG = os.path.join(HERE, 'log.jsonl')
GRAPH = 'https://graph.facebook.com/v23.0'

def api(method, path, params=None, body=None):
    params = dict(params or {}); params['access_token'] = os.environ['IG_ACCESS_TOKEN']
    url = f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def load_comments(fixture):
    if fixture:
        return json.load(open(fixture, encoding='utf-8'))
    uid = os.environ['IG_USER_ID']
    out = []
    media = api('GET', f'{uid}/media', {'fields': 'id,timestamp', 'limit': 25}).get('data', [])
    for m in media:
        if m['id'] not in CFG['campaigns']:
            continue
        cs = api('GET', f"{m['id']}/comments", {'fields': 'id,text,timestamp,from,username', 'limit': 50}).get('data', [])
        for c in cs:
            out.append({'media_id': m['id'], 'comment_id': c['id'], 'text': c.get('text', ''), 'timestamp': c['timestamp'],
                        'user_id': (c.get('from') or {}).get('id'), 'username': c.get('username')})
    return out

def norm(s): return ''.join(s.split()).lower()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--fixture'); ap.add_argument('--send', action='store_true')
    a = ap.parse_args()
    live = a.send and os.path.exists(os.path.join(HERE, 'ENABLED'))
    state = json.load(open(STATE)) if os.path.exists(STATE) else {'done_comments': [], 'done_user_media': [], 'sent_today': {}}
    today = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=9)).strftime('%Y-%m-%d')
    sent_today = state['sent_today'].get(today, 0)
    now = dt.datetime.now(dt.timezone.utc)
    summary = {'checked': 0, 'matched': 0, 'planned': 0, 'sent': 0, 'skipped': {}, 'failed': 0}
    def skip(why): summary['skipped'][why] = summary['skipped'].get(why, 0) + 1
    for c in load_comments(a.fixture):
        summary['checked'] += 1
        camp = CFG['campaigns'].get(c['media_id'])
        if not camp: skip('캠페인 없는 게시물'); continue
        if not any(norm(k) in norm(c['text']) for k in camp['keywords']): skip('키워드 없음'); continue
        summary['matched'] += 1
        if c['comment_id'] in state['done_comments']: skip('이미 보낸 댓글'); continue
        key = f"{c.get('user_id')}:{c['media_id']}"
        if key in state['done_user_media']: skip('같은 사람·같은 게시물'); continue
        age = now - dt.datetime.fromisoformat(c['timestamp'].replace('+0000', '+00:00'))
        if age > dt.timedelta(days=6, hours=20): skip('7일 지남'); continue
        if c.get('username') == CFG['own_username']: skip('내 댓글'); continue
        if sent_today >= CFG['daily_cap']: skip('하루 상한'); continue
        text = CFG['template'].format(link=camp['link'], title=camp['title'])
        rec = {'at': now.isoformat(timespec='seconds'), 'media_id': c['media_id'], 'comment_id': c['comment_id'], 'chars': len(text), 'mode': 'live' if live else 'dry'}
        if live:
            try:
                r = api('POST', f"{os.environ['IG_USER_ID']}/messages", body={'recipient': {'comment_id': c['comment_id']}, 'message': {'text': text}})
                rec['ok'] = bool(r.get('message_id')); summary['sent'] += 1; sent_today += 1
            except Exception as e:
                rec['ok'] = False; rec['error'] = str(e)[:200]; summary['failed'] += 1
            time.sleep(CFG['gap_sec'])
        else:
            rec['preview'] = text; summary['planned'] += 1
        state['done_comments'].append(c['comment_id'])
        state['done_user_media'].append(key)
        with open(LOG, 'a', encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    state['sent_today'][today] = sent_today
    if live: json.dump(state, open(STATE, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
