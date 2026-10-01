import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
state=ROOT/'state.json'
data=json.loads((ROOT/'data/challenges.json').read_text(encoding='utf-8'))
s=json.loads(state.read_text()) if state.exists() else {'next_index':1,'history':[]}
idx=s.get('next_index',1)
if idx>data['total']: idx=1
subprocess.run([sys.executable,str(ROOT/'publisher.py'),'--index',str(idx),'--both'],check=True)
