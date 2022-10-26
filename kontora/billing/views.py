from django.db.models import Q
from django.http import JsonResponse

from billing.models import Debt
from customers.models import Customer


# Comment on every view
# - Is there any problem?
# - What are the limitation of each view?


def list_debt_per_customer_total(request):
    customers = Customer.objects.all()

    result = []
    for customer in customers:
        data = {
            "customer_id": customer.pk,
            "debts_total": sum(customer.debts.values_list("amount", flat=True)),
            "contract_debts_total": sum(sum(c.debts.values_list("amount", flat=True)) for c in customer.contracts.all())
        }
        result.append(data)

    return JsonResponse(result, safe=False)


def get_total_debt_by_customer_id(request, customer_id: int):
    customer = Customer.objects.get(pk=customer_id)

    total = sum(customer.debts.values_list("amount", flat=True))
    total += sum(sum(c.debts.values_list("amount", flat=True)) for c in customer.contracts.all())
    return JsonResponse({
        "customer_id": customer.pk,
        "total": total,
    })


def get_debts_by_customer_id(request, customer_id: int):
    debts = Debt.objects.filter(
        Q(customer_id=customer_id) | Q(contract__customer_id=customer_id),
    )

    result = []
    for debt in debts:
        data = {
            "debt_id": debt.pk,
            "amount": float(debt.amount),
            "contract_id": debt.contract_id,
            "created_at": str(debt.created_at),
            "updated_at": str(debt.created_at),
        }
        result.append(data)

    return JsonResponse(result, safe=False)
