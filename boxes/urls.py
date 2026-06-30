from django.urls import path
from . import views

urlpatterns = [
    path("", views.BoxListView.as_view(), name="box-list"),
    path("new/", views.BoxCreateView.as_view(), name="box-create"),
    path("<int:pk>/edit/", views.BoxUpdateView.as_view(), name="box-update"),
    path("<int:pk>/delete/", views.BoxDeleteView.as_view(), name="box-delete"),
]