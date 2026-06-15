from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

app_name = 'agents'

urlpatterns = [
    path('', views.home, name='home'),
    path('agents/', views.index, name='index'),
    path('agents/<int:pk>/', views.agent_detail, name='agent_detail'),
    path('weapons/', views.weapons_list, name='weapons_list'),
    path('weapons/<int:pk>/', views.weapon_detail, name='weapon_detail'),
    path('maps/', views.maps_list, name='maps_list'),
    path('maps/<int:pk>/', views.map_detail, name='map_detail'),
    path('accounts/profile/', RedirectView.as_view(url='/', permanent=False), name='profile'),
    # Basic auth routes (simple login/logout). Replaced Riot OAuth with local auth.
    path('accounts/login/', auth_views.LoginView.as_view(template_name='agents/login.html'), name='login'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/logout/', views.logout_view, name='logout'),
]
