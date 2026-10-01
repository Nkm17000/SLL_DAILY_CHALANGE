import os
import json
import time
import argparse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
DATA = json.loads((ROOT / CFG['content_file']).read_text(encoding='utf-8'))
OUT = ROOT / CFG['output_dir']

GRAPH_VERSION = os.getenv('META_GRAPH_VERSION', 'v24.0')
GRAPH = f'https://graph.facebook.com/{GRAPH_VERSION}'


def env(name, required=True):
    value = os.getenv(name, '').strip()
    if required and not value:
        raise RuntimeError(f'Missing environment variable: {name}')
    return value


def generate(index):
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, str(ROOT / 'app.py'), '--index', str(index)],
        check=True,
    )
    challenge = DATA['challenges'][index - 1]
    return (
        challenge,
        OUT / f"{challenge['id']}.png",
        OUT / f"{challenge['id']}.txt",
    )


def facebook_stage_image(image_path):
    """Stage an unpublished Page photo and return its temporary public CDN URL.

    Meta hosts the image temporarily on its own CDN while Instagram creates
    the media container.
    """
    page_id = env('FACEBOOK_PAGE_ID')
    token = env('FACEBOOK_PAGE_ACCESS_TOKEN')

    with open(image_path, 'rb') as image_file:
        response = requests.post(
            f'{GRAPH}/{page_id}/photos',
            data={
                'access_token': token,
                'published': 'false',
            },
            files={
                'source': ('challenge.png', image_file, 'image/png'),
            },
            timeout=120,
        )

    if not response.ok:
        raise RuntimeError(
            f'Facebook staging upload failed: {response.status_code} {response.text}'
        )

    photo_id = response.json().get('id')
    if not photo_id:
        raise RuntimeError(f'Facebook staging returned no photo id: {response.text}')

    # Ask Graph API for the CDN image URL. The returned URL is temporary and
    # is used immediately for Instagram container creation.
    details = requests.get(
        f'{GRAPH}/{photo_id}',
        params={
            'fields': 'images',
            'access_token': token,
        },
        timeout=60,
    )

    if not details.ok:
        raise RuntimeError(
            f'Facebook staging image lookup failed: {details.status_code} {details.text}'
        )

    images = details.json().get('images') or []
    if not images:
        raise RuntimeError(
            'Facebook did not return a CDN image URL for the staged photo.'
        )

    # Prefer the largest available image.
    images = sorted(
        images,
        key=lambda item: (item.get('width') or 0) * (item.get('height') or 0),
        reverse=True,
    )
    image_url = images[0].get('source')
    if not image_url:
        raise RuntimeError('Facebook returned an image entry without a source URL.')

    return photo_id, image_url


def facebook_photo(image_path, caption):
    page_id = env('FACEBOOK_PAGE_ID')
    token = env('FACEBOOK_PAGE_ACCESS_TOKEN')

    with open(image_path, 'rb') as image_file:
        response = requests.post(
            f'{GRAPH}/{page_id}/photos',
            data={
                'access_token': token,
                'caption': caption,
            },
            files={
                'source': ('challenge.png', image_file, 'image/png'),
            },
            timeout=120,
        )

    if not response.ok:
        raise RuntimeError(
            f'Facebook publish failed: {response.status_code} {response.text}'
        )
    return response.json()


def instagram_image(image_url, caption):
    user_id = env('INSTAGRAM_USER_ID')
    token = env('INSTAGRAM_ACCESS_TOKEN')

    response = requests.post(
        f'{GRAPH}/{user_id}/media',
        data={
            'image_url': image_url,
            'caption': caption,
            'access_token': token,
        },
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(
            f'Instagram container creation failed: {response.status_code} {response.text}'
        )

    creation_id = response.json().get('id')
    if not creation_id:
        raise RuntimeError(f'Instagram returned no creation id: {response.text}')

    for _ in range(30):
        status = requests.get(
            f'{GRAPH}/{creation_id}',
            params={
                'fields': 'status_code',
                'access_token': token,
            },
            timeout=60,
        )
        if status.ok:
            status_code = status.json().get('status_code')
            if status_code in ('FINISHED', 'PUBLISHED'):
                break
            if status_code == 'ERROR':
                raise RuntimeError(
                    f'Instagram media processing failed: {status.text}'
                )
        time.sleep(3)
    else:
        raise RuntimeError('Instagram media processing timed out.')

    response = requests.post(
        f'{GRAPH}/{user_id}/media_publish',
        data={
            'creation_id': creation_id,
            'access_token': token,
        },
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(
            f'Instagram publish failed: {response.status_code} {response.text}'
        )
    return response.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=int)
    parser.add_argument('--facebook', action='store_true')
    parser.add_argument('--instagram', action='store_true')
    parser.add_argument('--both', action='store_true')
    args = parser.parse_args()

    state_path = ROOT / 'state.json'
    state = (
        json.loads(state_path.read_text(encoding='utf-8'))
        if state_path.exists()
        else {'next_index': 1, 'history': []}
    )

    index = args.index or state['next_index']
    if index > DATA['total']:
        index = 1

    challenge, image, caption_file = generate(index)
    caption = caption_file.read_text(encoding='utf-8')

    results = {
        'index': index,
        'id': challenge['id'],
        'facebook': None,
        'instagram': None,
    }

    # Instagram needs a public image URL. Stage the image as an
    # unpublished Facebook Page photo and use its temporary CDN URL.
    # If both are requested, publish the normal Facebook post after staging.
    staged_photo_id = None
    if args.instagram or args.both:
        staged_photo_id, public_image_url = facebook_stage_image(image)
        results['instagram_image_source'] = 'facebook_cdn_staging'
        results['staged_facebook_photo_id'] = staged_photo_id
        results['instagram_public_image_url'] = public_image_url

    if args.facebook or args.both:
        results['facebook'] = facebook_photo(image, caption)

    if args.instagram or args.both:
        results['instagram'] = instagram_image(public_image_url, caption)

    if not (args.facebook or args.instagram or args.both):
        print(json.dumps({
            'generated': str(image),
            'caption': str(caption_file),
            'index': index,
        }, indent=2))
        return

    state['next_index'] = index + 1
    state.setdefault('history', []).append({
        'index': index,
        'id': challenge['id'],
        'results': results,
        'timestamp': int(time.time()),
    })
    state_path.write_text(json.dumps(state, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
