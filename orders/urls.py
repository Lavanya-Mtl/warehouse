from django.urls import path
from . import views

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path("new/", views.OrderCreateView.as_view(), name="order-create"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("<int:pk>/edit/", views.OrderUpdateView.as_view(), name="order-update"),
    path(
        "<int:pk>/transition/<str:new_status>/",
        views.order_transition,
        name="order-transition",
    ),
    path("<int:pk>/re-recommend/", views.order_re_recommend, name="order-re-recommend"),
    path("dashboard", views.DashboardView.as_view(), name="dashboard"),
]