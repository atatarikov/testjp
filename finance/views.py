from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection

from finance import models
from finance.forms import CounterpartyForm, ContractForm, PaymentStagesForm, PaymentForm, PaymentStagesFilterForm, \
    PaymentFilterForm, ContractFormList, PlanPerForm, ContractFilterForm, FinPlanFilterForm
from finance.models import Counterparty, Contract, PaymentStages, Payment

from django.contrib.auth.decorators import login_required


def move_plan():
    import datetime
    today = datetime.datetime.today()
    today_format = today.strftime("%d/%m/%Y")
    first_day_this_month = datetime.datetime.today().replace(day=1)
    dt = datetime.timedelta(days=1)
    end_day_last_month = (first_day_this_month - dt)
    first_day_last_month = end_day_last_month.replace(day=1)
    first_day_last_month = first_day_last_month.strftime("%Y-%m-%d")
    end_day_last_month = end_day_last_month.strftime("%Y-%m-%d")

    cursor = connection.cursor()
    query = 'SELECT finance_paymentstages.id from finance_paymentstages where (finance_paymentstages.date BETWEEN %s AND %s) AND finance_paymentstages.id not in (select payment_stages_id from finance_payment where payment_stages_id is not null)'
    cursor.execute(query, (first_day_last_month, end_day_last_month))
    qs = dictfetchall(cursor)
    for i in qs:
        obj = PaymentStages.objects.get(pk=i['id'])
        obj.comment += f'** {today_format} добавлен автоматический перенос даты в связи с неоплатой ** '
        obj.date += datetime.timedelta(weeks=4)
        obj.save()


