import os, json, re, hashlib, textwrap, argparse
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
TZ=ZoneInfo(os.getenv("TIMEZONE","Asia/Kolkata"))
STATE_PATH=ROOT/"quiz_state.json"
OUT=ROOT/"output"; OUT.mkdir(exist_ok=True)
GRAPH_VERSION=os.getenv("META_GRAPH_VERSION","v24.0")
GRAPH=f"https://graph.facebook.com/{GRAPH_VERSION}"
SUBJECTS={
 "MATH":{"label":"MATH","prompt":"medium difficulty quantitative aptitude / arithmetic / algebra for Indian competitive exams"},
 "GKGS":{"label":"GK & GS","prompt":"medium difficulty Indian general knowledge and general studies, civics, geography, history, economy or science"},
 "REASONING":{"label":"REASONING","prompt":"medium difficulty logical reasoning / series / coding-decoding / syllogism for Indian competitive exams"},
 "ENGLISH":{"label":"ENGLISH","prompt":"medium difficulty English grammar, vocabulary, sentence improvement or usage for Indian competitive exams"}
}
BRAND_LINES=[
 "Smart Learning Lab 247 | Daily practice for serious aspirants",
 "SSC | UPSC | Banking | Railway | RAS | IAS",
 "Website: https://smartlearninglab-react.pages.dev/",
 "Instagram: https://www.instagram.com/smartlearninglab247",
 "YouTube: https://www.youtube.com/@smartlearninglab247",
 "Facebook: https://www.facebook.com/smartlearninglab247"
]
THEMES=[
 ("#EAF5FF","#1253A4","#09264C","#FFC928"),
 ("#FFF0E4","#8D2020","#481016","#FFC928"),
 ("#F4ECFF","#5B22A5","#2B0759","#FFD447"),
 ("#ECF9E8","#17683C","#06351F","#FFD447"),
]
def load_state():
    if STATE_PATH.exists():
        try: s=json.loads(STATE_PATH.read_text(encoding="utf8"))
        except Exception: s={}
    else: s={}
    s.setdefault("challenge_no",0); s.setdefault("questions",[]); s.setdefault("last_quiz",None)
    return s
