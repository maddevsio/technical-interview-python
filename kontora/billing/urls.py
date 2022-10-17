from django.urls import path

from billing import views

app_name = "billing"
urlpatterns = [
    path("debt/list-per-custmer-total", views.list_debt_per_customer_total, name="list_debt_per_customer_total"),
    path("debt/<int:custormer_id/total>", views.get_total_debt_by_customer_id, name="get_total_debt_by_customer_id"),
    path("debt/<int:custormer_id/list>", views.get_debts_by_customer_id, name="get_debts_by_customer_id"),
]