@login_required(redirect_field_name='login')
def index(request):
    move_plan()
    is_plan = False
    today = datetime.today()
    mounth_int = int(today.strftime("%m"))
    data = []
    data_sum = {'sum_1': 0.00,
                'sum_2': 0.00,
                'sum_3': 0.00,
                'sum_4': 0.00,
                'sum_5': 0.00,
                'sum_6': 0.00,
                'sum_7': 0.00,
                'sum_8': 0.00,
                'sum_9': 0.00,
                'sum_10': 0.00,
                'sum_11': 0.00,
                'sum_12': 0.00,
                'sum_13': 0.00,
                'sum_14': 0.00,
                'sum_15': 0.00,
                'sum_1_': 0.00,
                'sum_2_': 0.00,
                'sum_3_': 0.00,
                'sum_4_': 0.00,
                'sum_5_': 0.00,
                'sum_6_': 0.00,
                'sum_7_': 0.00,
                'sum_8_': 0.00,
                'sum_9_': 0.00,
                'sum_10_': 0.00,
                'sum_11_': 0.00,
                'sum_12_': 0.00,
                'sum_13_': 0.00,
                'sum_14_': 0.00,
                'sum_15_': 0.00,
                'sum_contract_sum': 0.00,
                'sum_now': 0.00,
                'sum_next': 0.00,
                'sum_delta': 0.00,
                'sum_saldo': 0.00,
                }
    now = datetime.now()
    year_now = now.strftime("%Y")
    year_next = str(int(year_now) + 1)
    start_data_now = datetime.strptime(f"{year_now}-01-01", "%Y-%m-%d").date()
    end_data_now = datetime.strptime(f"{year_now}-12-31", "%Y-%m-%d").date()
    start_data_next = datetime.strptime(
        f"{year_next}-01-01", "%Y-%m-%d").date()
    end_data_next = datetime.strptime(f"{year_next}-12-31", "%Y-%m-%d").date()
    cursor = connection.cursor()
    query_text = '''SELECT finance_paymentstages.contract_id AS contract_id,
       finance_counterparty.name AS counterparty_name,
       finance_contract.title AS contract_title,
       CASE WHEN finance_contract.be_nds = True THEN finance_contract.sum_with_nds ELSE finance_contract.sum END AS contract_sum,
       finance_contract.number AS contract_number,
       finance_contract.date AS contract_date,
       finance_contract.sum_incorrect AS contract_sum_incorrect
FROM (SELECT DISTINCT finance_paymentstages.contract_id
      FROM finance_paymentstages AS finance_paymentstages WHERE finance_paymentstages.date BETWEEN %s AND %s) AS finance_paymentstages
         LEFT JOIN finance_contract AS finance_contract ON finance_paymentstages.contract_id = finance_contract.id
         LEFT JOIN finance_counterparty AS finance_counterparty
                   ON finance_contract.counterparty_id = finance_counterparty.id WHERE finance_contract.is_plan = %s and finance_contract.is_closed = FALSE'''
    add_title_text = ' [только действующие]'
    if request.method == 'POST':
        if 'is_closed' in request.POST:
            query_text = query_text.replace(
                'finance_contract.is_plan = %s and finance_contract.is_closed = FALSE',
                'finance_contract.is_plan = %s')
            cursor.execute(query_text, (start_data_now, end_data_now, is_plan))
            add_title_text = ' [по всем контрактам]'
    cursor.execute(query_text, (start_data_now, end_data_now, is_plan))

    qs = dictfetchall(cursor)
    for el in qs:
        insert_data = {
            'counterparty': el['counterparty_name'],
            'contract': el['contract_title'],
            'contract_number': el['contract_number'],
            'sum_incorrect': el['contract_sum_incorrect'],
            'contract_data': el['contract_date'].strftime("%Y-%M-%d"),
            'contract_sum': el['contract_sum'],
            'now': get_full_payment(
                el['contract_id']),
            'saldo': el['contract_sum'] - get_full_payment(
                el['contract_id']),
            'next': get_paymentstages_next_year(
                el['contract_id'],
                start_data_next,
                end_data_next)}
        for i in range(1, 16):
            if (i > 12):
                return_data = get_payment_in_month(
                    start_data_next, end_data_next, i - 12, el['contract_id'])
            else:
                return_data = get_payment_in_month(
                    start_data_now, end_data_now, i, el['contract_id'])
            if not return_data == 0:
                insert_data[str(i)] = round(return_data['sum_fact'], 2)
                insert_data[str(i) + '_'] = round(return_data['sum_plan'], 2)
            else:
                insert_data[str(i)] = 0.00
                insert_data[str(i) + '_'] = 0.00
        data.append(insert_data)
    for el in data:
        for i in range(1, 16):
            key_plan = str(i) + '_'
            key_fact = str(i)
            if key_plan in el:
                data_sum['sum_' +
                         key_plan] = round(data_sum['sum_' +
                                                    key_plan] +
                                           float(el[str(i) +
                                                    '_']), 2)
            if key_fact in el:
                data_sum['sum_' +
                         key_fact] = round(data_sum['sum_' +
                                                    key_fact] +
                                           float(el[str(i)]), 2)
            if i == mounth_int:
                data_sum['sum_delta'] = data_sum['sum_' +
                                                 key_fact] - data_sum['sum_' + key_plan]
        if 'contract_sum' in el:
            data_sum['sum_contract_sum'] = round(
                data_sum['sum_contract_sum'] + float(el['contract_sum']), 2)
        if 'now' in el:
            data_sum['sum_now'] = round(
                data_sum['sum_now'] + float(el['now']), 2)
        if 'saldo' in el:
            data_sum['sum_saldo'] = round(
                data_sum['sum_saldo'] + float(el['saldo']), 2)
        if 'next' in el:
            data_sum['sum_next'] = round(
                data_sum['sum_next'] + float(el['next']), 2)

    #
    for i in range(1, 16):
        key_plan = str(i) + '_'
        key_fact = str(i)
        if i < mounth_int:
            data_sum['sum_' + key_plan] = ''
        elif i > mounth_int:
            data_sum['sum_' + key_fact] = data_sum['sum_' + key_plan]
            data_sum['sum_' + key_plan] = ''

    for i in data:
        for i1 in range(1, 16):
            key_plan = str(i1) + '_'
            key_fact = str(i1)
            if i1 < mounth_int:
                i[key_plan] = ''
                if i[key_fact] == 0.0:
                    i[key_fact] = ''
            elif i1 > mounth_int:
                if i[key_plan] == 0.0:
                    i[key_plan] = ''
                i[key_fact] = i[key_plan]
                i[key_plan] = ''
    return render(request,
                  'finance/index.html',
                  {'data': data,
                   'add_title_text': add_title_text,
                   'form_filter': FinPlanFilterForm,
                   'data_sum': data_sum,
                   'mounth_int': mounth_int,
                   'title': 'Финансовый план',
                   'year_now': year_now,
                   'year_next': year_next,
                   })


