from django.contrib import admin

from contracts.models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "identifier",
        "customer_display",
    ]

    @admin.display(description="Customer")
    def customer_display(self, obj):
        return obj.customer.fullname
