from datetime import datetime, timedelta
from django.db import models
from django.db.models import Q


class ExchangeTransactionManager(models.Manager):

    def get_waiting_transactions(self):
        from .models import ExchangeTransaction
        """ Gets for transactions waiting for payment """
        ts = self.filter(
                Q(status__lte=ExchangeTransaction.WAITING_FOR_WALLET)|
                Q(is_failed=True)
            )
        return ts

    def get_recents(self):
        from .models import ExchangeTransaction
        return self.filter(status=ExchangeTransaction.\
            TRANSACTION_COMPLETE).order_by('-updated_at').all()[:7]


class CoinBalanceManager(models.Manager):

    def get_last_balance(self, coin):
        balance = self.filter(coin=coin).order_by("-date").first()
        if balance:
            return balance.balance
        else:
            return 0


class CoinAddressInManager(models.Manager):

    def create_payment_address(self, coin):
        """ Gets for existing available payment
            address or creates new if no
        """

        address = coin.create_new_address()
        payment_address = self.create(address=address, coin=coin)
        return payment_address


class ChatManager(models.Manager):

    def is_flood(self, ip):
        """ Allows 2 messages per minute """
        tl = datetime.now() - timedelta(minutes=1)
        c = self.filter(Q(ip=ip)&Q(date__gte=tl)).count()
        if c > 1:
            return True
        return False