@login_required(redirect_field_name='login')
def plan(request):
    is_plan = True
    today = datetime.today()
    mounth_int = int(today.strftime("%m"))
    data = []
    data_sum = {'sum_1': 0.00,
                'sum_2': 0.00,
                'sum_3': 0.00,
                'sum_4': 0.00,
                'sum_5': 0.00,
                'sum_6': 0.00,
                'sum_7': 0.00,
                'sum_8': 0.00,
                'sum_9': 0.00,
                'sum_10': 0.00,
                'sum_11': 0.00,
                'sum_12': 0.00,
                'sum_13': 0.00,
                'sum_14': 0.00,
                'sum_15': 0.00,
                'sum_1_': 0.00,
                'sum_2_': 0.00,
                'sum_3_': 0.00,
                'sum_4_': 0.00,
                'sum_5_': 0.00,
                'sum_6_': 0.00,
                'sum_7_': 0.00,
                'sum_8_': 0.00,
                'sum_9_': 0.00,
                'sum_10_': 0.00,
                'sum_11_': 0.00,
                'sum_12_': 0.00,
                'sum_13_': 0.00,
                'sum_14_': 0.00,
                'sum_15_': 0.00,
                'sum_contract_sum': 0.00,
                'sum_now': 0.00,
                'sum_next': 0.00,
                'sum_delta': 0.00,
                'sum_saldo': 0.00,
                }
    now = datetime.now()
    year_now = now.strftime("%Y")
    year_next = str(int(year_now) + 1)
    start_data_now = datetime.strptime(f"{year_now}-01-01", "%Y-%m-%d").date()
    end_data_now = datetime.strptime(f"{year_now}-12-31", "%Y-%m-%d").date()
    start_data_next = datetime.strptime(
        f"{year_next}-01-01", "%Y-%m-%d").date()
    end_data_next = datetime.strptime(f"{year_next}-12-31", "%Y-%m-%d").date()
    cursor = connection.cursor()
    cursor.execute('''SELECT finance_paymentstages.contract_id AS contract_id,
       finance_counterparty.name AS counterparty_name,
       finance_contract.title AS contract_title,
       CASE WHEN finance_contract.be_nds = True THEN finance_contract.sum_with_nds ELSE finance_contract.sum END AS contract_sum,
       finance_contract.number AS contract_number,
       finance_contract.date AS contract_date,
       finance_contract.sum_incorrect AS contract_sum_incorrect
FROM (SELECT DISTINCT finance_paymentstages.contract_id
      FROM finance_paymentstages AS finance_paymentstages WHERE finance_paymentstages.date BETWEEN %s AND %s) AS finance_paymentstages
         LEFT JOIN finance_contract AS finance_contract ON finance_paymentstages.contract_id = finance_contract.id
         LEFT JOIN finance_counterparty AS finance_counterparty
                   ON finance_contract.counterparty_id = finance_counterparty.id WHERE finance_contract.is_plan = %s''', (start_data_now, end_data_next, is_plan))
    qs = dictfetchall(cursor)
    for el in qs:
        insert_data = {
            'counterparty': el['counterparty_name'],
            'contract': el['contract_title'],
            'contract_number': el['contract_number'],
            'sum_incorrect': el['contract_sum_incorrect'],
            'contract_data': el['contract_date'].strftime("%Y-%M-%d"),
            'contract_sum': el['contract_sum'],
            'now': get_full_payment(
                el['contract_id']),
            'saldo': el['contract_sum'] - get_full_payment(
                el['contract_id']),
            'next': get_paymentstages_next_year(
                el['contract_id'],
                start_data_next,
                end_data_next)}
        for i in range(1, 16):
            if (i > 12):
                return_data = get_payment_in_month(
                    start_data_next, end_data_next, i - 12, el['contract_id'])
            else:
                return_data = get_payment_in_month(
                    start_data_now, end_data_now, i, el['contract_id'])
            if not return_data == 0:
                insert_data[str(i)] = round(return_data['sum_fact'], 2)
                insert_data[str(i) + '_'] = round(return_data['sum_plan'], 2)
            else:
                insert_data[str(i)] = 0.00
                insert_data[str(i) + '_'] = 0.00
        data.append(insert_data)
    for el in data:
        for i in range(1, 16):
            key_plan = str(i) + '_'
            key_fact = str(i)
            if key_plan in el:
                data_sum['sum_' +
                         key_plan] = round(data_sum['sum_' +
                                                    key_plan] +
                                           float(el[str(i) +
                                                    '_']), 2)
            if key_fact in el:
                data_sum['sum_' +
                         key_fact] = round(data_sum['sum_' +
                                                    key_fact] +
                                           float(el[str(i)]), 2)
            if i == mounth_int:
                data_sum['sum_delta'] = data_sum['sum_' +
                                                 key_fact] - data_sum['sum_' + key_plan]
        if 'contract_sum' in el:
            data_sum['sum_contract_sum'] = round(
                data_sum['sum_contract_sum'] + float(el['contract_sum']), 2)
        if 'now' in el:
            data_sum['sum_now'] = round(
                data_sum['sum_now'] + float(el['now']), 2)
        if 'saldo' in el:
            data_sum['sum_saldo'] = round(
                data_sum['sum_saldo'] + float(el['saldo']), 2)
        if 'next' in el:
            data_sum['sum_next'] = round(
                data_sum['sum_next'] + float(el['next']), 2)

    #
    for i in range(1, 16):
        key_plan = str(i) + '_'
        key_fact = str(i)
        if i < mounth_int:
            data_sum['sum_' + key_plan] = ''
        elif i > mounth_int:
            data_sum['sum_' + key_fact] = data_sum['sum_' + key_plan]
            data_sum['sum_' + key_plan] = ''

    for i in data:
        for i1 in range(1, 16):
            key_plan = str(i1) + '_'
            key_fact = str(i1)
            if i1 < mounth_int:
                i[key_plan] = ''
                if i[key_fact] == 0.0:
                    i[key_fact] = ''
            elif i1 > mounth_int:
                if i[key_plan] == 0.0:
                    i[key_plan] = ''
                i[key_fact] = i[key_plan]
                i[key_plan] = ''
    return render(request,
                  'finance/index.html',
                  {'data': data,
                   'data_sum': data_sum,
                   'mounth_int': mounth_int,
                   'title': 'Воронка'})


