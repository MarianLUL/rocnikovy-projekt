from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Agent(models.Model):
    name = models.CharField(max_length=100)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='agents')
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    full_portrait_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Ability(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='abilities')
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    is_ultimate = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.agent.name} - {self.name}"


class Weapon(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    weapon_type = models.CharField(max_length=100, blank=True)
    cost = models.IntegerField(null=True, blank=True)
    magazine = models.IntegerField(null=True, blank=True)
    fire_rate = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    damage_profile = models.JSONField(null=True, blank=True)
    max_range_m = models.IntegerField(null=True, blank=True)
    run_speed_multiplier = models.FloatField(null=True, blank=True)
    firing_modes = models.JSONField(null=True, blank=True)
    wall_penetration = models.CharField(max_length=100, blank=True)
    equip_time_seconds = models.FloatField(null=True, blank=True)
    reload_time_seconds = models.FloatField(null=True, blank=True)
    ads_zoom_multiplier = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class Map(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    modes = models.ManyToManyField('Mode', blank=True, related_name='maps')

    def __str__(self):
        return self.name


class Mode(models.Model):
    """Represent a game mode in which a map may be playable (e.g., Competitive, Spike Rush)."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class RiotAccount(models.Model):
    """Stores linkage between a local user and a Riot account."""
    from django.conf import settings

    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='riot_account')
    riot_id = models.CharField(max_length=200, blank=True)
    display_name = models.CharField(max_length=200, blank=True)
    access_token = models.CharField(max_length=500, blank=True)
    refresh_token = models.CharField(max_length=500, blank=True)
    token_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} -> {self.display_name or self.riot_id}"
