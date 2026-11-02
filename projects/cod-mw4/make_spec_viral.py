# "Viral" batch for the CoD MW4 campaign, built from the research in research.md (music-synced edits,
# comment prompts, slow-motion graphics). Kill times verified on 4 fps strips.
import json
C=[555,0,810,1080]
BAR=4*60/140          # hype bed: 140 bpm, a cut every 4 beats lands on an 808 hit
HALF=BAR/2
base=dict(source="source.mp4",crop=C,game_y=300,cta="",emojis=[],mood="hype",montage=True,times="output",payoff=None,labels=[])
clips=[]
# 1. beat-synced kill montage: every kill lands half a bar into its segment (on the beat), cuts on the bar
kills=[51.3,95.0,199.75,373.3,152.2,356.75,280.65]
segs=[[k-HALF,k+HALF] for k in kills]+[[35.15-HALF,35.15+2.0]]
hits=[round(i*BAR+HALF,3) for i in range(len(segs))]
clips.append({**base,"name":"mw4-beat-montage","title":"Every MW4 kill on the *beat*","segments":segs,
  "bed_db":-11,"beat_hits":hits,"texts":[[round(7*BAR,3),2.9,"BEST ONE? *1-8*"]]})
# 2. rate this play: one full play, comment prompt at the end
clips.append({**base,"name":"mw4-rate-this-play-v2","montage":False,"title":"Rate this MW4 play *1-10*",
  "segments":[[273.3,284.2,1.0]],"times":"source","texts":[[281.4,2.8,"COMMENT YOUR *RATING*"]]})
# 3. slow motion graphics: normal lead-in, then the moment at 0.4-0.5x
s3=[[50.0,50.6,1.0],[50.6,52.6,0.4],[372.9,373.9,0.4],[356.5,357.7,0.5],[94.5,95.5,0.5],[280.1,281.1,0.5]]
clips.append({**base,"name":"mw4-slow-motion","title":"MW4 in *slow motion*","segments":s3,"bed_db":-13,"texts":[]})
json.dump({"watermark":"","clips":clips},open("projects/cod-mw4/spec_viral.json","w"),indent=1)
for c in clips: print(c["name"], round(sum((s[1]-s[0])/(s[2] if len(s)>2 else 1) for s in c["segments"]),2))
