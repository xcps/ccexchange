from hashlib import md5
from decimal import Decimal
import urllib
import traceback

from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField
from django.conf import settings

from .managers import ExchangeTransactionManager, ChatManager,\
                CoinAddressInManager, CoinBalanceManager
from .rpc_protocol import RPCCaller
from .utils import my_round
# Create your models here.


class Coin(models.Model):
    name = models.CharField(max_length=20, verbose_name=_('Name'))
    symbol = models.CharField(max_length=4, verbose_name=_('Symbol'),
                                default="")
    rpc_url = models.CharField(max_length=350, null=False, blank=False,
            unique=True, verbose_name=_('RPC url'),
            help_text=(_('In the form of http://127.0.0.1:9376')))
    rpc_username = models.CharField(max_length=32,
                verbose_name=_('RPC username'))
    rpc_password = models.CharField(max_length=50,
                verbose_name=_('RPC password'))
    wallet_passphrase = models.CharField(max_length=255, blank=True,
                                null=False,
                                verbose_name=_('Wallet passphrase'))
    info = JSONField(default=dict, blank=True, verbose_name=_('Info'))

    def save(self, *args, **kwargs):
        super(Coin, self).save(*args, **kwargs)
        if len(self.info) == 0:
            try:
                self.update_info()
            except:
                pass

    def get_balance(self):
        return self._get_rpc().get_balance()

    def update_info(self):
        info = self._get_rpc().get_info()
        info['networkhashps'] = self._get_rpc().get_network_hashes()
        balance = CoinBalance.objects.get_last_balance(self)
        current_balance = float(info["balance"])
        if balance != current_balance:
            CoinBalance.objects.create(balance=current_balance, \
                                        coin=self)
        self.info = info
        self.save()

    def create_new_address(self):
        return self._get_rpc().create_new_address()

    def send_coins(self, address, amount):
        return self._get_rpc().send_coins(address, amount,
                                            self.wallet_passphrase)

    def check_received(self, address):
        return self._get_rpc().check_received(address)

    def is_address_valid(self, address):
        return self._get_rpc().is_address_valid(address)

    def get_received_transactions(self):
        data = self._get_rpc().get_transactions()
        result = {}
        for t in data:
            if t["category"] == "receive":
                result[t["address"]] = {
                    "amount": t["amount"],
                    "confirmations": t["confirmations"],
                }
        return result

    def _get_rpc(self):
        if hasattr(self, 'rpc') == False:
            self.rpc = RPCCaller(self.rpc_username, self.rpc_password,
                                                    self.rpc_url)
        return self.rpc

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = _('Coin daemon')
        verbose_name_plural = _('Coin daemons')


class CoinBalance(models.Model):
    coin = models.ForeignKey(Coin, null=False, blank=False,
                                verbose_name=_('Coin'))
    balance = models.FloatField(default=0, null=False, blank=False,
                                verbose_name=_('Balance'))
    date = models.DateTimeField(auto_now_add=True,
                                verbose_name=_('Date'))
    objects = CoinBalanceManager()

    def __str__(self):
        return '{}: {} {}'.format(self.coin.symbol, self.balance, self.date)

    class Meta:
        verbose_name = _('Coin balance')
        verbose_name_plural = _('Coin balances')


class CoinAddress(models.Model):
    address = models.CharField(max_length=35, unique=True,
                verbose_name=_('Address'))
    coin = models.ForeignKey(Coin,
            null=False, blank=False, verbose_name=_('Coin'))

    def __str__(self):
        return '{}, {}'.format(self.address, self.coin.symbol)

    class Meta:
        abstract = True


class CoinAddressIn(CoinAddress):
    objects = CoinAddressInManager()

    class Meta:
        verbose_name = _('Coin address in')
        verbose_name_plural = _('Coin addresses in')


class CoinAddressOut(CoinAddress):
    pass

    class Meta:
        verbose_name = _('Coin address out')
        verbose_name_plural = _('Coin addresses out')


class Pair(models.Model):
    coin_from = models.ForeignKey(Coin, null=False, blank=False,
                                    related_name="coin_from",
                                    verbose_name=_('Coin from'))
    coin_to = models.ForeignKey(Coin, null=False, blank=False,
                                related_name="coin_to",
                                verbose_name=_('Coin to'))
    enabled = models.BooleanField(default=True, null=False,
                            blank=False, verbose_name=_('Enabled'))

    def get_rate(self):
        return Rate.objects.filter(pair=self).order_by('-date')\
                .first().rate

    def not_more_than(self):
        return "{}".format(my_round(Decimal(self.coin_to.get_balance()) / self.get_rate()))

    def get_rate_verbose(self):
        return "1 {} --> {} {}".format(
                self.coin_from.symbol,
                my_round(self.get_rate()),
                self.coin_to.symbol
            )

    def __str__(self):
        return '{} --> {}'.format(self.coin_from.symbol,
                                    self.coin_to.symbol)

    class Meta:
        verbose_name = _('Pair')
        verbose_name_plural = _('Pairs')


class Rate(models.Model):
    pair = models.ForeignKey(Pair, null=False, blank=False,
                                verbose_name=_('Pair'))
    rate = models.DecimalField(default=0, null=False,
                        max_digits=15, decimal_places=8,
                                verbose_name=_('Rate'))
    date = models.DateTimeField(auto_now_add=True,
                                verbose_name=_('Date'))

    def __str__(self):
        return '{}: {} ({})'.format(self.pair,
                                    self.rate,
                                    self.date)

    class Meta:
        verbose_name = _('Rate')
        verbose_name_plural = _('Rates')


