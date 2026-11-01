# Generates spec.json for the CoD MW4 launch clips (official Top Plays footage, no voice-over allowed).
import json
C=[555,0,810,1080]   # centre 3:4 of the 16:9 frame -> 1080x1440 window, crosshair stays centred
def clip(name,title,segs,payoff,texts,labels):
    return {"name":name,"source":"source.mp4","crop":C,"game_y":300,"segments":segs,"title":title,
            "texts":texts,"labels":labels,"payoff":payoff,"emojis":[],"mood":"hype","cta":""}
clips=[
 clip("mw4-rain-forest","No filter needed for *this*",
      [[51.0,52.4],[40.0,56.9]],51.2,
      [[40.2,3.0,"LOOK AT THE *RAIN*"],[43.5,3.5,"FOG IN THE *TREES*"],[47.5,3.5,"WATCH THE *CAR*..."]],
      [[51.2,"THAT *CAR FLIP*"]]),
 clip("mw4-industrial-double-v2","MW4 MP looks *unreal*",
      [[151.0,152.6],[138.5,166.3]],151.8,
      [[138.7,3.0,"INSIDE TO OUTSIDE"],[143.5,4.0,"THAT *LIGHTING*"],[155.5,2.5,"WAIT FOR IT..."]],
      [[151.8,"*DOUBLE KILL*"],[158.3,"LOOK AT THAT *HAZE*"]]),
 clip("mw4-bomb-glider","COD MP hits *different*",
      [[356.9,358.3],[343.9,360.2]],356.9,
      [[344.1,3.0,"THESE *STREETS*"],[348.5,4.0,"SUN + *SHADOWS*"],[352.8,3.5,"THEN THIS..."]],
      [[356.9,"*BOMB GLIDER*"]]),
 clip("mw4-snow-sniper","MW4 never looked so *good*",
      [[372.9,374.1],[370.8,384.0]],382.2,
      [[371.0,3.0,"SNIPING IN *SNOW*"],[375.5,3.0,"THE *DETAIL* THOUGH"],[379.5,2.5,"ONE MORE..."]],
      [[373.3,"*SCOPED IN*"]]),
 clip("mw4-street-details","The details speak for *themselves*",
      [[203.6,217.8]],None,
      [[203.8,3.0,"THESE *STREETS*"],[207.0,3.5,"EVERY *SIGN*"],[214.3,3.5,"SEEKER *DRONE*"]],
      []),
]
json.dump({"watermark":"","clips":clips},open("projects/cod-mw4/spec.json","w"),indent=1)
print(len(clips))
