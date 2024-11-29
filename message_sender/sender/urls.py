from django.urls import path
from sender import views

urlpatterns = [
    path('', views.index, name='index'),
    path('message-sender/', views.message_sender, name='message_sender'),
    path('stop-sender/', views.stop_sender, name='stop_sender'),
    path('check-status/', views.check_status, name='check_status'),
]