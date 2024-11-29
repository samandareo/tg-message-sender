from django.urls import path
from register_account import views

urlpatterns = [
    path('create_session/', views.create_session, name='create_session'),
    path('enter_code/<str:phone_number>/<int:api_id>/<str:api_hash>/', 
         views.enter_code, name='enter_code'),
]