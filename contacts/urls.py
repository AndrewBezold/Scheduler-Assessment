from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("close/auth/", views.close_oauth),
    path("close/redirect/", views.close_redirect),
    path("close/contacts/create/", views.close_create_contact)
]