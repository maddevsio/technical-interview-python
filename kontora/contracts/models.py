import uuid

from django.db import models


class Contract(models.Model):
    identifier = models.UUIDField(default=uuid.uuid4)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="contracts")

    def __str__(self):
        return f"{self.identifier}"
