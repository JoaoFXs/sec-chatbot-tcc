from django.urls import path
from . import views
from . import chat
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_login, name='logout'),
    path('home/', views.home, name='home'),
    path('train/', views.train, name='train'),
    path('chat/', chat.chat, name='chat'),
    path('download-calendario/', views.download_calendario, name='download_calendario'),
    path('download-exemplo-estagio/', views.download_doc_estagio, name='download-exemplo-estagio')
]
