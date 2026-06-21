from django.urls import path
from . import views

urlpatterns = [

    path('login/', views.login_view, name='login'),

    path('register/', views.register_view, name='register'),

    path('points/', views.get_points),

    path('dashboard/', views.dashboard),

    path("chatbot/", views.chatbot, name="chatbot"),

    path("chat-history/", views.get_chat_history),

    path("clear-chat-history/", views.clear_chat_history),

    path("api/new-chat/", views.new_chat),

    path('proxy/nominatim/search/', views.proxy_nominatim_search, name='proxy_search'),

    path('proxy/nominatim/reverse/', views.proxy_nominatim_reverse, name='proxy_reverse'),
    
]