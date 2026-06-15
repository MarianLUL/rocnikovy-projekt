import os
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
import django
django.setup()

from libraries.models import Weapon

API = 'https://valorant-api.com/v1/weapons'


def safe_get(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur


def run():
    try:
        resp = requests.get(API, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print('Failed to fetch weapons:', e)
        return

    payload = resp.json()
    items = payload.get('data') or []
    print(f'Found {len(items)} weapons')

    for it in items:
        name = it.get('displayName') or it.get('name') or ''
        desc = it.get('description') or ''
        # prefer explicit top-level icons only (base model)
        image = it.get('displayIcon') or it.get('displayIconSmall') or it.get('killStreamIcon') or ''

        weapon_type = it.get('category') or safe_get(it, 'shopData', 'category') or ''
        cost = safe_get(it, 'shopData', 'cost')

        # weaponStats may hold magazine size and fire rate
        weapon_stats = it.get('weaponStats') or {}
        magazine = weapon_stats.get('magazineSize') or weapon_stats.get('magazine')
        fire_rate = None
        if weapon_stats:
            # try a few keys
            fire_rate = weapon_stats.get('fireRate') or weapon_stats.get('rateOfFire') or weapon_stats.get('firingRate')

        # damage ranges: list of {rangeStartMeters, headDamage, bodyDamage, legDamage}
        damage_ranges = weapon_stats.get('damageRanges') or weapon_stats.get('damageRange') or []
        damage_profile = None
        max_range = None
        if isinstance(damage_ranges, list) and damage_ranges:
            damage_profile = []
            for dr in damage_ranges:
                if isinstance(dr, dict):
                    entry = {
                        'rangeStartMeters': dr.get('rangeStartMeters') or dr.get('rangeStart') or None,
                        'head': dr.get('headDamage') or dr.get('head') or None,
                        'body': dr.get('bodyDamage') or dr.get('body') or None,
                        'leg': dr.get('legDamage') or dr.get('leg') or None,
                    }
                    damage_profile.append(entry)
            # estimate max range as last rangeStartMeters
            last = damage_profile[-1]
            max_range = last.get('rangeStartMeters')

        # movement/run speed multiplier when wielding this weapon
        run_speed_multiplier = weapon_stats.get('runSpeedMultiplier') or weapon_stats.get('runSpeed') or None

        # firing modes or alt-fire info
        firing_modes = weapon_stats.get('firingPattern') or weapon_stats.get('fireModes') or weapon_stats.get('firingModes') or None

        # other stats
        wall_pen = weapon_stats.get('wallPenetration') or weapon_stats.get('wall_penetration') or weapon_stats.get('wall') or None
        equip_time = weapon_stats.get('equipTimeSeconds') or weapon_stats.get('equip_time_seconds') or None
        reload_time = weapon_stats.get('reloadTimeSeconds') or weapon_stats.get('reload_time_seconds') or None
        ads = weapon_stats.get('adsStats') or weapon_stats.get('ads_stats') or {}
        ads_zoom = None
        if isinstance(ads, dict):
            ads_zoom = ads.get('zoomMultiplier') or ads.get('zoom') or ads.get('zoomMultiplier')

        metadata = {}
        # keep some useful raw fields but skip full skins list (we want base model only)
        for k in ('uuid', 'displayName', 'category', 'shopData', 'weaponStats'):
            if k in it:
                try:
                    metadata[k] = it[k]
                except Exception:
                    metadata[k] = str(it[k])
        # record whether skins exist, but do not store the full skins array
        if it.get('skins'):
            metadata['has_skins'] = True
        # normalize shop category into a top-level metadata key for templates
        shop = it.get('shopData') or {}
        sc = shop.get('category') or shop.get('categoryText')
        if sc:
            metadata['shop_category'] = sc

        if not name:
            continue

        defaults = {
            'description': desc,
            'image_url': image,
            'weapon_type': weapon_type,
            'cost': cost or None,
            'magazine': magazine or None,
            'fire_rate': str(fire_rate) if fire_rate else '',
            'metadata': metadata,
            'damage_profile': damage_profile,
            'max_range_m': max_range,
            'run_speed_multiplier': float(run_speed_multiplier) if run_speed_multiplier is not None else None,
            'firing_modes': firing_modes,
            'wall_penetration': wall_pen or '',
            'equip_time_seconds': float(equip_time) if equip_time is not None else None,
            'reload_time_seconds': float(reload_time) if reload_time is not None else None,
            'ads_zoom_multiplier': float(ads_zoom) if ads_zoom is not None else None,
        }

        w, created = Weapon.objects.get_or_create(name=name, defaults=defaults)
        if not created:
            w.description = desc or w.description
            w.image_url = image or w.image_url
            w.weapon_type = weapon_type or w.weapon_type
            w.cost = cost or w.cost
            w.magazine = magazine or w.magazine
            w.fire_rate = str(fire_rate) if fire_rate else w.fire_rate
            # merge metadata
            old_meta = w.metadata or {}
            old_meta.update(metadata)
            w.metadata = old_meta
            # update new fields
            w.damage_profile = damage_profile or w.damage_profile
            w.max_range_m = max_range or w.max_range_m
            w.run_speed_multiplier = float(run_speed_multiplier) if run_speed_multiplier is not None else w.run_speed_multiplier
            w.firing_modes = firing_modes or w.firing_modes
            w.save()

        print(('Created' if created else 'Updated'), name)

    print('Done')


if __name__ == '__main__':
    run()
