# Creative batch for the CoD MW4 campaign (owner asked for funnier / more creative clips from the same footage).
import json
C=[555,0,810,1080]
def outtimes(segs, pairs):
    """map (segment index, source time) -> output time"""
    acc=[0.0]
    for s in segs: acc.append(acc[-1]+(s[1]-s[0])/(s[2] if len(s)>2 else 1))
    return [round(acc[i]+(t-segs[i][0])/(segs[i][2] if len(segs[i])>2 else 1),3) for i,t in pairs]
clips=[]
# 1. shotgun meme: joke framing + the player's own words + the game's DOUBLE/TRIPLE KILL banners
clips.append({"name":"mw4-shotgun-mains","source":"source.mp4","crop":C,"game_y":300,"mood":"hype","cta":"","emojis":[],
 "segments":[[34.4,35.8],[15.0,37.5]],"payoff":34.64,
 "title":"Shotgun mains in *MW4*:",
 "texts":[[15.1,3.2,"ME: \"I'LL PLAY IT *SLOW*\""],[18.4,3.0,"ALSO ME:"],[23.8,1.2,"\"ALRIGHT, LET'S GO\""],
          [27.5,1.3,"\"I'M DOING IT\""],[28.8,2.4,"\"I'M LITERALLY *BUNNY HOPPING*\""]],
 "labels":[[24.64,"*DOUBLE KILL*"],[34.64,"*TRIPLE KILL*"]]})
# 2. "was that a triple?" -> meanwhile a play the game itself calls a TRIPLE KILL
s2=[[367.1,369.7],[361.4,369.7],[270.0,284.2]]
q1,q2,q3,m,tk=outtimes(s2,[(0,367.2),(0,368.2),(1,367.2),(2,270.1),(2,280.4)])
clips.append({"name":"mw4-was-that-a-triple","source":"source.mp4","crop":C,"game_y":300,"mood":"hype","cta":"","emojis":[],
 "segments":s2,"times":"output","payoff":tk,
 "title":"\"Was that a *triple*?\"",
 "texts":[[q1,1.0,"\"OH MY GOD,\""],[q2,1.4,"\"WAS THAT A *TRIPLE*?\""],[q3,1.0,"\"OH MY GOD,\""],[q3+1.0,1.6,"\"WAS THAT A *TRIPLE*?\""],
          [m,3.5,"MEANWHILE, THIS PLAYER:"]],
 "labels":[[m,"Meanwhile..."],[tk,"*TRIPLE KILL*"]]})
# 3. pick one: three finalist plays, comment 1, 2 or 3
s3=[[333.0,340.5],[94.3,99.6],[194.2,202.4]]
a,b,c,end=outtimes(s3,[(0,333.0),(1,94.3),(2,194.2),(2,199.0)])
clips.append({"name":"mw4-pick-one-v2","montage":True,"source":"source.mp4","crop":C,"game_y":300,"mood":"hype","cta":"","emojis":[],
 "segments":s3,"times":"output","payoff":None,
 "title":"Which MW4 play *wins*?",
 "texts":[[a+0.1,3.0,"WHICH ONE IS BEST?"],[end,4.0,"COMMENT *1, 2 OR 3*"]],
 "labels":[[a,"Play *1*"],[b,"Play *2*"],[c,"Play *3*"]]})
# 4. map vibe check: 2.5 s per environment
shots=[(42.0,"RAINY *FOREST*"),(258.3,"SNOWY *CITY*"),(205.0,"CITY *ALLEYS*"),(351.5,"SUNNY *STREETS*"),
       (143.0,"INDUSTRIAL *YARD*"),(374.5,"SNOW *BASE*"),(13.5,"COLORFUL *ALLEYS*"),(106.0,"OLD *TOWN*")]
s4=[[t,t+2.5] for t,_ in shots]
ot=outtimes(s4,[(i,t) for i,(t,_) in enumerate(shots)])
clips.append({"name":"mw4-map-vibe-check-v2","montage":True,"source":"source.mp4","crop":C,"game_y":300,"mood":"hype","cta":"","emojis":[],
 "segments":s4,"times":"output","payoff":None,
 "title":"MW4 map *vibe check*",
 "texts":[[t+0.05,2.4,n] for t,(_,n) in zip(ot,shots)],"labels":[]})
json.dump({"watermark":"","clips":clips},open("projects/cod-mw4/spec_creative.json","w"),indent=1,ensure_ascii=False)
print([ (c["name"], round(sum((s[1]-s[0])/(s[2] if len(s)>2 else 1) for s in c["segments"]),1)) for c in clips])
