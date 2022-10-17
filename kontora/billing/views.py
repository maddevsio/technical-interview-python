from django.http import JsonResponse

from customers.models import Customer


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
