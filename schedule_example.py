import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
state=ROOT/'state.json'
data=json.loads((ROOT/'data/challenges.json').read_text(encoding='utf-8'))
s=json.loads(state.read_text()) if state.exists() else {'next_index':1}
idx=s['next_index']
if idx>data['total']: idx=1
subprocess.run(['python',str(ROOT/'app.py'),'--index',str(idx)],check=True)
s['next_index']=idx+1
state.write_text(json.dumps(s,indent=2),encoding='utf-8')
print(f'Prepared challenge #{idx}')