@login_required(redirect_field_name='login')
def plan_per(request):
    dates = []
    dates_f = []
    return_data = []
    sum_data = []
    sum_data_nac = []
    if request.method == 'POST':
        date_start = request.POST['date_start']
        date_start_f = datetime.strptime(f"{date_start}", "%Y-%m-%d").date()
        date_stop = request.POST['date_stop']
        date_stop_f = datetime.strptime(f"{date_stop}", "%Y-%m-%d").date()
        delta = date_stop_f - date_start_f

        if delta.days > 0:
            for i in range(delta.days + 1):
                dates.append(date_start_f + timedelta(i))
                dates_f.append(
                    (date_start_f + timedelta(i)).strftime("%d.%m.%y"))
                sum_data.append(0)
            cursor = connection.cursor()
            cursor.execute('''
            SELECT finance_paymentstages.id AS id,
            finance_paymentstages.title AS paymentstages_title,
            finance_counterparty.name AS counterparty_name,
            finance_contract.title AS contract_title,
            finance_contract.number AS contract_number,
            finance_contract.date AS contract_date
            FROM finance_paymentstages AS finance_paymentstages
            LEFT JOIN finance_contract AS finance_contract ON finance_paymentstages.contract_id = finance_contract.id
            LEFT JOIN finance_counterparty AS finance_counterparty ON finance_contract.counterparty_id = finance_counterparty.id
                               WHERE finance_paymentstages.date BETWEEN %s AND %s AND finance_contract.is_plan = False''',
                           (date_start, date_stop))
            qs = dictfetchall(cursor)
            for el in qs:
                iter_dict = {
                    'paymentstages_title': el['paymentstages_title'],
                    'counterparty_name': el['counterparty_name'],
                    'contract': el['contract_title'] + ' (' + el['contract_number'] + ' от ' + el['contract_date'].strftime("%Y-%M-%d") + ')'}
                iter_sum_list = []
                for _date in dates:
                    sum = 0
                    _qs = PaymentStages.objects.filter(pk=el['id'], date=_date)
                    if _qs:
                        if _qs[0].be_nds:
                            sum = _qs[0].sum_with_nds
                        else:
                            sum = _qs[0].sum
                    iter_sum_list.append(sum)

                    sum_data[len(iter_sum_list) - 1] += sum

                iter_dict['sums'] = iter_sum_list
                return_data.append(iter_dict)
        nar_itog = 0
        for ind, znach in enumerate(sum_data):
            nar_itog += znach
            sum_data_nac.append(nar_itog)

    return render(request,
                  'finance/plan_per.html',
                  {'form': PlanPerForm(),
                   'dates': dates_f,
                   'return_data': return_data,
                   'sum_list': sum_data,
                   'sum_list_nac': sum_data_nac})


