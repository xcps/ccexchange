import re

from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.conf import settings
from django.views import View
from django.urls import reverse
from django.db import connection
from django.views.generic.edit import CreateView
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView

from .models import Coin, CoinAddressIn, CoinAddressOut, \
                            ExchangeTransaction as ET, Pair, Chat
from .forms import PublicTransactionForm, ChatForm
from .utils import my_round
# Create your views here.

class BaseContextMixin(object):

    needs_cryptoinfo = True

    """ Base context mixin for base.html """

    def get_site_settings(self):
        return {
            'title': _('Cryptocoin exchanger'),
            'header': _('cryptocurrency exchanger'),
        }

    def get_context_data(self, **kwargs):
        """ Base context for base.html """
        context = super(BaseContextMixin, self)\
                        .get_context_data(**kwargs)
        context['site_settings'] = self.get_site_settings()
        if self.needs_cryptoinfo:
            context['coins'] = Coin.objects.all()
        return context


class IndexView(BaseContextMixin, CreateView):

    template_name = 'index.html'
    form_class = PublicTransactionForm
    needs_cryptoinfo = False

    def form_valid(self, form):
        pair = form.cleaned_data['pair']
        address = form.cleaned_data['payout_raw_address']
        coin_address = CoinAddressOut.objects.get_or_create(
                        address=address, coin=pair.coin_to)[0]
        form.instance.out_address = coin_address
        form.instance.in_address = CoinAddressIn.objects.\
                                create_payment_address(pair.coin_from)
        form.instance.ip = self.request.META['REMOTE_ADDR']
        return super(IndexView, self).form_valid(form)


    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        if self.request.POST:
            context['form'] = PublicTransactionForm(self.request.POST)
        else:
            context['form'] = PublicTransactionForm()
            context['pairs'] = Pair.objects.filter(enabled=True)
        context['chats'] = Chat.objects.filter(transaction=None)[:50]
        context['chatform'] = ChatForm()
        context['recents'] = ET.objects.get_recents()
        return context


class TransactionView(BaseContextMixin, DetailView):

    model = ET
    needs_cryptoinfo = False

    def get_context_data(self, **kwargs):
        context = super(TransactionView, self).\
                                get_context_data(**kwargs)
        status = self.object.status
        if status == ET.WAITING_FOR_PAYMENT:
            info_template = 'exchange/transact_templates/'\
                        'waiting_for_payment.html'
        elif status == ET.TRANSACTION_COMPLETE:
            info_template = 'exchange/transact_templates/'\
                        'transaction_complete.html'
        else:
            info_template = 'exchange/transact_templates/'\
                        'payment_received.html'
            context['received'] = self.object.coins_received.__str__().rstrip('0').rstrip('.') if '.' in self.object.coins_received.__str__() else self.object.coins_received.__str__()
        context['info_template'] = info_template
        context['chatform'] = ChatForm()
        context['chats'] = Chat.objects\
                                .filter(transaction=self.object)
        return context


class ChatView(CreateView):
    form_class = ChatForm

    def get_form_kwargs(self):
        kw = super(ChatView, self).get_form_kwargs()
        kw['request'] = self.request # the trick!
        return kw

    def form_invalid(self, form):
        uri = form.data['redirect_uri']
        return redirect(uri)

    def form_valid(self, form):
        uri = form.data['redirect_uri']
        self.success_url = uri
        transact = re.search('\/(.{32})\/$', uri)
        if transact:
            try:
                t = ET.objects.get(slug=transact.group(1))
                form.instance.transaction = t
            except:
                pass
        form.instance.ip = self.request.META['REMOTE_ADDR']
        return super(ChatView, self).form_valid(form)
