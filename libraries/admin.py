from django.contrib import admin
from .models import Role, Agent, Ability, Weapon, Map, RiotAccount

admin.site.register(Role)
admin.site.register(Agent)
admin.site.register(Ability)
admin.site.register(Weapon)
admin.site.register(Map)
admin.site.register(RiotAccount)