def get_payment_in_month(start_data_now, end_data_now, month_, contract_id):
    cursor = connection.cursor()
    #     cursor.execute('''SELECT contract_id, SUM(sum_fact) AS sum_fact, SUM(sum_plan) AS sum_plan FROM
    # (SELECT contract_id, SUM(sum) sum_fact, 0 AS sum_plan FROM finance_payment WHERE CAST(strftime('%m', date) AS integer) = %s AND date between %s AND %s GROUP BY contract_id
    # UNION ALL
    # SELECT contract_id, 0, SUM(sum) FROM finance_paymentstages WHERE CAST(strftime('%m', date) AS integer) = %s AND date between %s AND %s GROUP BY contract_id) GROUP BY contract_id
    # ''', (month_, start_data_now, end_data_now, month_, start_data_now, end_data_now))
    query = f'''SELECT contract_id, SUM(sum_fact) AS sum_fact, SUM(sum_plan) AS sum_plan FROM
    (SELECT contract_id, SUM(CASE WHEN be_nds = True THEN sum_with_nds ELSE sum END) sum_fact, 0 AS sum_plan FROM finance_payment WHERE finance_payment.contract_id={contract_id} AND MONTH(date) = {month_} AND date between '{start_data_now}' AND '{end_data_now}' GROUP BY contract_id
    UNION ALL
    SELECT contract_id, 0, SUM(CASE WHEN be_nds = True THEN sum_with_nds ELSE sum END) FROM finance_paymentstages WHERE finance_paymentstages.contract_id={contract_id} AND MONTH(date) = {month_} AND date between '{start_data_now}' AND '{end_data_now}' GROUP BY contract_id) AS T GROUP BY contract_id
    '''
    cursor.execute(query)
    qs = dictfetchall(cursor)
    return_data = 0
    if len(qs):
        return_data = qs[0]
    return return_data


def get_full_payment(contract_id):
    cursor = connection.cursor()
    query = f'''SELECT SUM(CASE WHEN be_nds = True THEN sum_with_nds ELSE sum END) sum FROM finance_payment WHERE contract_id = {contract_id} GROUP BY contract_id
        '''
    cursor.execute(query)
    qs = dictfetchall(cursor)
    return_data = 0
    if len(qs):
        return_data = round(qs[0]['sum'], 2)
    return return_data


def get_paymentstages_next_year(contract_id, start_data_next, end_data_next):
    cursor = connection.cursor()
    query = f'''SELECT SUM(CASE WHEN be_nds = True THEN sum_with_nds ELSE sum END) sum FROM finance_paymentstages WHERE contract_id = {contract_id} AND date between '{start_data_next}' AND '{end_data_next}' GROUP BY contract_id
        '''
    cursor.execute(query)
    qs = dictfetchall(cursor)
    return_data = 0
    if len(qs):
        return_data = round(qs[0]['sum'], 2)
    return return_data


def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


@login_required(redirect_field_name='login')
def default_list(request, object):
    objects_list = return_object_list(object, request)
    titles_list = get_full_data_about_object(object)['titles_list']
    fields_list = get_full_data_about_object(object)['fields_list']
    form_filter = get_full_data_about_object(object)['form_filter']
    return render(
        request,
        'finance/default_list.html',
        {
            'title': get_full_data_about_object(object)['title_list'],
            'objects_list': objects_list,
            'table': create_table(
                get_full_data_about_object(object)['model'],
                object,
                objects_list,
                titles_list,
                fields_list),
            'object': object,
            'button_list': create_button_list(
                object,
                request),
            'form_filter': form_filter})


