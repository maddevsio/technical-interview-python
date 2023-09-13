from celery import current_app
from django.core.mail import send_mail

from customers.models import Customer


# Comment on every task
# - Is there any problem?

@current_app.task()
def send_monthly_account_statements():
    customers = Customer.objects.filter(invite_sent=False)

    for customer in customers:
        send_mail(
            subject="Monthly Account Statement",
            message="Bla bla bla bla.",
            from_email="from@kontora.com",
            recipient_list=[customer.email],
            fail_silently=False,
        )

    customers.update(invite_sent=True)
