import os
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
import django
django.setup()

from libraries.models import Map

API = 'https://valorant-api.com/v1/maps'


def run():
    try:
        resp = requests.get(API, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print('Failed to fetch maps:', e)
        return

    payload = resp.json()
    items = payload.get('data') or []
    print(f'Found {len(items)} map entries')

    for it in items:
        # robust key handling depending on API version
        name = it.get('displayName') or it.get('name') or ''
        desc = it.get('description') or ''
        # try several image keys used in the API
        image = it.get('splash') or it.get('displayIcon') or it.get('listViewIcon') or it.get('mapUrl') or ''

        if not name:
            continue

        mp, created = Map.objects.get_or_create(name=name, defaults={'description': desc, 'image_url': image})
        if not created:
            mp.description = desc or mp.description
            mp.image_url = image or mp.image_url
            mp.save()

        # handle game modes if provided by API
        modes_raw = it.get('gameModes') or it.get('modes') or it.get('gameMode') or it.get('game_mode') or []
        mode_names = []
        if isinstance(modes_raw, list):
            for m in modes_raw:
                if isinstance(m, dict):
                    n = m.get('displayName') or m.get('name') or ''
                else:
                    n = str(m)
                if n:
                    mode_names.append(n)
        elif isinstance(modes_raw, str):
            mode_names = [modes_raw]

        if mode_names:
            from libraries.models import Mode
            mp.modes.clear()
            for mn in mode_names:
                mode_obj, _ = Mode.objects.get_or_create(name=mn)
                mp.modes.add(mode_obj)

        print(('Created' if created else 'Updated'), name, 'modes:', ','.join(mode_names) if mode_names else 'none')

    print('Done')


if __name__ == '__main__':
    run()