def return_object_list(object, request):
    objects_list = ''
    if request.method == 'POST':
        if object == 'PaymentStages':
            request_data = request.POST
            if request_data['contract']:
                objects_list = PaymentStages.objects.filter(
                    contract_id__exact=request_data['contract'])
                return objects_list
        elif object == 'Contract':
            request_data = request.POST
            if request_data['counterparty']:
                objects_list = Contract.objects.filter(
                    counterparty_id__exact=request_data['counterparty'])
                return objects_list
        elif object == 'Payment':
            request_data = request.POST
            if request_data['contract']:
                objects_list = Payment.objects.filter(
                    contract_id__exact=request_data['contract'])
                return objects_list
    objects_list = get_full_data_about_object(object)['model'].objects.all()
    return objects_list


@login_required(redirect_field_name='login')
def default_add(request, object):
    is_new = True
    error = ''
    if request.method == 'POST':
        if 'cancel' in request.POST:
            return redirect('../default_list/' + str(object))
        else:
            form = get_full_data_about_object(object)['form'](request.POST)
            if form.is_valid():
                obj_ = form.save()
                if 'save_exit' in request.POST:
                    return redirect('../default_list/' + str(object))
                else:
                    return redirect('../default_edit/' +
                                    str(object) + '/' + str(obj_.id))
            else:
                error = 'Форма была заполнена неверно!'
    form = get_full_data_about_object(object)['form']()
    return render(request,
                  'finance/default_add_edit.html',
                  {'title': get_full_data_about_object(object)['title_add'],
                   'object': object,
                   'form': form,
                   'error': error,
                   'buttons_add_edit': create_button_add_edit(is_new,
                                                              request,
                                                              object,
                                                              1,
                                                              None)})


@login_required(redirect_field_name='login')
def default_edit(request, object, id):
    object_from_model = get_object_or_404(
        get_full_data_about_object(object)['model'], id=id)
    error = ''
    is_new = False
    if request.method == 'POST':
        redirect_string = '../../' + get_url_redirect(object, id)
        if 'delete' in request.POST:
            error = ''
            object_del = get_full_data_about_object(
                object)['model'].objects.filter(id__exact=id)
            parent_model = get_full_data_about_object(object)['parent']
            if parent_model:
                field_object_ = get_full_data_about_object(object)['model']._meta.get_field(
                    parent_model[0].lower() + parent_model[1:])
                parent_id = field_object_.value_from_object(object_del[0])
            try:
                object_del.delete()
            except Exception as e:
                error = 'Нельзя удалить, поскольку есть связанные объекты!'
            if parent_model:
                get_full_data_about_object(
                    object)['parent_model'].objects.get(id=parent_id).save()
            if len(error) == 0:
                return redirect(redirect_string)
        elif ('save' in request.POST) or ('save_exit' in request.POST):
            form = get_full_data_about_object(object)['form'](
                request.POST, instance=object_from_model)
            if form.is_valid():
                object_from_model = form.save(commit=False)
                object_from_model.save()
                if 'save_exit' in request.POST:
                    return redirect(redirect_string)
            else:
                error = 'Форма была заполнена неверно!'
    form = get_full_data_about_object(
        object)['form'](instance=object_from_model)
    return render(
        request,
        'finance/default_add_edit.html',
        {
            'title': get_full_data_about_object(object)['title'] + str(
                get_title_edit(
                    object_from_model,
                    object)) + '"',
            'object': object,
            'form': form,
            'error': error,
            'buttons_add_edit': create_button_add_edit(
                is_new,
                request,
                object,
                2,
                id,
                True)})