def save_state(s): STATE_PATH.write_text(json.dumps(s,indent=2,ensure_ascii=False),encoding="utf8")
def groq_questions(state):
    key=os.getenv("GROQ_API_KEY")
    if not key: raise RuntimeError("GROQ_API_KEY is required. Add it to GitHub Secrets.")
    model=os.getenv("GROQ_MODEL","openai/gpt-oss-120b")
    previous=state.get("last_quiz")
    previous_text=("Previous quiz answer to reveal now: "+json.dumps({k:previous.get(k) for k in ("challenge_no","subject","question","correct_option","explanation")},ensure_ascii=False)) if previous else "No previous quiz exists; do not invent a previous answer."
    recent=[q.get("fingerprint","") for q in state["questions"][-5000:]]
    recent_questions=[q.get("question","") for q in state["questions"][-250:]]
    prompt=f"""Create exactly 4 original multiple-choice quiz questions for Indian competitive-exam learners. All must be MEDIUM or HARD (never easy), unambiguous, factually checkable, and have exactly four plausible options A-D with one correct answer. Subjects:
MATH: {SUBJECTS['MATH']['prompt']}
GKGS: {SUBJECTS['GKGS']['prompt']}
REASONING: {SUBJECTS['REASONING']['prompt']}
ENGLISH: {SUBJECTS['ENGLISH']['prompt']}
Do not repeat or closely paraphrase any existing question. Existing recent questions: {json.dumps(recent_questions,ensure_ascii=False)}.
For factual questions provide a reliable source_url (prefer official government, NCERT, constitutional/official institution or dictionary/grammar reference). For math/reasoning provide source_url to a suitable authoritative learning/reference page where possible. Do not fabricate URLs; if unsure, use a stable official reference page. Include a short explanation for next-post answer reveal. Return ONLY valid JSON:
{{"questions":[{{"subject":"MATH","question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}}, "correct_option":"B","explanation":"...","source_url":"https://...","difficulty":"medium"}}]}}
Exactly one question per subject using subject keys MATH, GKGS, REASONING, ENGLISH. correct_option must be A/B/C/D. Do not put the answer inside question/options. Keep questions and options concise enough for a 1080x1350 social image.
{previous_text}
"""
    r=requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
        json={"model":model,"temperature":0.7,"messages":[{"role":"system","content":"You create rigorous original exam questions and return valid JSON only."},{"role":"user","content":prompt}],
              "response_format":{"type":"json_object"}},timeout=120)
    if not r.ok: raise RuntimeError(f"Groq API failed: {r.status_code} {r.text[:1000]}")
    data=json.loads(r.json()["choices"][0]["message"]["content"])
    qs=data.get("questions",[])
    if len(qs)!=4: raise RuntimeError("Groq did not return exactly four questions.")
    seen=set(recent)
    required={"MATH","GKGS","REASONING","ENGLISH"}
    if {q.get("subject") for q in qs}!=required: raise RuntimeError("Groq returned missing/duplicate subjects.")
    for q in qs:
        if not isinstance(q.get("options"),dict) or set(q["options"])!={"A","B","C","D"}: raise RuntimeError("Each question must have A-D options.")
        if q.get("correct_option") not in "ABCD" or len(q.get("question",""))<12: raise RuntimeError("Invalid question or answer key.")
        q["difficulty"]=str(q.get("difficulty","medium")).lower()
        if q["difficulty"] not in ("medium","hard","advanced"): raise RuntimeError("Question difficulty was below medium; refusing to publish.")
        fp=hashlib.sha256(re.sub(r"\W+"," ",q["question"].lower()).encode()).hexdigest()
        if fp in seen: raise RuntimeError("Duplicate question detected; rerun to generate a fresh set.")
        q["fingerprint"]=fp
        q["source_url"]=q.get("source_url","")
    return qs