class ExternalRate(models.Model):
    pair = models.ForeignKey(Pair, null=False, blank=False,
                                verbose_name=_('Pair'))
    rate = models.DecimalField(default=0, null=False,
                        max_digits=15, decimal_places=8,
                                verbose_name=_('Rate'))
    date = models.DateTimeField(auto_now_add=True,
                                verbose_name=_('Date'))
    source = models.CharField(max_length=20, null=False, blank=False,
                                verbose_name=_('Source'))

    def save(self, *args, **kwargs):
        super(ExternalRate, self).save(*args, **kwargs)
        rate = self.rate / Decimal(1 + settings.EXCHANGE_FEE)
        Rate.objects.create(pair=self.pair, rate=rate)

    def __str__(self):
        return '{}: {} ({})'.format(self.pair,
                                    self.rate,
                                    self.source,
                                    self.date)


class ExchangeTransaction(models.Model):
    """ Status """
    WAITING_FOR_PAYMENT = 1
    PAYMENT_RECEIVED = 2
    NO_BALANCE = 3
    WAITING_FOR_WALLET = 4
    TRANSACTION_COMPLETE = 5

    STATUS_CHOICES = (
        (WAITING_FOR_PAYMENT, _('Waiting for payment')),
        (PAYMENT_RECEIVED, _('Payment received')),
        (NO_BALANCE, _('No balance to send payment')),
        (WAITING_FOR_WALLET, _('Waiting for wallet')),
        (TRANSACTION_COMPLETE, _('Transaction complete')),
    )

    pair = models.ForeignKey(Pair, null=False, blank=False,
                            verbose_name=_('Pair'))
    in_address = models.ForeignKey(CoinAddressIn, null=False,
                                    blank=False,
                                    verbose_name=_('Pay in address'),
                                    related_name="in_address")
    out_address = models.ForeignKey(CoinAddressOut, null=False,
                        blank=False,
                        verbose_name=_('Pay out address'),
                        related_name="out_address")
    coins_received = models.DecimalField(default=0, null=False,
                        max_digits=15, decimal_places=8,
                        blank=False, verbose_name=_('Coins received'))
    coins_sent = models.DecimalField(default=0, null=False,
                            blank=False,
                            max_digits=15, decimal_places=8,
                                    verbose_name=_('Coins sent'))
    rate = models.DecimalField(default=0, null=False,
                        max_digits=15, decimal_places=8,
                                    verbose_name=_('Rate'))
    commission = models.FloatField(default=0, null=False, blank=False,
                                    verbose_name=_('Commission'))
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES,
                                    default=WAITING_FOR_PAYMENT,
                                    verbose_name=_('Status'))
    is_failed = models.BooleanField(default=False, null=False,
                                                    blank=False)
    error_message = models.CharField(default="", max_length=2048,
                                        blank=True, null=True)
    slug = models.SlugField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmations = models.PositiveSmallIntegerField(default=0,
                                    blank=False, null=False,
                                    verbose_name=_('Confirmations'))
    ip = models.CharField(max_length=15, null=False, blank=False)
    objects = ExchangeTransactionManager()

    def get_absolute_url(self):
       return reverse('transaction', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._get_unique_slug()
        super(ExchangeTransaction, self).save(*args, **kwargs)

    def _make_slug_from_text(self, text):
        md5ed = md5(text.encode()).hexdigest()
        return ''.join(sorted(md5ed))

    def _get_unique_slug(self):
        slug = self._make_slug_from_text(self.out_address.address)
        unique_slug = slug
        num = 1
        while ExchangeTransaction.objects.filter(slug=unique_slug).\
                exists():
            text = '{}-{}'.format(slug, num)
            unique_slug = self._make_slug_from_text(text)
            num += 1
        return unique_slug

    def get_current_rate(self):
        return self.pair.get_rate()


    def process_transaction(self):
        money = self.coins_received

        # decide how much to send
        rate = self.pair.get_rate()

        amount_to_send = Decimal(money) * Decimal(rate)
        import logging
        logging.error(amount_to_send)

        # check if we have such much
        balance = self.pair.coin_to.get_balance()
        if balance < amount_to_send:
            self.status = ExchangeTransaction\
                                    .NO_BALANCE
            self.save()
            return

        try:
            # send coins and update transaction info
            self.pair.coin_to.send_coins(
                            self.out_address.address,
                            amount_to_send)
            self.status = ExchangeTransaction\
                                .TRANSACTION_COMPLETE
            self.coins_sent = amount_to_send
            self.rate = rate
            self.is_failed = False
            self.save()
        except urllib.error.HTTPError as e:
            self.status = ExchangeTransaction\
                                .WAITING_FOR_WALLET
            self.is_failed = True
            if hasattr(e, "read"):
                self.error_message = '{}: {}'.format(e.read(), traceback.format_exc())
            self.save()
            return

        self.pair.coin_to.update_info()
        self.pair.coin_from.update_info()

    def __str__(self):
        return self.slug #'{} to {}'.format(self.coin_from.symbol,
                                #self.coin_to.symbol)

    class Meta:
        verbose_name = _('Exchange transaction')
        verbose_name_plural = _('Exchange transactions')
        ordering = ['-updated_at',]


class Chat(models.Model):
    transaction = models.ForeignKey(ExchangeTransaction, blank=False,
                        null=True, default=None,
                        verbose_name=_('Transaction'))
    msg = models.CharField(max_length=255, verbose_name=_('Message'))
    ip = models.CharField(max_length=15, null=False, blank=False)
    date = models.DateTimeField(auto_now_add=True,
                    verbose_name=_('Date'))
    objects = ChatManager()

    class Meta:
        ordering = ['-date']
