import decimal

from django.db import models
from django.db.models import Sum


class Counterparty(models.Model):
    name = models.CharField(max_length=150,
                            verbose_name='Наименование контрагента')
    tin = models.CharField(max_length=12, verbose_name='ИНН', blank=True)
    iec = models.CharField(max_length=9, verbose_name='КПП', blank=True)
    comment = models.TextField(verbose_name='Комментарий', blank=True)

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'

    def __str__(self):
        return self.name


class Contract(models.Model):
    title = models.CharField(max_length=150, verbose_name='Название договора')
    counterparty = models.ForeignKey(
        'Counterparty',
        on_delete=models.PROTECT,
        null=True,
        verbose_name='Контрагент')
    number = models.CharField(max_length=50, verbose_name='№', blank=True)
    date = models.DateField(
        verbose_name='Дата договора',
        blank=True,
        null=True)
    sum = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        verbose_name='Сумма договора (без НДС)')
    comment = models.TextField(verbose_name='Комментарий', blank=True)
    sum_incorrect = models.BooleanField(
        verbose_name='Сумма договора не соответствует сумме по этапам',
        blank=True,
        null=True,
        default=False)
    is_plan = models.BooleanField(
        verbose_name='Это плановый договор',
        blank=True,
        null=True,
        default=False)
    is_closed = models.BooleanField(
        verbose_name='Это закрытый договор',
        blank=True,
        null=True,
        default=False)
    is_border_contract = models.BooleanField(
        verbose_name='Это рамочный договор',
        blank=True,
        null=True,
        default=False)
    sum_with_nds = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Сумма договора (c НДС)')
    be_nds = models.BooleanField(verbose_name='+НДС', blank=True,
                                 null=True,
                                 default=False)
    is_active = models.BooleanField(verbose_name='Актуален', default=True)

    class Meta:
        verbose_name = 'Договор'
        verbose_name_plural = 'Договоры'
        ordering = ('counterparty__name', 'title')

    def __str__(self):
        return f'[{self.counterparty.name}] {self.title}'

    def save(self, *args, **kwargs):
        if not self.sum_with_nds and self.be_nds:
            self.sum_with_nds = round(self.sum * decimal.Decimal('1.20'), 2)
        super().save(*args, **kwargs)


class PaymentStages(models.Model):
    title = models.CharField(max_length=150,
                             verbose_name='Название этапа оплаты по договору')
    contract = models.ForeignKey(
        'Contract',
        on_delete=models.PROTECT,
        null=True,
        verbose_name='Договор')
    date = models.DateField(verbose_name='Дата оплаты этапа')
    sum = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        verbose_name='Сумма оплаты этапа (без НДС)')
    sum_with_nds = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Сумма договора (c НДС)')
    be_nds = models.BooleanField(verbose_name='+НДС', blank=True,
                                 null=True,
                                 default=False)
    paymented = models.BooleanField(verbose_name='Оплачено', blank=True,
                                    null=True,
                                    default=False)

    comment = models.TextField(verbose_name='Комментарий', blank=True)
    is_active = models.BooleanField(verbose_name='Актуален', default=True)

    class Meta:
        verbose_name = 'Этап оплаты по договору'
        verbose_name_plural = 'Этапы оплаты по договорам'
        ordering = ('title',)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.sum_with_nds and self.be_nds:
            self.sum_with_nds = round(self.sum * decimal.Decimal('1.20'), 2)
        qs = PaymentStages.objects.filter(
            contract_id__exact=self.contract.id).exclude(
            id__exact=self.id).aggregate(
            Sum('sum'),
            Sum('sum_with_nds'))
        sum_ = self.sum
        sum_with_nds_ = self.sum_with_nds
        if qs['sum__sum'] is not None:
            sum_ += qs['sum__sum']
        if qs['sum_with_nds__sum'] is not None and sum_with_nds_ is not None:
            sum_with_nds_ += qs['sum_with_nds__sum']
        super().save(*args, **kwargs)
        if self.contract.sum != sum_ or self.contract.sum_with_nds != sum_with_nds_:
            self.contract.sum_incorrect = True
        else:
            self.contract.sum_incorrect = False
        if self.contract.is_border_contract:
            self.contract.sum = sum_
            self.contract.sum_with_nds = sum_with_nds_
        self.contract.save()


class Payment(models.Model):
    counterparty = models.ForeignKey(
        'Counterparty',
        on_delete=models.PROTECT,
        null=True,
        verbose_name='Контрагент')
    contract = models.ForeignKey(
        'Contract',
        on_delete=models.PROTECT,
        null=True,
        verbose_name='Договор')
    payment_stages = models.ForeignKey(
        'PaymentStages',
        on_delete=models.PROTECT,
        null=True,
        verbose_name='Этап оплаты по договору')
    number = models.CharField(
        max_length=50,
        verbose_name='№ платежного поручения',
        blank=True)
    date = models.DateField(verbose_name='Дата оплаты', null=True)
    sum = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        verbose_name='Сумма оплаты',
        default=0.0)
    comment = models.TextField(verbose_name='Комментарий', blank=True)
    sum_with_nds = models.DecimalField(
        max_digits=25,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Сумма договора (c НДС)')
    be_nds = models.BooleanField(verbose_name='+НДС', blank=True,
                                 null=True,
                                 default=False)
    is_active = models.BooleanField(verbose_name='Актуален', default=True)

    class Meta:
        verbose_name = 'Оплата по договору'
        verbose_name_plural = 'Оплаты по договорам'
        ordering = ('-date',)

    def __str__(self):
        return_data = "ПП №" + str(self.number) + " от " + str(self.date)
        if self.payment_stages:
            return_data += "[" + str(self.payment_stages.title) + "]"
        return return_data

    def save(self, *args, **kwargs):
        if self.payment_stages:
            ob = self.payment_stages
            ob.date = self.date
            ob.save()
        if not self.sum_with_nds and self.be_nds:
            self.sum_with_nds = round(self.sum * decimal.Decimal('1.20'), 2)

        if self.payment_stages:
            qs = Payment.objects.filter(
                payment_stages__id=self.payment_stages.id).exclude(
                id__exact=self.id).aggregate(
                Sum('sum'),
                Sum('sum_with_nds'))
            sum_ = 0
            sum_with_nds_ = 0
            if self.sum:
                sum_ = self.sum
            if self.sum_with_nds:
                sum_with_nds_ = self.sum_with_nds
            if qs['sum__sum'] is not None:
                sum_ += qs['sum__sum']
            if qs['sum_with_nds__sum'] is not None and sum_with_nds_ is not None:
                sum_with_nds_ += qs['sum_with_nds__sum']

            payment_stages_sum = 0
            payment_stages_sum_with_nds = 0
            if self.payment_stages.sum:
                payment_stages_sum = self.payment_stages.sum
            if self.payment_stages.sum_with_nds:
                payment_stages_sum_with_nds = self.payment_stages.sum_with_nds

            obj = self.payment_stages
            print(payment_stages_sum, sum_)
            if payment_stages_sum > sum_ or payment_stages_sum_with_nds > sum_with_nds_:
                obj.paymented = False
            else:
                obj.paymented = True
            obj.save()
        super().save(*args, **kwargs)
