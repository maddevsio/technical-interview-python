from django.db import models


class Debt(models.Model):
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, null=True, blank=True)
    contract = models.ForeignKey("contracts.Contract", on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        fullname = (self.customer and self.customer.fullname) or (self.contract and self.contract.customer.fullname)
        return f"{fullname} ({self.amount})"