from django.contrib import admin

# Register your models here.
from django.contrib import admin

# Register your models here.
from finance.models import *

admin.site.register(Counterparty)
admin.site.register(Contract)
admin.site.register(PaymentStages)
admin.site.register(Payment)