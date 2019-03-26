from django.contrib import admin
from .models import Coin, ExchangeTransaction, CoinAddressIn, CoinAddressOut, CoinAddress, CoinBalance, Pair, Rate, ExternalRate, Chat


class ChatAdmin(admin.ModelAdmin):
    list_display = ('date', 'transaction', 'ip', 'msg', 'date',)

    def msg(self, obj):
        return '{}...'.format(obj.msg[:10])
    msg.short_description = 'Msg'



class ExchangeTransactionAdmin(admin.ModelAdmin):
    list_display = ('fromto', 'created_at', 'status',
                    'pay_address_address', 'payout_address_address',
                    'coins_received', 'coins_sent', 'rate',)

    def pay_address_address(self, obj):
        return '{}...'.format(obj.in_address.address[:10])
    pay_address_address.short_description = 'From'

    def payout_address_address(self, obj):
        return '{}...'.format(obj.out_address.address[:10])
    payout_address_address.short_description = 'To'

    def fromto(self, obj):
        return obj.__str__()
    fromto.short_description = 'From-To'


class CoinAdmin(admin.ModelAdmin):
    list_display = ('name', 'balance', 'rpc_url')

    def balance(self, obj):
        return obj.info.get('balance', 'N/A')


class PairAdmin(admin.ModelAdmin):
    list_display = ('selfie', 'rate')

    def selfie(self, obj):
        return obj.__str__()

    def rate(self, obj):
        try:
            _rate = Rate.objects.filter(pair=obj).order_by('-date')\
                        .first().rate
        except:
            _rate = None
        return _rate


admin.site.register(Coin, CoinAdmin)
admin.site.register(ExchangeTransaction, ExchangeTransactionAdmin)
admin.site.register(CoinAddressIn)
admin.site.register(CoinAddressOut)
admin.site.register(CoinBalance)
admin.site.register(Pair, PairAdmin)
admin.site.register(Rate)
admin.site.register(ExternalRate)
admin.site.register(Chat, ChatAdmin)
