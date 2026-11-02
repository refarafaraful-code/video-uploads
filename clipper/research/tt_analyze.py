import json, glob, sys, re, collections, statistics, datetime
rows = {}
for f in sorted(glob.glob(sys.argv[1] + '/b*.json')):
    d = json.load(open(f))
    for it in d['items']:
        st = it.get('stats') or it.get('statsV2') or {}
        def n(k):
            try: return int(st.get(k) or 0)
            except: return 0
        a = it.get('author') or {}; mu = it.get('music') or {}; vi = it.get('video') or {}
        rows[it['id']] = dict(id=it['id'], src=d['url'].split('/')[-1], author=a.get('uniqueId', '') if isinstance(a, dict) else str(a),
            followers=(it.get('authorStats') or {}).get('followerCount'), plays=n('playCount'), likes=n('diggCount'), comments=n('commentCount'),
            shares=n('shareCount'), saves=n('collectCount'), dur=vi.get('duration'), music=(mu.get('title') or '')[:50], music_author=(mu.get('authorName') or '')[:30],
            original=mu.get('original'), created=int(it.get('createTime') or 0), desc=(it.get('desc') or '').replace('\n', ' ')[:200],
            tags=[c.get('hashtagName') for c in (it.get('challenges') or []) if isinstance(c, dict)], ad=bool(it.get('isAd')) )
R = sorted(rows.values(), key=lambda r: -r['plays'])
json.dump(R, open(sys.argv[1] + '/all.json', 'w'), ensure_ascii=False)
print('videos', len(R))
now = max(r['created'] for r in R)
print('\nTOP 40 by plays:')
for r in R[:40]:
    age = (now - r['created']) / 86400
    er = (r['likes'] + r['comments'] + r['shares']) / max(r['plays'], 1) * 100
    print(f"{r['plays']:>11,} er{er:4.1f}% {r['dur']:>3}s {age:5.0f}d @{r['author'][:18]:<18} [{r['src'][:14]}] ♪{r['music'][:28]} | {r['desc'][:110]}")
D = [r['dur'] for r in R if r['dur']]
top = [r for r in R if r['plays'] >= 1_000_000]
print('\nduration median all', statistics.median(D), '| 1M+ videos', len(top), 'median dur', statistics.median([r['dur'] for r in top if r['dur']]) if top else '-')
buckets = collections.defaultdict(list)
for r in R:
    if r['dur']: buckets[min(r['dur'] // 10 * 10, 90)].append(r['plays'])
print('median plays by duration bucket:', {k: (len(v), int(statistics.median(v))) for k, v in sorted(buckets.items())})
tc = collections.Counter(t.lower() for r in R for t in r['tags'] if t)
tt = collections.Counter(t.lower() for r in top for t in r['tags'] if t)
print('\ntop hashtags all:', tc.most_common(30))
print('top hashtags 1M+:', tt.most_common(25))
mc = collections.Counter((r['music'], r['music_author']) for r in top if not r['original'])
print('\nnon-original music on 1M+:', mc.most_common(20))
print('original sound share: all', round(sum(1 for r in R if r['original']) / len(R) * 100), '% | 1M+', round(sum(1 for r in top if r['original']) / max(len(top), 1) * 100), '%')
