from django.urls import path
from . import views

urlpatterns = [
    path('', views.board_list, name='board_list'),
    path('add/', views.board_add, name='board_add'),
    path('edit/<int:pk>/', views.board_edit, name='board_edit'),
    path('delete/<int:pk>/', views.board_delete, name='board_delete'),
    path('check_all/', views.board_check_all, name='board_check_all'),
    path('toggle/<int:board_id>/<int:relay_num>/', views.toggle_relay, name='toggle_relay'),
    path('all_on/', views.turn_all_on, name='turn_all_on'),
    path('all_off/', views.turn_all_off, name='turn_all_off'),
    path('schedule/', views.schedule_settings, name='schedule_settings'),
    path('sync_schedule/', views.sync_schedule, name='sync_schedule'),
]