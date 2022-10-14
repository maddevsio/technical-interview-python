from django.db import models


class Customer(models.Model):
    fullname = models.CharField(max_length=255)

    def __str__(self):
        return self.fullname
