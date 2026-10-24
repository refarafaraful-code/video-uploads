import json
C=[354,0,1212,1080]
CTA="PLAY PET SIM 99 ON ROBLOX"
def garg(name, src, teaser, build, cosmic, reveal, payoff, title, petname, build_txt, voice):
    teaser=round(payoff+0.3,2)
    segs=[[teaser,round(teaser+1.6,2)],[build[0],build[1]],[cosmic[0],cosmic[1],2.0],[reveal[0],reveal[1]+1.5]]
    return {"name":name,"source":src,"crop":C,"segments":segs,"title":title,
      "texts":[[teaser+0.05,1.5,"HOW DID THIS HAPPEN?"],[build[0]+0.3,3.0,build_txt],
               [build[1]-1.2,1.5,"*BOOM*"],[cosmic[0]+1.0,6.0,"WAIT FOR IT..."],
               [reveal[0]+0.4,3.0,"HERE IT COMES!"],[payoff,6.0,petname]],
      "payoff":payoff,"emojis":[[payoff+0.15,"😱"]],"mood":"hype","cta":CTA,
      "labels":[[payoff,petname]],
      "voice":{"file":f"campaign_audio/{voice[0]}.mp3","words":f"campaign_audio/{voice[0]}.json","segments":voice[1],"align":[voice[2],payoff]}}
clips=[
 garg("ps99-v3-gargantuan-1x1x1x1","../ps99-clip1/source.mp4",87.5,(58.0,64.5),(64.5,80.0),(80.0,92.5),87.5,
      "WATCH THIS PET SIM 99 HATCH","GARGANTUAN *1X1X1X1*!","IT KEEPS GETTING BIGGER...",("H",[[0,12.3]],8.7)),
 garg("ps99-v3-gargantuan-anime-agony","clip02.mp4",72.6,(43.5,48.6),(48.6,64.0),(64.0,78.0),72.5,
      "PET SIM 99: WAIT FOR THE END","GARGANTUAN *ANIME AGONY*!","IT KEEPS GETTING BIGGER...",("C",[[0,9.0],[11.3,12.6]],7.2)),
 garg("ps99-v3-gargantuan-aura-cat","clip04.mp4",73.2,(43.0,49.0),(49.0,65.0),(65.0,79.0),72.6,
      "THIS PET SIM 99 HATCH GOT HUGE","GARGANTUAN *AURA CAT*!","IT KEEPS GETTING BIGGER...",("F",[[0,11.3]],7.9)),
 garg("ps99-v3-gargantuan-black-balloon-cat","clip05.mp4",81.8,(50.0,57.0),(57.0,73.3),(73.3,86.5),81.5,
      "PET SIM 99 BLACK BALLOON CAT HATCH","GARGANTUAN *BLACK BALLOON CAT*!","IT KEEPS GETTING BIGGER...",("M",[[0,8.7],[10.0,13.1]],6.8)),
 garg("ps99-v3-gargantuan-capybara","clip07.mp4",76.8,(44.0,52.5),(52.5,68.3),(68.3,80.5),76.5,
      "A GARGANTUAN CAPYBARA IN PET SIM 99","GARGANTUAN *CAPYBARA*!","IT KEEPS GETTING BIGGER...",("A",[[0,6.9],[7.4,8.9]],4.2)),
]
# compilation: 4 hatches, output-time annotations computed from the segments
parts=[("clip13.mp4",19.0,23.6,26.2,24.25,"HUGE *ABYSSAL AXOLOTL*"),
       ("clip09.mp4",9.4,13.3,16.0,14.25,"TITANIC *ARCANE CAT*"),
       ("clip08.mp4",35.0,39.1,42.0,40.25,"TITANIC *ARCANE HALO CAT*"),
       ("clip06.mp4",41.8,46.6,48.7,46.75,"TITANIC *ANCIENT DRAGON*")]
segs=[[46.7,47.9,1.0,"clip06.mp4"]]; t=1.2; texts=[[0.05,1.15,"4 RARE HATCHES..."]]; pay=[]
for i,(src,a,b,c,p,nm) in enumerate(parts):
    segs.append([a,b,1.2,src]); texts.append([t+0.1,(b-a)/1.2-0.2,f"HATCH {i+1}/4..."]); t+=(b-a)/1.2
    segs.append([b,c,1.0,src]); pt=t+(p-b); pay.append(round(pt,3)); texts.append([round(pt,3),c-p,nm]); t+=c-b
clips.append({"name":"ps99-v3-4-rare-hatches","source":"clip06.mp4","crop":C,"segments":segs,"times":"output",
  "title":"HUGE OR TITANIC? PET SIM 99","texts":texts,"payoff":pay,"emojis":[[pay[-1]+0.3,"🐉"]],"mood":"hype","cta":CTA,
  "voice":{"file":"campaign_audio/K.mp3","words":"campaign_audio/K.json","segments":[[0,5.0]],"align":[2.8,pay[-1]]},
  "labels":[[p,t] for p,t in zip(pay,[x[5] for x in parts])]})
print(round(t,2))
json.dump({"watermark":"","clips":clips},open("/home/user/video-uploads/projects/ps99/spec.json","w"),indent=1,ensure_ascii=False)
