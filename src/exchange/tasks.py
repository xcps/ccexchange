# Create your tasks here
from __future__ import absolute_import, unicode_literals
import logging
from celery import shared_task
import urllib
from datetime import datetime, timedelta
import pytz

from .models import ExchangeTransaction, Coin, ExternalRate

from .nv_rates import get_gstbtc_rate
from .novaex_rates import get_ancbtc_rate

def update_nv_rates():
    data = get_gstbtc_rate()
    sales = reversed(data["Sell"])
    sell_rate = None
    for sell in sales:
        if sell["amount"] > 99:
            sell_rate = sell["cost"]
            break
    ex = ExternalRate.objects.get_or_create(
        pair__coin_from__symbol='GST',
        pair__coin_to__symbol='BTC'
        )[0]
    ex.rate = sell_rate
    ex.save()

    buys = data["Buy"]
    buy_rate = None
    for buy in buys:
        if buy["amount"] > 99:
            buy_rate = buy["cost"]
            break
    ex = ExternalRate.objects.get_or_create(
        pair__coin_from__symbol='BTC',
        pair__coin_to__symbol='GST'
        )[0]
    ex.rate = buy_rate
    return [sell_rate, buy_rate,]

def update_gvk_rates(nv_rates):
    data = get_ancbtc_rate()
    sales = data["sellorders"]
    sell_rate = None
    for sell in sales:
        if sell["amount"] > 99:
            sell_rate = sell["price"]
            break

    ex = ExternalRate.objects.get_or_create(
        pair__coin_from__symbol='GST',
        pair__coin_to__symbol='ANC'
        )[0]
    ex.rate = sell_rate / nv_rates[0]
    ex.save()

    buys = data['buyorders']
    buy_rate = None
    for buy in buys:
        if buy["amount"] > 99:
            buy_rate = buy["price"]
            break
    ex = ExternalRate.objects.get_or_create(
        pair__coin_from__symbol='ANC',
        pair__coin_to__symbol='GST'
        )[0]
    ex.rate = buy_rate / nv_rates[1]
    return [sell_rate, buy_rate,]

@shared_task
def update_rates():
    nv_rates = update_nv_rates()
    gvk_rates = update_gvk_rates(nv_rates)
    return True

@shared_task
def update_coins_info():
    for coin in Coin.objects.all():
        coin.update_info()




@shared_task
def serve_incomplete_transactions2():
    T_CACHE = {}
    one_week_ago = datetime.now(pytz.utc) - timedelta(days=7)
    transacts = ExchangeTransaction.objects\
                    .get_waiting_transactions()\
                    .prefetch_related('in_address')\
                    .prefetch_related('out_address')\
                    .prefetch_related('pair')\
                    .filter(created_at__gte=one_week_ago)
    result = []
    for transact in transacts:
        try:
            coin_from = transact.pair.coin_from
            if T_CACHE.get(coin_from.symbol) is None:
                T_CACHE[coin_from.symbol] = coin_from.get_received_transactions()
            t = T_CACHE[coin_from.symbol].get(transact.in_address.address)
            if t:
                if transact.coins_received != t["amount"] or \
                        transact.confirmations != t["confirmations"]:
                    transact.coins_received = t["amount"]
                    transact.confirmations = t["confirmations"]
                    transact.status = ExchangeTransaction\
                                        .PAYMENT_RECEIVED
                    transact.is_failed = False
                    transact.save()
                if t["confirmations"] >= 6:
                    result.append('{} confirmations'.format(t["confirmations"]))
                    transact.process_transaction()
        except Exception as ex:
            transact.is_failed = True
            transact.error_message = ex.__str__()
            transact.save()
            continue
    return '\n'.join(result)


@shared_task
def serve_incomplete_transactions():
    transacts = ExchangeTransaction.objects\
                    .get_waiting_transactions()\
                    .prefetch_related('in_address')\
                    .prefetch_related('out_address')
    result = []
    for transact in transacts:
        try:
            if transact.status == ExchangeTransaction\
                    .WAITING_FOR_PAYMENT:
                money = transact.pair.coin_from.check_received(
                                transact.in_address.address)
                if money > 0:
                    # transaction info update
                    transact.status = ExchangeTransaction\
                                        .PAYMENT_RECEIVED
                    transact.coins_received = money
                    transact.save()
                else:
                    result.append('{} not received'.format(
                                transact.in_address.address))
                    continue
            money = transact.coins_received

            # decide how much to send
            rate = transact.pair.get_rate()
            amount_to_send = money * rate

            # check if we have such much
            balance = transact.pair.coin_to.get_balance()
            if balance < amount_to_send:
                res = '{} has not enough balance ({} vs {})'\
                        .format(transact.coin_to.name, balance,
                                                amount_to_send)
                result.append(res)
                transact.status = ExchangeTransaction\
                                        .NO_BALANCE
                transact.save()
                continue

            try:
                # send coins and update transaction info
                transact.pair.coin_to.send_coins(
                                transact.out_address.address,
                                amount_to_send)
                transact.status = ExchangeTransaction\
                                    .TRANSACTION_COMPLETE
                transact.coins_sent = amount_to_send
                transact.rate = rate
                transact.is_failed = False
                transact.save()
            except urllib.error.HTTPError as e:
                transact.status = ExchangeTransaction\
                                    .WAITING_FOR_WALLET
                transact.is_failed = True
                res = 'Waiting for wallet {}'.format(
                                transact.pair.coin_to.name)
                result.append(res)
                if hasattr(e, "read"):
                    transact.error_message = e.read()
                transact.save()
                continue

            res = 'Transact complete {}-{}: {}-{} ({})'.format(
                                transact.pair.coin_from.symbol,
                                transact.pair.coin_to.symbol,
                                transact.coins_received,
                                transact.coins_sent,
                                transact.rate,
            )
            result.append(res)
            transact.pair.coin_to.update_info()
            transact.pair.coin_from.update_info()
        except Exception as ex:
            transact.is_failed = True
            transact.error_message = ex.__str__()
            transact.save()
            continue
    return '\n'.join(result)
