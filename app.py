import json, argparse, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
DATA=json.loads((ROOT/CFG['content_file']).read_text(encoding='utf-8'))

def font(size,bold=False):
    p='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if not os.path.exists(p): p='C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf'
    return ImageFont.truetype(p,size) if os.path.exists(p) else ImageFont.load_default()

def wrap(draw,text,f,mw):
    out=[]; cur=''
    for w in text.split():
        t=(cur+' '+w).strip()
        if draw.textbbox((0,0),t,font=f)[2] <= mw: cur=t
        else:
            if cur: out.append(cur)
            cur=w
    if cur: out.append(cur)
    return out

def render(c):
    W,H=CFG['image']['width'],CFG['image']['height']; m=90
    im=Image.new('RGB',(W,H),'#0B1020'); d=ImageDraw.Draw(im)
    d.rounded_rectangle((m,m,W-m,H-m),radius=48,fill='#111936',outline='#6675E8',width=4)
    d.text((m+60,m+55),'SMART LEARNING LAB',font=font(42,True),fill='white')
    d.text((m+60,m+112),'DAILY CHALLENGE',font=font(30,True),fill='#9EAEFF')
    y=m+210
    for line in wrap(d,c['title'],font(58,True),W-2*m-120):
        d.text((m+60,y),line,font=font(58,True),fill='white'); y+=70
    y+=30
    for line in wrap(d,c['hook'],font(30),W-2*m-120):
        d.text((m+60,y),line,font=font(30),fill='#D7DEFF'); y+=42
    y+=40
    for line in wrap(d,c['question'],font(39,True),W-2*m-120):
        d.text((m+60,y),line,font=font(39,True),fill='white'); y+=54
    y+=35
    for k,v in c['options'].items():
        d.rounded_rectangle((m+60,y,W-m-60,y+82),radius=20,fill='#1B2547')
        d.text((m+90,y+21),f'{k}. {v}',font=font(31),fill='white')
        y+=105
    fy=H-m-160
    d.text((m+60,fy),f"TIME: {c['time_limit_seconds']}s  |  {c['difficulty']}",font=font(27,True),fill='#B5C2FF')
    d.text((m+60,fy+55),'COMMENT YOUR ANSWER | SHARE WITH A FRIEND',font=font(25,True),fill='white')
    out=ROOT/CFG['output_dir']/(c['id']+'.png'); im.save(out); return out

def make_caption(c):
    tags=' '.join(c['hashtags']) if CFG['caption']['include_hashtags'] else ''
    return (c['hook']+'\n\n'+c['question']+'\n\n'+
            'A. '+c['options']['A']+'\nB. '+c['options']['B']+'\nC. '+c['options']['C']+'\nD. '+c['options']['D']+
            '\n\nTime: '+str(c['time_limit_seconds'])+' seconds\n'+c['cta']+'\n\n'+tags)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--index',type=int); ap.add_argument('--id'); ap.add_argument('--count',type=int,default=1)
    a=ap.parse_args()
    if a.id: chosen=[x for x in DATA['challenges'] if x['id']==a.id]
    else:
        idx=(a.index or 1)-1; chosen=DATA['challenges'][idx:idx+a.count]
    for c in chosen:
        p=render(c); p.with_suffix('.txt').write_text(make_caption(c),encoding='utf-8'); print(p)

if __name__=='__main__': main()
