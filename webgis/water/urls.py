from django.urls import path
from . import views

urlpatterns = [

path('points/',views.get_points),

path('dashboard/',views.dashboard),

path("chatbot/", views.chatbot, name="chatbot"),

path("chat-history/", views.get_chat_history),

path("clear-chat-history/", views.clear_chat_history),

]