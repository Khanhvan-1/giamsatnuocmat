from django.urls import path
from . import views

urlpatterns = [

    # API ĐIỂM QUAN TRẮC
    path('points/', views.get_points, name='points'),

    # CHATBOT
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chat-history/', views.get_chat_history, name='chat_history'),
    path('clear-chat-history/', views.clear_chat_history, name='clear_chat_history'),
    path('new-chat/', views.new_chat, name='new_chat'),
    path('report/', views.report_view, name='report'),

    path(
        'report-data/',
        views.get_report_data,
        name='report_data'
    ),
    path(
        'rivers/',
        views.get_rivers,
        name='rivers'
    ),
    path(
        'reports/latest/',
        views.get_latest_reports,
        name='latest_reports'
    ),
    # NOMINATIM
    path(
        'proxy/nominatim/search/',
        views.proxy_nominatim_search,
        name='proxy_search'
    ),

    path(
        'proxy/nominatim/reverse/',
        views.proxy_nominatim_reverse,
        name='proxy_reverse'
    ),
]