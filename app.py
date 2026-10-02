import argparse, json, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
THEMES=json.loads((ROOT/'themes.json').read_text(encoding='utf-8'))['themes']
INDEX=json.loads((ROOT/'content_index.json').read_text(encoding='utf-8'))

FONT_PATHS={
 'regular':['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','C:/Windows/Fonts/arial.ttf'],
 'bold':['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','C:/Windows/Fonts/arialbd.ttf'],
 'italic':['/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf','C:/Windows/Fonts/ariali.ttf'],
}

def font(size,bold=False,italic=False):
    key='italic' if italic else ('bold' if bold else 'regular')
    for p in FONT_PATHS[key]:
        if os.path.exists(p): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def rgb(h):
    h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def rgba(h,a=255): return (*rgb(h),a)

def wrap(d,text,f,maxw):
    words=str(text).split(); lines=[]; cur=''
    for w in words:
        cand=(cur+' '+w).strip()
        if d.textbbox((0,0),cand,font=f)[2] <= maxw: cur=cand
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines or ['']

def draw_wrapped(d,text,xy,f,fill,maxw,spacing=8,max_lines=None):
    lines=wrap(d,text,f,maxw)
    if max_lines: lines=lines[:max_lines]
    x,y=xy
    for line in lines:
        d.text((x,y),line,font=f,fill=fill); y += f.size+spacing
    return y

def card(im,box,fill,outline=None,r=34,shadow=True,width=3):
    x1,y1,x2,y2=box
    if shadow:
        sh=Image.new('RGBA',im.size,(0,0,0,0)); sd=ImageDraw.Draw(sh)
        sd.rounded_rectangle((x1+8,y1+12,x2+8,y2+12),radius=r,fill=(0,0,0,32))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width if outline else 1)

