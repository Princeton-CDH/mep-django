from django.contrib import admin

from mep.accounts.models import Account


class AccountAdmin(admin.ModelAdmin):
    model = Account
    list_display = ('id', 'list_persons', 'list_addresses')

admin.site.register(Account, AccountAdmin)
