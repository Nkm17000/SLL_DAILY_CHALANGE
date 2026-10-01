import argparse
import json
import os
import math
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

def card(im,box,fill,outline=None,r=34,shadow=True):
    x1,y1,x2,y2=box
    if shadow:
        sh=Image.new('RGBA',im.size,(0,0,0,0)); sd=ImageDraw.Draw(sh)
        sd.rounded_rectangle((x1+8,y1+12,x2+8,y2+12),radius=r,fill=(0,0,0,35))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=3 if outline else 1)

def icon(d,kind,cx,cy,size,t):
    a=rgba(t['accent']); a2=rgba(t['accent2']); dark=rgba(t['dark']); white=rgba('#FFFFFF')
    if kind=='clock':
        d.ellipse((cx-size,cy-size,cx+size,cy+size),fill=a,outline=dark,width=5); d.ellipse((cx-size*.72,cy-size*.72,cx+size*.72,cy+size*.72),fill=white)
        d.line((cx,cy,cx,cy-size*.48),fill=dark,width=6); d.line((cx,cy,cx+size*.38,cy+size*.15),fill=dark,width=6); d.ellipse((cx-6,cy-6,cx+6,cy+6),fill=dark)
    elif kind=='code':
        d.rounded_rectangle((cx-size,cy-size*.72,cx+size,cy+size*.72),radius=18,fill=dark,outline=a,width=4)
        f=font(int(size*.72),True); d.text((cx-size*.55,cy-size*.42),'</>',font=f,fill=a2)
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

def theme_for(theme_number):
    return dict(THEMES[(theme_number-1)%len(THEMES)],theme_number=((theme_number-1)%len(THEMES))+1)

def load_item(kind,index):
    meta=INDEX['content'][kind]
    d=json.loads((ROOT/meta['file']).read_text(encoding='utf-8'))
    items=d.get('items') or d.get('challenges')
    item=items[(index-1)%len(items)]
    if kind=='daily_challenge':
        item=dict(item)
        item['prompt']=item.get('question',item.get('prompt',''))
        item['kicker']='YOUR 15-SECOND CHALLENGE'
        item['title']='Math / Brain Daily Challenge' if item.get('category')=='math' else 'Daily Challenge'
        item['content_type']=kind
    return item

def layout_info(kind):
    return {
      'crack_the_code':('CRACK THE CODE','code','Decode it before the timer ends.'),
      'ai_detective':('AI DETECTIVE','brain','Can you spot the incorrect answer?'),
      'predict_the_code':('PREDICT THE CODE','code','Run it in your head. No compiler needed.'),
      'spot_the_mistake':('SPOT THE MISTAKE','bug','One detail is wrong. Find it.'),
      'logic_puzzle':('LOGIC PUZZLE','brain','Slow down. Look for the rule.'),
      'tech_tip':('60-SECOND TECH TIP','bolt','One useful idea you can use today.'),
      'build_it':('BUILD IT','code','Turn the idea into a tiny working project.'),
      'ai_challenge':('AI CHALLENGE','brain','Try it, verify it, improve it.'),
      'this_or_that':('THIS OR THAT','scale','Choose based on the real trade-offs.'),
      'tech_explained':('TECH EXPLAINED','light','A complex idea in simple words.'),
      'weekly_mission':('WEEKLY MISSION','bolt','Build something small. Learn something real.'),
      'science_challenge':('SCIENCE CHALLENGE','science','Use the formula. Trust the evidence.'),
      'cyber_safety':('CYBER SAFETY','shield','Pause. Check. Protect.'),
      'learn_60_seconds':('LEARN IN 60 SECONDS','light','One concept. One minute. One useful takeaway.'),
      'weekly_result':('WEEKLY RESULT','scale','Answer reveal + the key idea to remember.'),
      'daily_challenge':('15 SECOND CHALLENGE','clock','No searching. Your turn.'),
    }[kind]