def font(size,bold=False):
    candidates=(["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","C:/Windows/Fonts/arialbd.ttf"] if bold else
                ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","C:/Windows/Fonts/arial.ttf"])
    for p in candidates:
        if os.path.exists(p): return ImageFont.truetype(p,size)
    return ImageFont.load_default()
def wrap(draw,text,f,max_width):
    lines=[]; line=""
    for word in str(text).split():
        trial=(line+" "+word).strip()
        if draw.textbbox((0,0),trial,font=f)[2] <= max_width: line=trial
        else:
            if line: lines.append(line)
            line=word
    if line: lines.append(line)
    return lines or [""]
def draw_wrapped(draw,text,xy,f,fill,max_width,gap=10,max_lines=6):
    x,y=xy
    for line in wrap(draw,text,f,max_width)[:max_lines]:
        draw.text((x,y),line,font=f,fill=fill); y+=f.size+gap
    return y
def make_image(q,number):
    subject=q["subject"]; label=SUBJECTS[subject]["label"]
    bg,accent,dark,gold=THEMES[(number+list(SUBJECTS).index(subject))%len(THEMES)]
    im=Image.new("RGB",(1080,1350),bg); d=ImageDraw.Draw(im)
    d.rectangle((0,0,1080,22),fill=accent)
    d.rounded_rectangle((48,45,1032,155),radius=28,fill=dark)
    d.text((78,64),"SMART LEARNING LAB 247",font=font(27,True),fill="#FFFFFF")
    d.text((78,106),f"{number}_SLL_DAILY_{subject}",font=font(24,True),fill=gold)
    d.rounded_rectangle((48,185,1032,250),radius=22,fill=gold)
    d.text((75,200),f"CHALLENGE NO. {number}  •  {label}",font=font(27,True),fill="#152238")
    d.rounded_rectangle((48,280,1032,710),radius=30,fill="#FFFFFF",outline=accent,width=4)
    d.text((78,310),"QUESTION",font=font(22,True),fill=accent)
    y=draw_wrapped(d,q["question"],(78,365),font(34,True),"#172033",900,12,7)
    y=max(y+22,490)
    for i,k in enumerate("ABCD"):
        row=i//2; col=i%2; x=65+col*490; yy= min(750+row*130, 1010+row*5)
        d.rounded_rectangle((x,yy,x+455,yy+105),radius=22,fill="#F8FAFC",outline=accent,width=3)
        d.ellipse((x+18,yy+24,x+72,yy+78),fill=accent)
        d.text((x+35,yy+34),k,font=font(23,True),fill="#FFFFFF")
        draw_wrapped(d,q["options"][k],(x+88,yy+20),font(22,True),"#18243A",345,5,3)
    d.rounded_rectangle((48,1030,1032,1115),radius=22,fill=gold)
    d.text((78,1054),"COMMENT YOUR ANSWER • ANSWER REVEALED NEXT POST",font=font(21,True),fill="#172033")
    d.text((58,1150),"SSC | UPSC | Banking | Railway | RAS | IAS",font=font(21,True),fill=dark)
    d.text((58,1195),"smartlearninglab-react.pages.dev",font=font(20),fill=dark)
    d.text((58,1235),"@smartlearninglab247  •  Learn • Practice • Grow",font=font(20,True),fill=accent)
    d.text((58,1290),"Follow for the next challenge",font=font(19),fill=dark)
    path=OUT/f"{number}_SLL_DAILY_{subject}.png"; im.save(path,optimize=True)
    return path
def caption(q,number,previous):
    lines=[f"{number}_SLL_DAILY_{q['subject']}",f"Challenge No. {number} | {SUBJECTS[q['subject']]['label']}","",q["question"]]
    lines += [f"{k}. {q['options'][k]}" for k in "ABCD"]
    if q.get("source_url"):
        lines += ["",f"Reference: {q['source_url']}"]
    lines += ["","Comment your answer. No answer is shown in this challenge; the next post reveals the previous quiz answer and subject."]
    if previous:
        lines += ["",f"PREVIOUS QUIZ ANSWER — Challenge No. {previous['challenge_no']} ({SUBJECTS[previous['subject']]['label']})",
                  f"Question: {previous['question']}",f"Correct answer: {previous['correct_option']}. {previous['options'][previous['correct_option']]}",
                  f"Explanation: {previous['explanation']}"]
    lines += [""]+BRAND_LINES+["","#SmartLearningLab247 #DailyChallenge #Maths #GK #GS #Reasoning #English #CompetitiveExams"]
    return "\n".join(lines)
def account_pairs(platform,id_name,token_name):
    """Load enabled account destinations from config.json; credentials stay in environment secrets."""
    config_path=ROOT/"config.json"
    try:
        config=json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Could not read {config_path.name}: {exc}") from exc
    key="facebook_accounts" if platform=="facebook" else "instagram_accounts"
    accounts=[]
    for item in config.get(key,[]):
        if not item.get("enabled",True):
            continue
        ident_env=item.get("page_id_env" if platform=="facebook" else "user_id_env","")
        token_env=item.get("page_token_env" if platform=="facebook" else "access_token_env","")
        ident=os.getenv(ident_env) if ident_env else None
        token=os.getenv(token_env) if token_env else None
        if ident and token:
            accounts.append((ident,token))
        elif ident or token:
            print(f"WARNING: incomplete {platform} account '{item.get('name','unnamed')}'; both ID and token secrets are required.")
    return accounts
def fb_stage(image,fb_accounts):
    if not fb_accounts: raise RuntimeError("At least one Facebook page ID/token pair is required to host Instagram images.")
    pid,ptok=fb_accounts[0]
    with open(image,"rb") as f:
        r=requests.post(f"{GRAPH}/{pid}/photos",data={"published":"false","access_token":ptok},files={"source":("quiz.png",f,"image/png")},timeout=180)
    if not r.ok: raise RuntimeError(f"Facebook image staging failed: {r.status_code} {r.text[:500]}")
    photo=r.json().get("id")
    rr=requests.get(f"{GRAPH}/{photo}",params={"fields":"images","access_token":ptok},timeout=60)
    if not rr.ok: raise RuntimeError(f"Could not get public image URL: {rr.text[:500]}")
    imgs=rr.json().get("images",[])
    if not imgs or not imgs[0].get("source"): raise RuntimeError("Facebook did not return a public image URL for Instagram.")
    return imgs[0]["source"]
def publish_fb(image,cap,accounts):
    results=[]
    for pid,tok in accounts:
        try:
            with open(image,"rb") as f:
                r=requests.post(f"{GRAPH}/{pid}/photos",data={"caption":cap,"access_token":tok},files={"source":("quiz.png",f,"image/png")},timeout=180)
            results.append({"platform":"facebook","id":pid,"ok":r.ok,"response":r.json() if r.headers.get("content-type","").startswith("application/json") else r.text[:500]})
        except Exception as e: results.append({"platform":"facebook","id":pid,"ok":False,"error":str(e)})
    return results
def publish_ig(image_url,cap,accounts):
    results=[]
    for uid,tok in accounts:
        try:
            r=requests.post(f"{GRAPH}/{uid}/media",data={"image_url":image_url,"caption":cap,"access_token":tok},timeout=120)
            if not r.ok: raise RuntimeError(f"container create failed {r.status_code}: {r.text[:400]}")
            cid=r.json()["id"]
            pub=requests.post(f"{GRAPH}/{uid}/media_publish",data={"creation_id":cid,"access_token":tok},timeout=120)
            results.append({"platform":"instagram","id":uid,"ok":pub.ok,"response":pub.json() if pub.headers.get("content-type","").startswith("application/json") else pub.text[:500]})
        except Exception as e: results.append({"platform":"instagram","id":uid,"ok":False,"error":str(e)})
    return results
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    state=load_state()
    questions=groq_questions(state)
    number=int(state.get("challenge_no",0))+1
    previous=state.get("last_quiz")
    outputs=[]; results=[]
    fb=account_pairs("facebook","FACEBOOK_PAGE_ID","FACEBOOK_PAGE_ACCESS_TOKEN")
    ig=account_pairs("instagram","INSTAGRAM_USER_ID","INSTAGRAM_ACCESS_TOKEN")
    if not a.dry_run and (not fb or not ig): raise RuntimeError("Configure at least one Facebook and one Instagram account using the documented secrets.")
    staged_url=None
    for q in questions:
        q["challenge_no"]=number
        q["title"]=f"{number}_SLL_DAILY_{q['subject']}"
        image=make_image(q,number)
        cap=caption(q,number,previous)
        cap_path=OUT/f"{number}_SLL_DAILY_{q['subject']}.txt"; cap_path.write_text(cap,encoding="utf8")
        outputs.append({"name":q["title"],"image":str(image),"caption":str(cap_path),"source_url":q.get("source_url","")})
        if not a.dry_run:
            fr=publish_fb(image,cap,fb); results.extend(fr)
            if ig:
                if staged_url is None: staged_url=fb_stage(image,fb)
                results.extend(publish_ig(staged_url,cap,ig))
        state["questions"].append({"challenge_no":number,"subject":q["subject"],"question":q["question"],"fingerprint":q["fingerprint"],"source_url":q.get("source_url","")})
        state["last_quiz"]={"challenge_no":number,"subject":q["subject"],"question":q["question"],"options":q["options"],"correct_option":q["correct_option"],"explanation":q["explanation"],"source_url":q.get("source_url","")}
    state["challenge_no"]=number
    state["questions"]=state["questions"][-5000:]
    save_state(state)
    print(json.dumps({"challenge_no":number,"dry_run":a.dry_run,"outputs":outputs,"publish_results":results},indent=2,ensure_ascii=False))
    if results and not any(x.get("ok") for x in results): raise SystemExit("All publishing destinations failed. Review publish_results above.")
if __name__=="__main__": main()
