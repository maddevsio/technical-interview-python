from django.db import models


class Customer(models.Model):
    fullname = models.CharField(max_length=255)
    email = models.EmailField(max_length=256)

    invite_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.fullname
