import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_library.settings')
django.setup()

from django.contrib.auth import get_user_model
from libraries.models import Role, Agent, Ability

API_URL = 'https://valorant-api.com/v1/agents'


def fetch_agents():
    resp = requests.get(API_URL, timeout=30)
    resp.raise_for_status()
    return resp.json().get('data', [])


def run():
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        print('Created superuser: admin / adminpass')
    else:
        print('Superuser already exists')

    agents_data = fetch_agents()

    roles_cache = {}
    created_agents = 0
    updated_agents = 0

    for a in agents_data:
        # only import playable characters
        if not a.get('isPlayableCharacter'):
            continue

        name = a.get('displayName') or a.get('display_name') or 'Unknown'
        uuid = a.get('uuid') or ''
        real_name = a.get('developerName') or ''
        role_info = a.get('role') or {}
        role_name = role_info.get('displayName') or role_info.get('name') or 'Unknown'
        description = a.get('description') or ''
        image_url = a.get('displayIcon') or a.get('bustPortrait') or a.get('fullPortrait') or ''
        full_portrait = a.get('fullPortraitV2') or a.get('fullPortrait') or a.get('bustPortrait') or ''

        # get or create role
        role = roles_cache.get(role_name)
        if not role:
            role, _ = Role.objects.get_or_create(name=role_name, defaults={'description': ''})
            roles_cache[role_name] = role

        # include uuid and real_name in description (without changing models)
        full_description = description or ''
        meta_lines = []
        if real_name:
            meta_lines.append(f'Real name: {real_name}')
        if uuid:
            meta_lines.append(f'UUID: {uuid}')
        if meta_lines:
            full_description = (full_description + '\n\n' + '\n'.join(meta_lines)).strip()

        agent_obj, was_created = Agent.objects.get_or_create(
            name=name,
            defaults={'role': role, 'description': full_description, 'image_url': image_url, 'full_portrait_url': full_portrait}
        )

        if was_created:
            created_agents += 1
        else:
            # update fields if changed
            changed = False
            if agent_obj.role != role:
                agent_obj.role = role
                changed = True
            if image_url and agent_obj.image_url != image_url:
                agent_obj.image_url = image_url
                changed = True
            if full_description and agent_obj.description != full_description:
                agent_obj.description = full_description
                changed = True
            if full_portrait and getattr(agent_obj, 'full_portrait_url', '') != full_portrait:
                agent_obj.full_portrait_url = full_portrait
                changed = True
            if changed:
                agent_obj.save()
                updated_agents += 1

        # replace abilities
        Ability.objects.filter(agent=agent_obj).delete()
        for ability in a.get('abilities', []) or []:
            ab_name = ability.get('displayName') or ability.get('name') or ''
            ab_desc = ability.get('description') or ''
            slot = ability.get('slot') or ''
            is_ultimate = slot.lower() == 'ultimate' if isinstance(slot, str) else False
            Ability.objects.create(agent=agent_obj, name=ab_name, key=slot, description=ab_desc, is_ultimate=is_ultimate)

    total = created_agents + updated_agents
    print(f'Imported/updated {total} agents ({created_agents} created, {updated_agents} updated)')


if __name__ == '__main__':
    run()