def pill(d,box,text,fill,text_fill,outline=None,size=22):
    d.rounded_rectangle(box,radius=(box[3]-box[1])//2,fill=fill,outline=outline,width=2 if outline else 1)
    d.text((box[0]+18,box[1]+(box[3]-box[1]-size)//2-2),text,font=font(size,True),fill=text_fill)

def icon(d,kind,cx,cy,size,t):
    a=rgba(t['accent']); a2=rgba(t['accent2']); dark=rgba(t['dark']); white=rgba('#FFFFFF')
    if kind=='clock':
        d.ellipse((cx-size,cy-size,cx+size,cy+size),fill=a,outline=dark,width=5); d.ellipse((cx-size*.72,cy-size*.72,cx+size*.72,cy+size*.72),fill=white)
        d.line((cx,cy,cx,cy-size*.48),fill=dark,width=6); d.line((cx,cy,cx+size*.38,cy+size*.15),fill=dark,width=6); d.ellipse((cx-6,cy-6,cx+6,cy+6),fill=dark)
    elif kind=='code':
        d.rounded_rectangle((cx-size,cy-size*.72,cx+size,cy+size*.72),radius=18,fill=dark,outline=a,width=4)
        d.text((cx-size*.55,cy-size*.42),'</>',font=font(int(size*.72),True),fill=a2)
    elif kind=='bug':
        d.ellipse((cx-size*.55,cy-size*.5,cx+size*.55,cy+size*.5),fill=a,outline=dark,width=4)
        for s in (-1,1):
            d.line((cx+s*size*.5,cy-size*.25,cx+s*size*.9,cy-size*.5),fill=dark,width=5)
            d.line((cx+s*size*.5,cy,cx+s*size*.95,cy),fill=dark,width=5)
            d.line((cx+s*size*.5,cy+size*.25,cx+s*size*.9,cy+size*.5),fill=dark,width=5)
    elif kind=='brain':
        d.ellipse((cx-size*.8,cy-size*.65,cx,cy+size*.65),fill=a2,outline=dark,width=4); d.ellipse((cx,cy-size*.65,cx+size*.8,cy+size*.65),fill=a,outline=dark,width=4)
    elif kind=='bolt':
        d.polygon([(cx-size*.15,cy-size),(cx+size*.55,cy-size*.12),(cx+size*.12,cy-size*.12),(cx+size*.35,cy+size),(cx-size*.55,cy+size*.1),(cx-size*.1,cy+size*.1)],fill=a2,outline=dark)
    elif kind=='shield':
        d.polygon([(cx,cy-size),(cx+size*.75,cy-size*.55),(cx+size*.6,cy+size*.45),(cx,cy+size),(cx-size*.6,cy+size*.45),(cx-size*.75,cy-size*.55)],fill=a,outline=dark)
        d.line((cx-size*.28,cy,cx-size*.05,cy+size*.25,cx+size*.4,cy-size*.28),fill=white,width=7,joint='curve')
    elif kind=='light':
        d.ellipse((cx-size*.65,cy-size*.75,cx+size*.65,cy+size*.35),fill=a2,outline=dark,width=4); d.line((cx-size*.25,cy+size*.45,cx+size*.25,cy+size*.45),fill=dark,width=6)
    elif kind=='science':
        d.polygon([(cx-size*.45,cy-size*.65),(cx+size*.45,cy-size*.65),(cx+size*.2,cy-size*.15),(cx+size*.7,cy+size*.65),(cx-size*.7,cy+size*.65),(cx-size*.2,cy-size*.15)],fill=a2,outline=dark)
    elif kind=='scale':
        d.line((cx,cy-size*.8,cx,cy+size*.7),fill=dark,width=6); d.line((cx-size*.65,cy-size*.45,cx+size*.65,cy-size*.45),fill=dark,width=6)
        d.line((cx-size*.55,cy-size*.4,cx-size*.8,cy+size*.2),fill=a,width=4); d.line((cx+size*.55,cy-size*.4,cx+size*.8,cy+size*.2),fill=a,width=4)
        d.arc((cx-size*.95,cy+size*.05,cx-size*.25,cy+size*.55),0,180,fill=a,width=4); d.arc((cx+size*.25,cy+size*.05,cx+size*.95,cy+size*.55),0,180,fill=a,width=4)
    elif kind=='target':
        for r,c in [(size,a),(size*.72,white),(size*.42,a2)]: d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=c,outline=dark,width=3)
    elif kind=='check':
        d.ellipse((cx-size,cy-size,cx+size,cy+size),fill=a,outline=dark,width=4); d.line((cx-size*.45,cy,cx-size*.08,cy+size*.35,cx+size*.55,cy-size*.38),fill=white,width=8,joint='curve')
    elif kind=='book':
        d.rounded_rectangle((cx-size,cy-size*.7,cx-size*.05,cy+size*.7),radius=10,fill=a,outline=dark,width=4)
        d.rounded_rectangle((cx+size*.05,cy-size*.7,cx+size,cy+size*.7),radius=10,fill=a2,outline=dark,width=4)
        d.line((cx,cy-size*.65,cx,cy+size*.62),fill=dark,width=4)

LAYOUTS={
 'daily_challenge':('15 SECOND CHALLENGE','clock','No searching. Your turn.'),
 'crack_the_code':('CRACK THE CODE','code','Decode it before the timer ends.'),
 'ai_detective':('AI DETECTIVE','target','Find the answer that does not belong.'),
 'predict_the_code':('PREDICT THE CODE','code','Run it in your head. No compiler needed.'),
 'spot_the_mistake':('SPOT THE MISTAKE','bug','Find the exact line or step that breaks.'),
 'logic_puzzle':('LOGIC PUZZLE','brain','Look for the rule before choosing.'),
 'tech_tip':('60-SECOND TECH TIP','bolt','One useful idea you can use today.'),
 'build_it':('BUILD IT','code','Turn the idea into a tiny working project.'),
 'ai_challenge':('AI CHALLENGE','brain','Try it, verify it, improve it.'),
 'this_or_that':('THIS OR THAT','scale','Choose your approach and explain the trade-off.'),
 'tech_explained':('TECH EXPLAINED','light','A complex idea in simple words.'),
 'weekly_mission':('WEEKLY MISSION','target','Build something small. Learn something real.'),
 'science_challenge':('SCIENCE CHALLENGE','science','Use the evidence. Then explain why.'),
 'cyber_safety':('CYBER SAFETY','shield','Pause. Check. Protect.'),
 'learn_60_seconds':('LEARN IN 60 SECONDS','book','One concept. One minute. One useful takeaway.'),
 'weekly_result':('WEEKLY RESULT','check','Answer reveal + the key idea to remember.'),
}
# Fixed base theme per template; record index then cycles through all 10 themes.
THEME_BASE={k:i+1 for i,k in enumerate(LAYOUTS)}

def theme_for(theme_number):
    return dict(THEMES[(theme_number-1)%len(THEMES)],theme_number=((theme_number-1)%len(THEMES))+1)

def theme_for_content(kind,index):
    base=THEME_BASE.get(kind,1)
    return theme_for(((base-1 + max(0,index-1)) % len(THEMES))+1)

def load_item(kind,index):
    meta=INDEX['content'][kind]
    d=json.loads((ROOT/meta['file']).read_text(encoding='utf-8'))
    items=d.get('items') or d.get('challenges')
    item=dict(items[(index-1)%len(items)])
    if kind=='daily_challenge':
        item['prompt']=item.get('question',item.get('prompt',''))
    item['content_type']=kind
    return item

def _header(im,d,left,right,title,ico,tagline,kind,sequence,t):
    W,H=im.size
    fbrand=font(38,True); fsub=font(18,True)
    d.text((left,70),'SMART LEARNING LAB',font=fbrand,fill=rgba(t['text']))
    d.text((left,118),'L E A R N   •   P R A C T I C E   •   G R O W',font=fsub,fill=rgba(t['accent']))
    # compact book mark
    d.rounded_rectangle((left-62,60,left-2,124),radius=12,fill=rgba(t['accent']))
    d.polygon([(left-53,70),(left-11,70),(left-32,92)],fill=rgba('#FFFFFF'))
    d.text((right-400,72),title,font=font(38,True),fill=rgba(t['accent']))
    d.line((right-400,122,right-160,122),fill=rgba(t['accent']),width=5)
    # hero is intentionally consistent brand, but body layout is template-specific
    card(im,(left,155,right,375),rgba(t['accent']),None,46,False); d=ImageDraw.Draw(im)
    d.rounded_rectangle((left+22,175,right-18,393),radius=42,fill=rgba(t['dark']))
    icon(d,ico,left+105,275,78,t)
    d.text((left+190,198),title,font=font(52,True),fill=rgba('#FFFFFF'))
    draw_wrapped(d,tagline,(left+190,275),font(27,False,True),rgba(t['accent2']),right-left-230,6,2)
    pill(d,(left,425,left+370,485),f'DAILY CONTENT  #{sequence:04d}',rgba('#FFFFFF'),rgba(t['text']),rgba(t['border']),20)
    pill(d,(right-290,425,right,485),kind.replace('_',' ').upper()[:20],rgba(t['accent']),rgba('#FFFFFF'),None,19)

def _answer_grid(im,d,left,right,y,item,t,label='CHALLENGE'):
    card(im,(left,y,right,y+225),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
    pill(d,(left+28,y+24,left+310,y+70),label,rgba(t['soft']),rgba(t['accent']),None,19)
    draw_wrapped(d,item['prompt'],(left+32,y+86),font(42,True),rgba(t['text']),right-left-64,7,3)
    oy=y+250; gap=20; h=108; colw=(right-left-gap)//2
    for idx,(letter,val) in enumerate(list(item.get('options',{}).items())[:4]):
        row=idx//2; col=idx%2; x=left+col*(colw+gap); yy=oy+row*(h+18)
        card(im,(x,yy,x+colw,yy+h),rgba(t['surface']),rgba(t['border']),28,True); d=ImageDraw.Draw(im)
        d.ellipse((x+22,yy+22,x+82,yy+82),fill=rgba(t['accent']))
        d.text((x+40,yy+32),letter,font=font(25,True),fill=rgba('#FFFFFF'))
        draw_wrapped(d,str(val),(x+100,yy+29),font(27,True),rgba(t['text']),colw-125,4,2)
    return oy+2*(h+18)+10

def _footer(im,d,left,right,item,kind,t):
    W,H=im.size; fy=H-285
    card(im,(left,fy,right,fy+118),rgba(t['surface2']),None,28,False); d=ImageDraw.Draw(im)
    d.text((left+28,fy+22),f"⏱ {item.get('time_limit_seconds',30)} SEC",font=font(23,True),fill=rgba(t['accent']))
    d.text((right-280,fy+22),str(item.get('difficulty','Medium')).upper(),font=font(23,True),fill=rgba(t['text']))
    d.text((left+28,fy+66),item.get('cta','Comment your answer • Tag a friend • Share').upper(),font=font(20,True),fill=rgba(t['text']))
    d.text((left,fy+145),'Small Questions • Big Progress',font=font(30,True,True),fill=rgba(t['accent']))
    d.text((right-390,fy+150),f"THEME {t['theme_number']}/10 • {t['name'].upper()}",font=font(17,True),fill=rgba(t['muted']))
    if item.get('answer') and kind in {'weekly_result','crack_the_code','predict_the_code','spot_the_mistake','logic_puzzle','science_challenge','cyber_safety','ai_detective'}:
        d.text((left,fy+190),'ANSWER REVEALED IN THE CAPTION / NEXT POST',font=font(16,True),fill=rgba(t['muted']))

def render(item,kind,sequence_number,theme_number=None):
    W,H=CFG['image']['width'],CFG['image']['height']; t=theme_for(theme_number) if theme_number else theme_for_content(kind,sequence_number)
    im=Image.new('RGBA',(W,H),rgba(t['background'])); d=ImageDraw.Draw(im)
    # Decorative theme shapes, deterministic rather than random.
    for x,y,r,c,a in [(0,185,165,t['accent'],28),(W,150,180,t['accent2'],25),(W,H-160,190,t['accent'],20),(-20,H-250,175,t['accent2'],18)]:
        d.ellipse((x-r,y-r,x+r,y+r),fill=rgba(c,a))
    margin=60; left,right=105,W-105
    card(im,(margin,28,W-margin,H-28),rgba(t['surface']),rgba(t['border']),46,True); d=ImageDraw.Draw(im)
    title,ico,tagline=LAYOUTS[kind]
    _header(im,d,left,right,title,ico,tagline,kind,sequence_number,t)
    y=520

    # 1) Core challenge formats: distinct 2x2 answer UX.
    if kind in {'daily_challenge','crack_the_code','logic_puzzle','science_challenge','cyber_safety'}:
        bottom=_answer_grid(im,d,left,right,y,item,t,'YOUR 15-SECOND CHALLENGE' if kind=='daily_challenge' else item.get('kicker','YOUR CHALLENGE'))
        if kind=='science_challenge':
            pill(d,(left,bottom+8,left+270,bottom+56),'FORMULA FIRST',rgba(t['soft']),rgba(t['accent']),None,18)
        if kind=='cyber_safety':
            pill(d,(right-300,bottom+8,right,bottom+56),'PAUSE • CHECK • PROTECT',rgba(t['soft']),rgba(t['accent']),None,17)

    # 2) AI Detective: evidence board with 3 candidates and a red/green clue rail.
    elif kind=='ai_detective':
        card(im,(left,y,right,y+190),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
        pill(d,(left+28,y+24,left+300,y+70),'CASE FILE',rgba(t['soft']),rgba(t['accent']),None,19)
        draw_wrapped(d,item['prompt'],(left+32,y+88),font(37,True),rgba(t['text']),right-left-64,7,3)
        cy=y+220; opts=list(item.get('options',{}).items()); gap=18; h=105
        for i,(letter,val) in enumerate(opts[:3]):
            yy=cy+i*(h+14); card(im,(left,yy,right,yy+h),rgba(t['surface2'] if i%2 else t['surface']),rgba(t['border']),25,True); d=ImageDraw.Draw(im)
            d.ellipse((left+22,yy+22,left+82,yy+82),fill=rgba(t['accent'])); d.text((left+41,yy+31),letter,font=font(24,True),fill=rgba('#FFFFFF'))
            draw_wrapped(d,val,(left+102,yy+24),font(25,True),rgba(t['text']),right-left-135,4,2)
        bottom=cy+3*(h+14)+8

    # 3) Code prediction: actual code editor panel + output choices.
    elif kind=='predict_the_code':
        card(im,(left,y,right,y+255),rgba(t['dark']),rgba(t['accent']),30,True); d=ImageDraw.Draw(im)
        pill(d,(left+25,y+22,left+290,y+68),'CODE EDITOR',rgba(t['accent']),rgba('#FFFFFF'),None,18)
        code=item.get('code','')
        draw_wrapped(d,code,(left+28,y+90),font(26,False),rgba('#FFFFFF'),right-left-56,8,6)
        bottom=_answer_grid(im,d,left,right,y+285,item,t,'WHAT WILL IT PRINT?')

    # 4) Spot the mistake: error-focused red line with correction panel.
    elif kind=='spot_the_mistake':
        card(im,(left,y,right,y+220),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
        pill(d,(left+28,y+24,left+300,y+70),'ERROR HUNT',rgba(t['soft']),rgba(t['accent']),None,19)
        draw_wrapped(d,item['prompt'],(left+32,y+88),font(38,True),rgba(t['text']),right-left-64,7,3)
        d.line((left+40,y+175,right-40,y+175),fill=rgba(t['accent']),width=6)
        bottom=_answer_grid(im,d,left,right,y+245,item,t,'WHICH PART IS WRONG?')

    # 5) Tech tip: one big tip card + 3 action chips.
    elif kind=='tech_tip':
        card(im,(left,y,right,y+340),rgba(t['surface']),rgba(t['border']),38,True); d=ImageDraw.Draw(im)
        pill(d,(left+28,y+25,left+300,y+72),'SAVE THIS TIP',rgba(t['soft']),rgba(t['accent']),None,19)
        draw_wrapped(d,item['prompt'],(left+34,y+95),font(39,True),rgba(t['text']),right-left-68,7,3)
        draw_wrapped(d,item.get('tip',''),(left+34,y+220),font(27,False),rgba(t['muted']),right-left-68,6,4)
        bottom=y+365
        for i,txt in enumerate(['READ','TRY','SAVE']):
            x=left+i*255; pill(d,(x,bottom,x+225,bottom+58),txt,rgba(t['accent']),rgba('#FFFFFF'),None,18)

    # 6) Build It: project brief, steps, output.
    elif kind=='build_it':
        card(im,(left,y,right,y+210),rgba(t['dark']),rgba(t['accent']),34,True); d=ImageDraw.Draw(im)
        pill(d,(left+28,y+24,left+290,y+70),'MINI PROJECT',rgba(t['accent']),rgba('#FFFFFF'),None,19)
        draw_wrapped(d,item['prompt'],(left+32,y+90),font(34,True),rgba('#FFFFFF'),right-left-64,7,3)
        bottom=y+240
        steps=['PLAN','BUILD','TEST']
        for i,step in enumerate(steps):
            yy=bottom+i*90; d.ellipse((left+25,yy,left+85,yy+60),fill=rgba(t['accent2'])); d.text((left+43,yy+15),str(i+1),font=font(22,True),fill=rgba(t['dark']))
            d.text((left+110,yy+10),step,font=font(23,True),fill=rgba(t['accent']))
            if i==0: draw_wrapped(d,'Define the smallest working version.',(left+110,yy+40),font(18),rgba(t['muted']),right-left-160,3,1)
            elif i==1: draw_wrapped(d,'Implement one feature at a time.',(left+110,yy+40),font(18),rgba(t['muted']),right-left-160,3,1)
            else: draw_wrapped(d,'Check normal, edge, and invalid cases.',(left+110,yy+40),font(18),rgba(t['muted']),right-left-160,3,1)
        bottom+=300
        card(im,(left,bottom-5,right,bottom+150),rgba(t['surface2']),None,26,False); d=ImageDraw.Draw(im); draw_wrapped(d,item.get('task',''),(left+28,bottom+22),font(24),rgba(t['text']),right-left-56,6,5)

    # 7) AI Challenge: prompt builder card + verify checklist.
    elif kind=='ai_challenge':
        card(im,(left,y,right,y+240),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
        pill(d,(left+28,y+24,left+340,y+70),'PROMPT TO TRY',rgba(t['soft']),rgba(t['accent']),None,19)
        draw_wrapped(d,item['prompt'],(left+32,y+90),font(36,True),rgba(t['text']),right-left-64,7,4)
        bottom=y+270
        for i,txt in enumerate(['ASK','VERIFY','REWRITE']):
            yy=bottom+i*86; card(im,(left,yy,right,yy+68),rgba(t['surface2']),rgba(t['border']),24,False); d=ImageDraw.Draw(im); d.ellipse((left+18,yy+14,left+64,yy+60),fill=rgba(t['accent'])); d.text((left+33,yy+22),str(i+1),font=font(18,True),fill=rgba('#FFFFFF')); d.text((left+84,yy+18),txt,font=font(22,True),fill=rgba(t['text']))
        bottom+=270

    # 8) This or That: split-screen comparison.
    elif kind=='this_or_that':
        comp=item.get('compare',{})
        card(im,(left,y,right,y+180),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
        draw_wrapped(d,comp.get('question',item['prompt']),(left+32,y+34),font(35,True),rgba(t['text']),right-left-64,7,3)
        bottom=y+205; gap=24; cw=(right-left-gap)//2
        for j,key in enumerate(['A','B']):
            x=left+j*(cw+gap); card(im,(x,bottom,x+cw,bottom+230),rgba(t['surface']),rgba(t['accent']),30,True); d=ImageDraw.Draw(im)
            d.ellipse((x+24,bottom+22,x+84,bottom+82),fill=rgba(t['accent'])); d.text((x+43,bottom+32),key,font=font(24,True),fill=rgba('#FFFFFF'))
            draw_wrapped(d,comp.get(key,''),(x+28,bottom+105),font(30,True),rgba(t['text']),cw-56,6,4)
        bottom+=255
        pill(d,(left,bottom,right,bottom+58),'COMMENT YOUR CHOICE + ONE REASON',rgba(t['accent']),rgba('#FFFFFF'),None,20)

    # 9) Tech explained: definition + 3 fact cards.
    elif kind=='tech_explained':
        card(im,(left,y,right,y+235),rgba(t['dark']),None,34,True); d=ImageDraw.Draw(im)
        pill(d,(left+28,y+24,left+290,y+70),'ONE-SENTENCE IDEA',rgba(t['accent']),rgba('#FFFFFF'),None,18)
        draw_wrapped(d,item['prompt'],(left+32,y+90),font(38,True),rgba('#FFFFFF'),right-left-64,7,4)
        bottom=y+260
        for i,fact in enumerate(item.get('facts',[])[:3]):
            yy=bottom+i*100; card(im,(left,yy,right,yy+82),rgba(t['surface2']),rgba(t['border']),24,False); d=ImageDraw.Draw(im); d.ellipse((left+18,yy+18,left+60,yy+60),fill=rgba(t['accent'])); d.text((left+31,yy+25),str(i+1),font=font(17,True),fill=rgba('#FFFFFF')); draw_wrapped(d,fact,(left+78,yy+17),font(20,True),rgba(t['text']),right-left-100,4,2)
        bottom+=330

    # 10) Weekly mission: 7-day roadmap.
    elif kind=='weekly_mission':
        card(im,(left,y,right,y+190),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
        pill(d,(left+28,y+24,left+270,y+70),'7-DAY BUILD',rgba(t['soft']),rgba(t['accent']),None,19)
        draw_wrapped(d,item['prompt'],(left+32,y+90),font(34,True),rgba(t['text']),right-left-64,7,3)
        bottom=y+215; task=item.get('task','')
        phases=[('DAY 1','Plan'),('DAY 2–3','Build'),('DAY 4','Validate'),('DAY 5','Test'),('DAY 6','Polish'),('DAY 7','Explain')]
        for i,(day,label) in enumerate(phases):
            col=i%2; row=i//2; x=left+col*440; yy=bottom+row*105
            card(im,(x,yy,x+410,yy+86),rgba(t['surface2']),rgba(t['border']),24,False); d=ImageDraw.Draw(im); d.text((x+18,yy+16),day,font=font(18,True),fill=rgba(t['accent'])); d.text((x+145,yy+16),label,font=font(22,True),fill=rgba(t['text']))
        bottom+=340

    # 11) Learn 60 seconds: lesson timeline.
    elif kind=='learn_60_seconds':
        card(im,(left,y,right,y+220),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
        pill(d,(left+28,y+24,left+310,y+70),'60-SECOND LESSON',rgba(t['soft']),rgba(t['accent']),None,18)
        draw_wrapped(d,item['prompt'],(left+32,y+90),font(36,True),rgba(t['text']),right-left-64,7,4)
        bottom=y+245
        for i,fact in enumerate(item.get('facts',[])[:3]):
            yy=bottom+i*100; d.ellipse((left+24,yy+10,left+68,yy+54),fill=rgba(t['accent'])); d.line((left+46,yy+54,left+46,yy+90),fill=rgba(t['accent']),width=5) if i<2 else None; draw_wrapped(d,fact,(left+88,yy+5),font(22,True),rgba(t['text']),right-left-120,5,3)
        bottom+=310

    # 12) Weekly result: reveal board with answer and why.
    elif kind=='weekly_result':
        card(im,(left,y,right,y+210),rgba(t['dark']),None,34,True); d=ImageDraw.Draw(im)
        pill(d,(left+28,y+24,left+290,y+70),'ANSWER REVEAL',rgba(t['accent']),rgba('#FFFFFF'),None,18)
        draw_wrapped(d,item['prompt'],(left+32,y+90),font(35,True),rgba('#FFFFFF'),right-left-64,7,3)
        bottom=y+235
        answer=item.get('answer','—')
        card(im,(left,bottom,right,bottom+150),rgba(t['surface2']),rgba(t['accent']),30,True); d=ImageDraw.Draw(im)
        d.text((left+32,bottom+25),'CORRECT ANSWER',font=font(18,True),fill=rgba(t['muted']))
        d.text((left+32,bottom+58),str(answer),font=font(50,True),fill=rgba(t['accent']))
        draw_wrapped(d,item.get('explanation',''),(left+230,bottom+35),font(24,False),rgba(t['text']),right-left-270,6,4)
        bottom+=180

    else:
        # safe fallback, still deterministic and clean
        bottom=_answer_grid(im,d,left,right,y,item,t,item.get('kicker','CHALLENGE')) if item.get('options') else y+300

    _footer(im,d,left,right,item,kind,t)
    return im.convert('RGB'),t

def caption(item,kind,theme):
    lines=[f"{item['title']} | Smart Learning Lab",'',item['prompt']]
    if item.get('options'):
        for k,v in item['options'].items(): lines.append(f'{k}. {v}')
    if item.get('compare'):
        lines += ['',f"A: {item['compare'].get('A','')}",f"B: {item['compare'].get('B','')}"]
    if item.get('answer'):
        lines += ['',f"Answer: {item['answer']}",f"Why: {item.get('explanation','See the next post for the explanation.')}"]
    if item.get('tip'): lines += ['',f"Tip: {item['tip']}"]
    if item.get('task'): lines += ['',f"Mission: {item['task']}"]
    lines += ['',item.get('cta','Comment your answer • Tag a friend • Share'),'']
    lines += item.get('hashtags',['#SmartLearningLab','#LearnPracticeGrow'])
    return '\n'.join(lines)

def generate(kind,index,theme_number=None):
    item=load_item(kind,index)
    theme_number=theme_number or theme_for_content(kind,index)['theme_number']
    im,t=render(item,kind,index,theme_number)
    out=ROOT/CFG['output_dir']; out.mkdir(exist_ok=True)
    stem=f"{kind}-{index:04d}"
    image_path=out/f'{stem}.png'; cap_path=out/f'{stem}.txt'
    im.save(image_path,format='PNG',optimize=True)
    cap_path.write_text(caption(item,kind,t),encoding='utf-8')
    return item,image_path,cap_path,t

def main():
    p=argparse.ArgumentParser(); p.add_argument('--content-type',default='daily_challenge',choices=sorted(INDEX['content'].keys())); p.add_argument('--index',type=int,default=1); p.add_argument('--theme',type=int); p.add_argument('--count',type=int,default=1)
    a=p.parse_args()
    for n in range(a.count):
        item,img,cap,t=generate(a.content_type,a.index+n,a.theme)
        print(json.dumps({'content_type':a.content_type,'index':a.index+n,'theme':t['name'],'image':str(img),'caption':str(cap)},indent=2,ensure_ascii=False))
if __name__=='__main__': main()
