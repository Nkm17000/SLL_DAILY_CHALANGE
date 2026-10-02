import argparse, json, os, time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
from app import generate, INDEX, ROOT, CFG

GRAPH_VERSION=os.getenv('META_GRAPH_VERSION','v24.0')
GRAPH=f'https://graph.facebook.com/{GRAPH_VERSION}'
TZ=ZoneInfo(os.getenv('TIMEZONE','Asia/Kolkata'))


def load_state():
    p=ROOT/'state.json'
    default={'next_index':{},'history':[],'theme_counter':0}
    if not p.exists():
        return default
    try:
        state=json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return default

    # Migrate state from the original single-content project, where
    # next_index was an integer. The multi-content engine requires a
    # per-content mapping. Preserve the old number as the starting index
    # for daily_challenge so an existing repository does not crash.
    if isinstance(state, dict) and isinstance(state.get('next_index'), int):
        legacy_index=max(1, int(state['next_index']))
        state['next_index']={'daily_challenge': legacy_index}

    if not isinstance(state, dict):
        return default
    if not isinstance(state.get('next_index'), dict):
        state['next_index']={}
    if not isinstance(state.get('history'), list):
        state['history']=[]
    try:
        state['theme_counter']=int(state.get('theme_counter',0))
    except (TypeError, ValueError):
        state['theme_counter']=0
    return state

def save_state(s):
    (ROOT/'state.json').write_text(json.dumps(s,indent=2,ensure_ascii=False),encoding='utf-8')

def load_schedule():
    return json.loads((ROOT/'schedule.json').read_text(encoding='utf-8'))

def _rotation_start_date(state, now):
    # The first successful publish initializes day 1. Thereafter the project
    # alternates Group A / Group B every calendar day in Asia/Kolkata.
    value=state.get('rotation_start_date')
    if value:
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            pass
    start=now.date()
    state['rotation_start_date']=start.isoformat()
    return start

def _active_group(state, now):
    start=_rotation_start_date(state, now)
    days=(now.date()-start).days
    return 'A' if days % 2 == 0 else 'B'

def _active_slot_for_time(slots, minutes, group):
    group_slots=[s for s in slots if s.get('day_group')==group]
    parsed=[]
    for s in group_slots:
        h,m=map(int,s['time_ist'].split(':')); parsed.append((h*60+m,s['content_type']))
    if not parsed:
        raise ValueError(f'No schedule slots configured for day group {group}')
    prior=[x for x in parsed if x[0] <= minutes]
    return max(prior)[1] if prior else parsed[0][1]

def select_content_type(requested='auto', schedule_cron='', state=None):
    if requested and requested!='auto':
        if requested not in INDEX['content']: raise ValueError(f'Unknown content type: {requested}')
        return requested
    if state is None:
        state=load_state()
    now=datetime.now(TZ)
    schedule=load_schedule()
    slots=schedule['slots']
    group=_active_group(state, now)

    # Scheduled workflow sends the 8 shared cron values. Pick the content
    # assigned to that clock slot for today's active group.
    if schedule_cron:
        matching=[s for s in slots if s.get('cron_utc')==schedule_cron and s.get('day_group')==group]
        if matching:
            return matching[0]['content_type']

    minutes=now.hour*60+now.minute
    return _active_slot_for_time(slots, minutes, group)

def next_index(state,kind):
    n=int(state.setdefault('next_index',{}).get(kind,1))
    total=INDEX['content'][kind]['total']
    return 1 if n>total else n

def token(name):
    v=os.getenv(name)
    if not v: raise RuntimeError(f'Missing environment variable: {name}')
    return v

def facebook_stage_image(image_path):
    page_id=token('FACEBOOK_PAGE_ID'); page_token=token('FACEBOOK_PAGE_ACCESS_TOKEN')
    with open(image_path,'rb') as fh:
        r=requests.post(f'{GRAPH}/{page_id}/photos',data={'published':'false','access_token':page_token},files={'source':('daily-challenge.png',fh,'image/png')},timeout=180)
    if not r.ok: raise RuntimeError(f'Facebook image staging failed: {r.status_code} {r.text}')
    data=r.json(); photo_id=data.get('id') or data.get('post_id')
    if not photo_id: raise RuntimeError(f'Facebook staging returned no photo id: {r.text}')
    # Ask Graph for the CDN source URL. This is the only external hosting mechanism used by the project.
    q=requests.get(f'{GRAPH}/{photo_id}',params={'fields':'images','access_token':page_token},timeout=60)
    if not q.ok: raise RuntimeError(f'Facebook image URL lookup failed: {q.status_code} {q.text}')
    images=q.json().get('images') or []
    if not images or not images[0].get('source'):
        raise RuntimeError(f'Facebook did not return a public image URL: {q.text}')
    return photo_id,images[0]['source']

def facebook_photo(image_path,caption):
    page_id=token('FACEBOOK_PAGE_ID'); page_token=token('FACEBOOK_PAGE_ACCESS_TOKEN')
    with open(image_path,'rb') as fh:
        r=requests.post(f'{GRAPH}/{page_id}/photos',data={'caption':caption,'access_token':page_token},files={'source':('daily-challenge.png',fh,'image/png')},timeout=180)
    if not r.ok: raise RuntimeError(f'Facebook publish failed: {r.status_code} {r.text}')
    return r.json()

def _meta_error(response):
    try:
        payload=response.json()
        return payload.get('error') or {}
    except ValueError:
        return {}

