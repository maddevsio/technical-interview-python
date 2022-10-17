from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("billing/", include("billing.urls")),
    path("contracts/", include("contracts.urls")),
    path("customers/", include("customers.urls")),
]
