import os, json, time, argparse
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
DATA=json.loads((ROOT/CFG['content_file']).read_text(encoding='utf-8'))
OUT=ROOT/CFG['output_dir']

GRAPH_VERSION=os.getenv('META_GRAPH_VERSION','v24.0')
GRAPH=f'https://graph.facebook.com/{GRAPH_VERSION}'

def env(name, required=True):
    v=os.getenv(name,'').strip()
    if required and not v:
        raise RuntimeError(f'Missing environment variable: {name}')
    return v

def generate(index):
    import subprocess, sys
    subprocess.run([sys.executable,str(ROOT/'app.py'),'--index',str(index)],check=True)
    c=DATA['challenges'][index-1]
    return c, OUT/(c['id']+'.png'), OUT/(c['id']+'.txt')

def upload_r2(local_path, key):
    from boto3.session import Session
    endpoint=env('R2_ENDPOINT')
    access=env('R2_ACCESS_KEY_ID')
    secret=env('R2_SECRET_ACCESS_KEY')
    bucket=env('R2_BUCKET')
    public=env('R2_PUBLIC_BASE_URL').rstrip('/')
    s=Session(aws_access_key_id=access,aws_secret_access_key=secret)
    client=s.client('s3',endpoint_url=endpoint,region_name='auto')
    client.upload_file(str(local_path),bucket,key,ExtraArgs={'ContentType':'image/png','CacheControl':'public,max-age=31536000'})
    return public+'/'+key

def facebook_photo(image_path, caption):
    page_id=env('FACEBOOK_PAGE_ID'); token=env('FACEBOOK_PAGE_ACCESS_TOKEN')
    with open(image_path,'rb') as f:
        r=requests.post(f'{GRAPH}/{page_id}/photos',data={'access_token':token,'caption':caption},files={'source':('challenge.png',f,'image/png')},timeout=120)
    if not r.ok: raise RuntimeError(f'Facebook publish failed: {r.status_code} {r.text}')
    return r.json()

def instagram_image(image_url, caption):
    user_id=env('INSTAGRAM_USER_ID'); token=env('INSTAGRAM_ACCESS_TOKEN')
    r=requests.post(f'{GRAPH}/{user_id}/media',data={'image_url':image_url,'caption':caption,'access_token':token},timeout=120)
    if not r.ok: raise RuntimeError(f'Instagram container creation failed: {r.status_code} {r.text}')
    creation_id=r.json().get('id')
    if not creation_id: raise RuntimeError(f'Instagram returned no creation id: {r.text}')
    for _ in range(20):
        s=requests.get(f'{GRAPH}/{creation_id}',params={'fields':'status_code','access_token':token},timeout=60)
        if s.ok and s.json().get('status_code') in ('FINISHED','PUBLISHED'):
            break
        if s.ok and s.json().get('status_code')=='ERROR':
            raise RuntimeError(f'Instagram media processing failed: {s.text}')
        time.sleep(3)
    r=requests.post(f'{GRAPH}/{user_id}/media_publish',data={'creation_id':creation_id,'access_token':token},timeout=120)
    if not r.ok: raise RuntimeError(f'Instagram publish failed: {r.status_code} {r.text}')
    return r.json()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--index',type=int)
    ap.add_argument('--facebook',action='store_true')
    ap.add_argument('--instagram',action='store_true')
    ap.add_argument('--both',action='store_true')
    a=ap.parse_args()
    state_path=ROOT/'state.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else {'next_index':1,'history':[]}
    index=a.index or state['next_index']
    if index>DATA['total']: index=1
    c,image,caption_file=generate(index)
    caption=caption_file.read_text(encoding='utf-8')
    results={'index':index,'id':c['id'],'facebook':None,'instagram':None}
    if a.facebook or a.both: results['facebook']=facebook_photo(image,caption)
    if a.instagram or a.both:
        key=f'daily-challenge/{c["id"]}.png'
        url=upload_r2(image,key)
        results['instagram']=instagram_image(url,caption)
        results['public_image_url']=url
    if not (a.facebook or a.instagram or a.both):
        print(json.dumps({'generated':str(image),'caption':str(caption_file),'index':index},indent=2)); return
    state['next_index']=index+1
    state.setdefault('history',[]).append({'index':index,'id':c['id'],'results':results,'timestamp':int(time.time())})
    state_path.write_text(json.dumps(state,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()
