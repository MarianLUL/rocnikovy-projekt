from django.shortcuts import render, get_object_or_404
from .models import Role, Agent
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
import requests
import secrets
from django.utils import timezone


def index(request):
    roles = Role.objects.all()
    role_id = request.GET.get('role')
    if role_id:
        agents = Agent.objects.filter(role_id=role_id).order_by('name')
    else:
        agents = Agent.objects.all().order_by('name')
    return render(request, 'agents/index.html', {'roles': roles, 'agents': agents, 'selected_role': role_id})


def agent_detail(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    roles = Role.objects.all()
    return render(request, 'agents/agent_detail.html', {'agent': agent, 'roles': roles})


def home(request):
    """Homepage with image-rich cards for the main sections."""
    from .models import Agent, Weapon, Map

    featured_agent = Agent.objects.order_by('name').first()
    featured_weapon = Weapon.objects.order_by('name').first()
    featured_map = Map.objects.order_by('name').first()

    return render(request, 'agents/home.html', {
        'featured_agent': featured_agent,
        'featured_weapon': featured_weapon,
        'featured_map': featured_map,
    })


def weapons_list(request):
    from .models import Weapon
    weapons = Weapon.objects.all().order_by('name')
    return render(request, 'agents/weapons_list.html', {'weapons': weapons})


def weapon_detail(request, pk):
    from .models import Weapon
    weapon = get_object_or_404(Weapon, pk=pk)
    return render(request, 'agents/weapon_detail.html', {'weapon': weapon})


def maps_list(request):
    from .models import Map, Mode
    modes = Mode.objects.all().order_by('name')
    maps_by_mode = []
    for m in modes:
        maps_for_mode = m.maps.all().order_by('name')
        maps_by_mode.append((m, maps_for_mode))

    uncategorized = Map.objects.filter(modes__isnull=True).order_by('name')
    return render(request, 'agents/maps_list.html', {'maps_by_mode': maps_by_mode, 'uncategorized': uncategorized, 'modes': modes})


def map_detail(request, pk):
    from .models import Map
    mp = get_object_or_404(Map, pk=pk)
    return render(request, 'agents/map_detail.html', {'map': mp})


def logout_view(request):
    """Log the user out (accepts GET) and redirect to home."""
    auth_logout(request)
    return redirect('/')


def register_view(request):
    """Allow new users to create a regular account."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'agents/register.html', {'form': form})


@login_required
def connect_riot(request):
    """Start OAuth flow to connect a Riot account to the logged-in user."""
    authorize_url = getattr(settings, 'RIOT_OAUTH_AUTHORIZE_URL', 'https://example.com/authorize')
    client_id = getattr(settings, 'RIOT_CLIENT_ID', '')
    redirect_uri = getattr(settings, 'RIOT_REDIRECT_URI', '')

    if not client_id or not redirect_uri:
        return render(request, 'agents/connect_riot.html', {'error': 'Riot OAuth not configured. Set RIOT_CLIENT_ID and RIOT_REDIRECT_URI in settings.'})

    state = secrets.token_urlsafe(16)
    request.session['riot_oauth_state'] = state
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid',
        'state': state,
    }
    from urllib.parse import urlencode
    url = f"{authorize_url}?{urlencode(params)}"
    return redirect(url)


def riot_callback(request):
    """OAuth2 callback to finish linking Riot account. Requires login."""
    code = request.GET.get('code')
    state = request.GET.get('state')
    saved_state = request.session.get('riot_oauth_state')
    if state != saved_state:
        return render(request, 'agents/connect_riot.html', {'error': 'Invalid OAuth state'})

    if not request.user.is_authenticated:
        login_url = getattr(settings, 'LOGIN_URL', '/admin/login/')
        return redirect(f"{login_url}?next={request.path}")

    token_url = getattr(settings, 'RIOT_OAUTH_TOKEN_URL', 'https://example.com/token')
    client_id = getattr(settings, 'RIOT_CLIENT_ID', '')
    client_secret = getattr(settings, 'RIOT_CLIENT_SECRET', '')
    redirect_uri = getattr(settings, 'RIOT_REDIRECT_URI', '')

    if not client_id or not client_secret or not redirect_uri:
        return render(request, 'agents/connect_riot.html', {'error': 'Riot OAuth tokens not configured.'})

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret,
    }

    resp = requests.post(token_url, data=data, timeout=15)
    if resp.status_code != 200:
        return render(request, 'agents/connect_riot.html', {'error': 'Token exchange failed', 'details': resp.text})
    token_data = resp.json()
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in')

    userinfo_url = getattr(settings, 'RIOT_OAUTH_USERINFO_URL', '')
    riot_id = ''
    display_name = ''
    headers = {'Authorization': f'Bearer {access_token}'} if access_token else {}
    if userinfo_url:
        r = requests.get(userinfo_url, headers=headers, timeout=10)
        if r.status_code == 200:
            info = r.json()
            riot_id = info.get('sub') or info.get('id') or ''
            display_name = info.get('name') or info.get('displayName') or ''

    from .models import RiotAccount
    ra, _ = RiotAccount.objects.get_or_create(user=request.user)
    ra.riot_id = riot_id
    ra.display_name = display_name
    ra.access_token = access_token or ''
    ra.refresh_token = refresh_token or ''
    if expires_in:
        ra.token_expires = timezone.now() + timezone.timedelta(seconds=int(expires_in))
    ra.save()

    return render(request, 'agents/connect_riot.html', {'success': True, 'riot_account': ra})
