from django import template
register = template.Library()

from ..models import ExchangeTransaction

@register.filter
def get_status_verbose(status_code):
    for sc in ExchangeTransaction.STATUS_CHOICES:
        if sc[0] == status_code:
            return sc[1]
    return 'unknown status'

@register.filter
def mul(value, arg):
    return value*arg

@register.filter
def div(value, arg):
    return round(value/arg, 2)
