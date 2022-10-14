from django.contrib import admin

from billing.models import Debt


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    ...