def get_full_data_about_object(object):
    data_list = {}
    if object == 'Counterparty':
        data_list = {'model': Counterparty,
                     'form': CounterpartyForm,
                     'form_filter': '',
                     'title': 'КОНТРАГЕНТ "',
                     'title_add': 'НОВЫЙ КОНТРАГЕНТ',
                     'title_list': 'СПИСОК КОНТРАГЕНТОВ',
                     'titles_list': ['Наименование', 'ИНН', 'КПП'],
                     'fields_list': ['name', 'tin', 'iec'],
                     'key_fields_list': ['_no_', '_no_', '_no_'],
                     'link_list': 'default_add',
                     'link_list_edit': 'default_edit',
                     'parent_model': '',
                     'parent': '', }
    elif object == 'Contract':
        data_list = {
            'model': Contract,
            'form': ContractForm,
            'form_filter': ContractFilterForm,
            'title': 'ДОГОВОР "',
            'title_add': 'НОВЫЙ ДОГОВОР',
            'title_list': 'СПИСОК ДОГОВОРОВ',
            'titles_list': [
                'Наименование',
                'Контрагент',
                'Номер',
                'Плановый контракт',
                'От',
                'Закрыт',
                'Сумма'],
            'fields_list': [
                'title',
                'counterparty',
                'number',
                'is_plan',
                'date',
                'is_closed',
                'sum'],
            'key_fields_list': [
                '_no_',
                'name',
                '_no_',
                '_b_',
                '_no_',
                '_b_',
                '_fd_'],
            'link_list': 'default_add',
            'link_list_edit': 'default_edit',
            'parent': '',
        }
    elif object == 'PaymentStages' or object == 'Payment_stages':
        data_list = {
            'model': PaymentStages,
            'form': PaymentStagesForm,
            'form_filter': PaymentStagesFilterForm,
            'title': 'ЭТАП ОПЛАТЫ ПО ДОГОВОРУ "',
            'title_add': 'НОВЫЙ ЭТАП ОПЛАТЫ ПО ДОГОВОРУ',
            'title_list': 'СПИСОК ЭТАПОВ ОПЛАТЫ ПО ДОГОВОРАМ',
            'titles_list': [
                'Название',
                'Договор',
                'Дата',
                'Сумма',
                'Сумма с НДС',
                'Оплачен',
                'Комментарий'],
            'fields_list': [
                'title',
                'contract',
                'date',
                'sum',
                'sum_with_nds',
                'paymented',
                'comment'],
            'key_fields_list': [
                '_no_',
                'title',
                '_no_',
                '_fd_',
                '_r_',
                '_b_',
                '_no_',
            ],
            'link_list': 'default_add',
            'link_list_edit': 'default_edit',
            'parent': '',
        }
    elif object == 'Payment':
        data_list = {
            'model': Payment,
            'form': PaymentForm,
            'form_filter': PaymentFilterForm,
            'title': 'ОПЛАТА "',
            'title_add': 'НОВАЯ ОПЛАТА',
            'title_list': 'СПИСОК ОПЛАТ',
            'titles_list': [
                'Дата',
                'Номер пл.поруч.',
                'Контрагент',
                'Договор',
                'Этап оплаты',
                'Сумма'],
            'fields_list': [
                'date',
                'number',
                'counterparty',
                'contract',
                'payment_stages',
                'sum'],
            'key_fields_list': [
                '_no_',
                '_no_',
                'name',
                'title',
                'title',
                '_fd_'],
            'link_list': 'default_add',
            'link_list_edit': 'default_edit',
            'parent': '',
        }
    return data_list


