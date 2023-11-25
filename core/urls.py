from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .forms import LoginForm


app_name = 'core'

urlpatterns = [
    path('', views.index, name= 'index'),
    path('send/', views.send, name='send'),
    path('open/', views.open, name='open'),
    path('close/', views.close, name='close'),
    path('voice/', views.voice, name='voice'),
    path('login/', auth_views.LoginView.as_view(template_name= 'core/login.html',authentication_form = LoginForm), name='login'),
    path('logout/', views.logout_view, name='logout'),
]