def render(item,kind,sequence_number,theme_number):
    W,H=CFG['image']['width'],CFG['image']['height']; t=theme_for(theme_number)
    im=Image.new('RGBA',(W,H),rgba(t['background'])); d=ImageDraw.Draw(im)
    # decorative bubbles
    for x,y,r,c,a in [(0,180,180,t['accent'],32),(W,120,190,t['accent2'],28),(W,H-220,220,t['accent'],24),(-20,H-120,200,t['accent2'],24)]: d.ellipse((x-r,y-r,x+r,y+r),fill=rgba(c,a))
    margin=60; card(im,(margin,28,W-margin,H-28),rgba(t['surface']),rgba(t['border']),46,True); d=ImageDraw.Draw(im)
    left,right=105,W-105
    # header
    fbrand=font(38,True); fsub=font(18,True)
    d.text((left,72),'SMART LEARNING LAB',font=fbrand,fill=rgba(t['text']))
    d.text((left,118),'L E A R N   •   P R A C T I C E   •   G R O W',font=fsub,fill=rgba(t['accent']))
    # logo-ish book mark
    d.rounded_rectangle((left-62,62,left-2,125),radius=12,fill=rgba(t['accent']))
    d.polygon([(left-53,72),(left-11,72),(left-32,92)],fill=rgba('#FFFFFF'))
    title,ico,tagline=layout_info(kind)
    d.text((W-520,70),title.title(),font=font(48,True,True),fill=rgba(t['accent']))
    d.line((W-520,125,W-270,125),fill=rgba(t['accent']),width=5)
    # hero ribbon
    hero=(260,185,1335,410); card(im,hero,rgba(t['accent']),None,50,False); d=ImageDraw.Draw(im)
    d.rounded_rectangle((hero[0]+22,hero[1]+20,hero[2]-18,hero[3]+18),radius=48,fill=rgba(t['dark']))
    icon(d,ico,170,300,92,t)
    d.text((hero[0]+58,hero[1]+30),f'{title}',font=font(54,True),fill=rgba('#FFFFFF'))
    d.text((hero[0]+58,hero[1]+102),tagline,font=font(31,False,True),fill=rgba(t['accent2']))
    badge=f'DAILY CONTENT  #{sequence_number:04d}'
    d.rounded_rectangle((left,450,left+430,510),radius=30,fill=rgba('#FFFFFF'),outline=rgba(t['border']),width=3)
    d.text((left+28,465),badge,font=font(24,True),fill=rgba(t['text']))
    d.rounded_rectangle((right-250,450,right,510),radius=30,fill=rgba(t['accent']))
    d.text((right-215,465),kind.replace('_',' ').upper()[:17],font=font(22,True),fill=rgba('#FFFFFF'))
    # main content
    y=545
    if item.get('options'):
        card(im,(left,y,right,y+245),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
        d.rounded_rectangle((left+34,y+28,left+350,y+78),radius=25,fill=rgba(t['soft'])); d.text((left+60,y+40),'YOUR CHALLENGE',font=font(21,True),fill=rgba(t['accent']))
        q=item['prompt']; draw_wrapped(d,q,(left+42,y+98),font(48,True),rgba(t['text']),right-left-84,8,3)
        opts=list(item['options'].items())
        oy=y+275; gap=24; h=112; colw=(right-left-gap)//2
        for idx,(letter,val) in enumerate(opts[:4]):
            row=idx//2; col=idx%2; x=left+col*(colw+gap); yy=oy+row*(h+18)
            card(im,(x,yy,x+colw,yy+h),rgba(t['surface']),rgba(t['border']),30,True); d=ImageDraw.Draw(im)
            d.ellipse((x+24,yy+24,x+84,yy+84),fill=rgba(t['accent'])); d.text((x+42,yy+34),letter,font=font(26,True),fill=rgba('#FFFFFF'))
            draw_wrapped(d,val,(x+105,yy+30),font(28,True),rgba(t['text']),colw-130,4,2)
        bottom=oy+2*(h+18)+10
    elif kind=='this_or_that' and item.get('compare'):
        card(im,(left,y,right,y+250),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
        draw_wrapped(d,item['compare']['question'],(left+40,y+35),font(38,True),rgba(t['text']),right-left-80,7,3)
        bottom=y+280
        a=item['compare']['A']; b=item['compare']['B']; gap=24; cw=(right-left-gap)//2
        for j,val in enumerate([a,b]):
            x=left+j*(cw+gap); card(im,(x,bottom,x+cw,bottom+170),rgba(t['surface']),rgba(t['border']),32,True); d=ImageDraw.Draw(im)
            d.ellipse((x+24,bottom+24,x+84,bottom+84),fill=rgba(t['accent'])); d.text((x+44,bottom+34),chr(65+j),font=font(26,True),fill=rgba('#FFFFFF'))
            draw_wrapped(d,val,(x+105,bottom+35),font(30,True),rgba(t['text']),cw-125,5,3)
        bottom+=195
    else:
        card(im,(left,y,right,y+300),rgba(t['surface']),rgba(t['border']),34,True); d=ImageDraw.Draw(im)
        d.rounded_rectangle((left+34,y+28,left+370,y+78),radius=25,fill=rgba(t['soft'])); d.text((left+58,y+40),item.get('kicker','THE BIG IDEA'),font=font(21,True),fill=rgba(t['accent']))
        draw_wrapped(d,item['prompt'],(left+42,y+100),font(42,True),rgba(t['text']),right-left-84,8,4)
        bottom=y+325
        if item.get('code'):
            card(im,(left,bottom,right,bottom+205),rgba(t['dark']),None,28,True); d=ImageDraw.Draw(im); d.text((left+28,bottom+22),item['code'],font=font(25,False),fill=rgba('#FFFFFF'))
            bottom+=230
        if item.get('tip'):
            card(im,(left,bottom,right,bottom+205),rgba(t['surface2']),rgba(t['border']),28,True); d=ImageDraw.Draw(im); draw_wrapped(d,item['tip'],(left+30,bottom+30),font(27,False),rgba(t['text']),right-left-60,7,6); bottom+=230
        if item.get('task'):
            card(im,(left,bottom,right,bottom+205),rgba(t['surface2']),rgba(t['border']),28,True); d=ImageDraw.Draw(im); draw_wrapped(d,item['task'],(left+30,bottom+30),font(27,False),rgba(t['text']),right-left-60,7,6); bottom+=230
        if item.get('facts'):
            card(im,(left,bottom,right,bottom+235),rgba(t['surface2']),rgba(t['border']),28,True); d=ImageDraw.Draw(im); yy=bottom+28
            for fact in item['facts'][:3]: yy=draw_wrapped(d,'• '+fact,(left+30,yy),font(24,False),rgba(t['text']),right-left-60,5,3)+10
            bottom+=260
    # Footer / CTA
    footer_y=H-300
    card(im,(left,footer_y,right,footer_y+120),rgba(t['surface2']),None,28,False); d=ImageDraw.Draw(im)
    d.text((left+32,footer_y+25),f"⏱ {item.get('time_limit_seconds',30)} SEC",font=font(24,True),fill=rgba(t['accent']))
    d.text((right-300,footer_y+25),str(item.get('difficulty','Medium')).upper(),font=font(24,True),fill=rgba(t['text']))
    d.text((left+32,footer_y+70),item.get('cta','Comment • Tag • Share').upper(),font=font(22,True),fill=rgba(t['text']))
    d.text((left,footer_y+150),'Small Questions • Big Progress',font=font(32,True,True),fill=rgba(t['accent']))
    d.text((right-470,footer_y+155),f"THEME {t['theme_number']}/10 • {t['name'].upper()}",font=font(18,True),fill=rgba(t['muted']))
    # tiny answer reveal line for result/educational posts
    if item.get('answer') and kind in {'weekly_result','crack_the_code','predict_the_code','spot_the_mistake','logic_puzzle','science_challenge','cyber_safety','ai_detective'}:
        d.text((left,footer_y+195),'ANSWER REVEALED IN THE CAPTION / NEXT POST',font=font(17,True),fill=rgba(t['muted']))
    return im.convert('RGB'),t

def caption(item,kind,theme):
    lines=[f"{item['title']} | Smart Learning Lab",'',item['prompt']]
    if item.get('options'):
        for k,v in item['options'].items(): lines.append(f'{k}. {v}')
    if item.get('answer'):
        lines += ['',f"Answer: {item['answer']}",f"Why: {item.get('explanation','See the next post for the explanation.')}"]
    if item.get('tip'): lines += ['',f"Tip: {item['tip']}"]
    if item.get('task'): lines += ['',f"Mission: {item['task']}"]
    lines += ['',item.get('cta','Comment your answer • Tag a friend • Share'),'']
    lines += item.get('hashtags',['#SmartLearningLab','#LearnPracticeGrow'])
    return '\n'.join(lines)

def generate(kind,index,theme_number=None):
    item=load_item(kind,index); theme_number=theme_number or ((index-1)%len(THEMES))+1
    im,t=render(item,kind,index,theme_number)
    out=ROOT/CFG['output_dir']; out.mkdir(exist_ok=True)
    stem=f"{kind}-{index:04d}"
    image_path=out/f'{stem}.png'; cap_path=out/f'{stem}.txt'
    im.save(image_path,format='PNG',optimize=True)
    cap_path.write_text(caption(item,kind,t),encoding='utf-8')
    return item,image_path,cap_path,t

def main():
    p=argparse.ArgumentParser(); p.add_argument('--content-type',default='crack_the_code',choices=sorted(INDEX['content'].keys())); p.add_argument('--index',type=int,default=1); p.add_argument('--theme',type=int); p.add_argument('--count',type=int,default=1)
    a=p.parse_args()
    for n in range(a.count):
        item,img,cap,t=generate(a.content_type,a.index+n,a.theme)
        print(json.dumps({'content_type':a.content_type,'index':a.index+n,'theme':t['name'],'image':str(img),'caption':str(cap)},indent=2))
if __name__=='__main__': main()