def create_table(model, object_name, objects_list, titles_list, fields_list):
    link_list = get_full_data_about_object(object_name)['link_list_edit']
    code_line = '''<table class="table table-striped">
    <thead>
    <tr>
      <th scope="col">#</th>'''
    for title_from_list in titles_list:
        code_line += '<th scope="col">' + title_from_list + '</th>'
    code_line += '''
     </tr>
  </thead>
  <tbody>'''
    i = 0
    for object in objects_list:
        i += 1
        link_line = '<a href="../' + link_list + '/' + \
            str(object_name) + '/' + str(object.id) + '">'
        code_line += '''<tr>
  <th scope="row">''' + link_line + str(i) + '</a></th>'
        ii = 0
        for field_from_list in fields_list:
            try:
                field_object = model._meta.get_field(field_from_list)
                field_value = field_object.value_from_object(object)
            except BaseException:
                field_object = None
                field_value = None
            key_field_value = get_full_data_about_object(
                object_name)['key_fields_list'][ii]
            ii += 1
            if key_field_value == '_no_':
                if field_from_list == 'date' or field_from_list == 'sum':
                    code_line += '<td class="text-nowrap">' + \
                        link_line + str(field_value) + '</a></td>'
                else:
                    code_line += '<td>' + link_line + \
                        str(field_value) + '</a></td>'
                # code_line += '<td>' + link_line + str(field_value) + '</a></td>'
            elif key_field_value == '_fd_':
                code_line += '<td class="text-nowrap">' + link_line + \
                    return_correct_string(str(field_value)) + '</a></td>'
            elif key_field_value == '_b_':
                if field_value:
                    field_value = '&#10003;'
                else:
                    field_value = ''
                code_line += '<td>' + link_line + \
                    str(field_value) + '</a></td>'
            elif key_field_value == '_r_':
                code_line += '<td class="text-nowrap">' + link_line + \
                    return_result(object_name, field_from_list, object.id) + '</a></td>'
            else:
                support_model = get_full_data_about_object(
                    field_from_list[0:1].upper() + field_from_list[1:])['model']
                support_qs = support_model.objects.filter(
                    id__exact=field_value)
                if support_qs.count():
                    support_object = support_qs[0]
                    field_object_ = support_model._meta.get_field(
                        key_field_value)
                    field_value_ = field_object_.value_from_object(
                        support_object)
                    code_line += '<td>' + link_line + \
                        str(field_value_) + '</a></td>'
                else:
                    code_line += '<td>' + link_line + '</a></td>'
        code_line += '</tr>'
    code_line += '</tbody></table>'
    return code_line


def create_button_list(object, request):
    link_list = get_full_data_about_object(object)['link_list']
    code_line = '<a href="../' + link_list + '/' + object + \
        '" class="btn btn-success my-2 float-right" role="button">Добавить (+)</a>'
    return code_line


def create_button_add_edit(
        is_new,
        request,
        object,
        i,
        id,
        delete=False,
        add_string=False):
    code_line = '<a href = "'
    for i in range(i):
        code_line += '../'
    code_line += get_url_redirect(object, id) + \
        '" class ="btn btn-info my-2" role="button">Отменить</a>'
    if add_string:
        code_line += '''
        <button name = \'add_string\' type = "submit" class ="btn btn-secondary">Добавить строку</button>'''
    code_line += '''
    <button name = \'save\' type = "submit" class ="btn btn-success">Сохранить</button>'''
    code_line += '''
        <button name = \'save_exit\' type = "submit" class ="btn btn-success">Сохранить и выйти</button>'''
    if delete:
        code_line += '''
        <button name = \'delete\' type = "submit" class ="btn btn-danger">Удалить</button>'''
    code_line += '''
    <button name = \'print\' class ="btn btn-warning" onClick="window.print()">Печать в PDF</button>'''
    return code_line


def get_title_edit(object, object_name):
    title_string = ''
    if object_name == 'Contract' or object_name == 'PaymentStages':
        return object.title
    elif object_name == 'Counterparty':
        return object.name
    elif object_name == 'Payment':
        return_data = " №" + str(object.number) + " от " + str(object.date)
        if object.payment_stages:
            return return_data + "[" + str(object.payment_stages.title) + "]"


def get_url_redirect(object, id):
    if object == 'PointString':
        # object_point = PointString.objects.get(id=id)
        # return 'point_edit/Point/' + str(object_point.point.id)
        pass
    else:
        return 'default_list/' + str(object)


def return_correct_string(string_integer):
    sum_1 = string_integer[-3:]
    reversed_string = string_integer[-4::-1]
    sum_2 = ' '.join([reversed_string[i:i + 3]
                     for i in range(0, len(reversed_string), 3)])
    reversed_string_2 = sum_2[::-1]
    return str(reversed_string_2) + str(sum_1)


def return_result(object_name, field_from_list, object_id):
    return_data = 0
    if object_name == 'PaymentStages':
        if field_from_list == 'sum_with_nds':
            obj = PaymentStages.objects.get(pk=object_id)
            if obj.be_nds:
                return_data = obj.sum_with_nds
            else:
                return_data = obj.sum
    return return_correct_string(str(round(return_data, 2)))
