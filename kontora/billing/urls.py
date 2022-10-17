from django.urls import path

from billing import views

app_name = "billing"
urlpatterns = [
    path("debt/per-custmer-total", views.debt_per_customer_total, name="debt_per_customer_total")
]