def _wait_instagram_image_ready(creation_id, access, timeout_seconds=600, poll_seconds=5):
    """Wait until Meta reports that the Instagram image container is publishable."""
    deadline=time.monotonic()+timeout_seconds
    last_status=None

    while time.monotonic() < deadline:
        q=requests.get(
            f'{GRAPH}/{creation_id}',
            params={
                'fields':'status_code,status',
                'access_token':access
            },
            timeout=60
        )

        if not q.ok:
            # A temporary status-check failure should not immediately destroy
            # an otherwise valid container. Keep polling until the deadline.
            print(f'Instagram status check returned {q.status_code}: {q.text[:500]}')
            time.sleep(poll_seconds)
            continue

        data=q.json()
        status=data.get('status_code') or data.get('status')
        if status != last_status:
            print(f'Instagram image processing status: {status}')
            last_status=status

        if status in ('FINISHED','PUBLISHED'):
            return

        if status in ('ERROR','EXPIRED'):
            raise RuntimeError(
                f'Instagram image processing failed: {q.text}'
            )

        time.sleep(poll_seconds)

    raise TimeoutError(
        f'Instagram image container {creation_id} did not become ready '
        f'within {timeout_seconds} seconds.'
    )

def _publish_instagram_container(user_id, creation_id, access, max_attempts=8):
    """Publish a ready container, retrying Meta's transient 'not ready' response."""
    url=f'{GRAPH}/{user_id}/media_publish'
    last_response=None

    for attempt in range(1,max_attempts+1):
        r=requests.post(
            url,
            data={
                'creation_id':creation_id,
                'access_token':access
            },
            timeout=120
        )
        last_response=r

        if r.ok:
            return r.json()

        error=_meta_error(r)
        try:
            code=int(error.get('code',-1))
        except (TypeError,ValueError):
            code=-1
        try:
            subcode=int(error.get('error_subcode',-1))
        except (TypeError,ValueError):
            subcode=-1

        # Meta can still answer 9007/2207027 for a short period even after
        # the container status reaches FINISHED. Wait and try again.
        if code == 9007 and subcode == 2207027 and attempt < max_attempts:
            wait_seconds=min(15,5*attempt)
            print(
                f'Instagram says the media is not ready yet '
                f'(attempt {attempt}/{max_attempts}); waiting {wait_seconds}s...'
            )
            time.sleep(wait_seconds)
            continue

        raise RuntimeError(
            f'Instagram publish failed: {r.status_code} {r.text}'
        )

    raise RuntimeError(
        f'Instagram publish failed after {max_attempts} attempts: '
        f'{last_response.status_code} {last_response.text}'
    )

def instagram_image(public_url,caption):
    """
    Publish one generated PNG to Instagram.

    The image is first staged as an unpublished Facebook Page photo so Meta
    provides a public CDN URL. Instagram then creates an image container,
    waits for Meta to finish processing it, and retries the final publish
    when Meta briefly returns 9007/2207027 ("Media ID is not available").
    """
    user_id=token('INSTAGRAM_USER_ID')
    access=token('INSTAGRAM_ACCESS_TOKEN')

    r=requests.post(
        f'{GRAPH}/{user_id}/media',
        data={
            'image_url':public_url,
            'caption':caption,
            'access_token':access
        },
        timeout=120
    )
    if not r.ok:
        raise RuntimeError(
            f'Instagram container creation failed: {r.status_code} {r.text}'
        )

    creation_id=r.json().get('id')
    if not creation_id:
        raise RuntimeError(f'Instagram returned no creation id: {r.text}')

    print(f'Instagram image container created: {creation_id}')

    # Do not call media_publish immediately. This is the key fix for
    # Meta error 9007 / 2207027.
    _wait_instagram_image_ready(
        creation_id,
        access,
        timeout_seconds=600,
        poll_seconds=5
    )

    return _publish_instagram_container(
        user_id,
        creation_id,
        access,
        max_attempts=8
    )

def publish(kind=None,index=None,do_facebook=True,do_instagram=True,schedule_cron=''):
    state=load_state(); kind=select_content_type(kind or 'auto', schedule_cron, state); index=index or next_index(state,kind)
    item,image,cap,t=generate(kind,index)
    caption=cap.read_text(encoding='utf-8')
    result={'content_type':kind,'index':index,'id':item['id'],'theme':t['name'],'facebook':None,'instagram':None}
    staged=None
    if do_instagram:
        staged,url=facebook_stage_image(image); result['staged_facebook_photo_id']=staged
        result['instagram']=instagram_image(url,caption)
    if do_facebook:
        result['facebook']=facebook_photo(image,caption)
    state.setdefault('next_index',{})[kind]=1 if index>=INDEX['content'][kind]['total'] else index+1
    state.setdefault('history',[]).append({'timestamp':int(time.time()),**result})
    # Keep history bounded for repository size.
    state['history']=state['history'][-500:]
    save_state(state)
    print(json.dumps(result,indent=2,ensure_ascii=False))

def main():
    p=argparse.ArgumentParser(); p.add_argument('--content-type',default='auto'); p.add_argument('--index',type=int); p.add_argument('--schedule-cron',default=os.getenv('SCHEDULE_CRON','')); p.add_argument('--facebook',action='store_true'); p.add_argument('--instagram',action='store_true'); p.add_argument('--both',action='store_true')
    a=p.parse_args(); both=a.both or (not a.facebook and not a.instagram)
    publish(a.content_type,a.index,do_facebook=(both or a.facebook),do_instagram=(both or a.instagram),schedule_cron=a.schedule_cron)
if __name__=='__main__': main()
