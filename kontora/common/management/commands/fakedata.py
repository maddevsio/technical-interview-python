from itertools import cycle
from random import randrange

from django.core.management import BaseCommand

from billing.models import Debt
from contracts.models import Contract
from customers.models import Customer


class Command(BaseCommand):
    help = "Create fake data for the development environment."

    number_of_customers = 100
    number_of_debts_by_customer = 1000

    number_of_contracts = 100
    number_of_debts_by_contract = 100

    def handle(self, *args, **options):
        debts_count = self.number_of_contracts + self.number_of_debts_by_contract
        amount_list = (randrange(1000, 100000, debts_count) / 1000 for _ in range(debts_count))

        Customer.objects.bulk_create((Customer(fullname=f"John Doe {i}") for i in range(self.number_of_customers)))
        customers = Customer.objects.all()
        infinity_customers = cycle(customers)

        Debt.objects.bulk_create(
            (Debt(customer=next(infinity_customers), amount=next(amount_list)) for _ in range(self.number_of_contracts))
        )

        Contract.objects.bulk_create(
            (Contract(customer=next(infinity_customers)) for _ in range(self.number_of_debts_by_customer))
        )
        contracts = Contract.objects.all()
        infinity_contracts = cycle(contracts)

        Debt.objects.bulk_create(
            (
                Debt(contract=next(infinity_contracts), amount=next(amount_list))
                for _ in range(self.number_of_debts_by_contract)
            )
        )
