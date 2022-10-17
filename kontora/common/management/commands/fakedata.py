from itertools import cycle
from random import randrange

from django.core.management import BaseCommand

from billing.models import Debt
from contracts.models import Contract
from customers.models import Customer


class Command(BaseCommand):
    help = "Create fake data for the development environment."

    number_of_customers = 100
    number_of_debts_per_customer = 6

    number_of_contracts_per_customer = 100
    number_of_debts_per_contract = 3

    def handle(self, *args, **options):
        def amount_generator():
            while True:
                yield randrange(1, 500)

        amount = amount_generator()

        Customer.objects.bulk_create((Customer(fullname=f"John Doe {i}") for i in range(self.number_of_customers)))
        customers = Customer.objects.all()
        infinity_customers = cycle(customers)

        Debt.objects.bulk_create(
            (Debt(customer=next(infinity_customers), amount=next(amount)) for _ in range(self.number_of_customers * self.number_of_debts_per_customer))
        )

        Contract.objects.bulk_create(
            (Contract(customer=next(infinity_customers)) for _ in range(self.number_of_customers * self.number_of_contracts_per_customer))
        )
        contracts = Contract.objects.all()
        infinity_contracts = cycle(contracts)

        Debt.objects.bulk_create(
            (
                Debt(contract=next(infinity_contracts), amount=next(amount))
                for _ in range(self.number_of_customers * self.number_of_contracts_per_customer * self.number_of_debts_per_contract)
            )
        )
