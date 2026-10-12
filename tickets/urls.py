from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('tickets/', views.ticket_list_view, name='ticket_list'),
    path('tickets/new/', views.ticket_create_view, name='ticket_create'),
    path('tickets/<str:ticket_id>/', views.ticket_detail_view, name='ticket_detail'),
    path('tickets/<str:ticket_id>/edit/', views.ticket_update_view, name='ticket_update'),
    path('tickets/<str:ticket_id>/delete/', views.ticket_delete_view, name='ticket_delete'),
    path('register/', views.register_view, name='register'),
]
