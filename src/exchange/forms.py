from django import forms
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from .models import ExchangeTransaction, Chat, Pair


class PublicTransactionForm(forms.ModelForm):
    payout_raw_address = forms.CharField(max_length=35,
                                        label=_('Payout address'))
    out_address = forms.HiddenInput()

    class Meta:
        model = ExchangeTransaction
        fields = ['pair',]

    def __init__(self, **kwargs):
        super(PublicTransactionForm, self).__init__(**kwargs)
        self.fields['pair'].queryset = Pair.objects.filter(enabled=True)

    def clean_pair(self):
        cleaned_data = super(PublicTransactionForm, self).clean()
        pair = cleaned_data.get("pair")
        if pair.enabled == False:
            raise forms.ValidationError("Pair is disabled")
        return pair

    def clean_payout_raw_address(self):
        cleaned_data = super(PublicTransactionForm, self).clean()
        pair = cleaned_data.get("pair")
        out_address = cleaned_data.get("payout_raw_address")
        if pair.coin_to.is_address_valid(out_address)==False:
            raise forms.ValidationError(
                "Payout address {} is not valid for {}".format(
                                                    out_address,
                                                    pair.coin_to.name)
            )
        return out_address


class ChatForm(forms.ModelForm):
    msg =  forms.CharField(label='',
            widget=forms.TextInput(\
                attrs={'placeholder': _('Enter a message')}))
    redirect_uri = forms.HiddenInput()
    ip = forms.HiddenInput()

    class Meta:
        model = Chat
        fields = ['msg',]

    def __init__(self, *args, **kwargs):
        try:
            self.request = kwargs.pop('request')
        except:
            pass
        super(ChatForm, self).__init__(*args, **kwargs)

    def clean_msg(self, *args, **kwargs):
        ip = self.request.META['REMOTE_ADDR']
        cleaned_data = super(ChatForm, self).clean()
        if Chat.objects.is_flood(ip):
            messages.add_message(self.request, messages.INFO, _("Seems like a flood, wait for a while"))
            raise forms.ValidationError(
                "Seems like a flood, wait for a while")
        msg = cleaned_data.get("msg")
        return msg
