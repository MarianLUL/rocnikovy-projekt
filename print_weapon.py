import os, sys, json
sys.path.insert(0, r'c:\Users\marian\Documents\Django\valorant_library')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','school_library.settings')
import django
django.setup()
from libraries.models import Weapon
w = Weapon.objects.get(pk=2)
print(json.dumps({'name':w.name,'cost':w.cost,'magazine':w.magazine,'fire_rate':w.fire_rate,'max_range_m':w.max_range_m,'run_speed_multiplier':w.run_speed_multiplier,'wall_penetration':w.wall_penetration,'image_url':w.image_url,'metadata': w.metadata}, default=str, ensure_ascii=False))
