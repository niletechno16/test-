from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
from datetime import date
import calendar

ARABIC_MONTHS = {
    1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',
    7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'
}

def _month_year_context(date_from, today):
    try:
        parts = date_from.split('-')
        sel_year  = int(parts[0])
        sel_month = int(parts[1])
    except Exception:
        sel_year  = today.year
        sel_month = today.month
    month_label     = f"{ARABIC_MONTHS[sel_month]} {sel_year}"
    available_years = list(range(today.year - 3, today.year + 1))
    return sel_month, sel_year, month_label, available_years

@login_required
def customers_list(request):
    today = date.today()
    default_from = today.replace(day=1).strftime('%Y-%m-%d')
    last_day     = calendar.monthrange(today.year, today.month)[1]
    default_to   = today.replace(day=last_day).strftime('%Y-%m-%d')
    date_from = request.GET.get('from', default_from)
    date_to   = request.GET.get('to',   default_to)
    search    = request.GET.get('search', '')
    sel_month, sel_year, month_label, available_years = _month_year_context(date_from, today)

    if get_role(request.user) != 'visitor' and not is_manager_level(request.user):
        return redirect('home')

    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        customers = vdata['customers']
        if search:
            customers = [c for c in customers if search in c['customer_name'] or search in c['customer_phone']]
        return render(request, 'customers/index.html', {
            'customers': customers, 'search': search, 'is_manager': True,
            'date_from': date_from, 'date_to': date_to,
            'month_label': month_label,
            'selected_month': sel_month, 'selected_year': sel_year,
            'available_years': available_years,
        })

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    search_clause = ""
    if search:
        search_clause = f" AND (c.customer_name LIKE N'%{search}%' OR c.customer_phone LIKE N'%{search}%')"

    query = f"""
        SELECT c.*,
               COUNT(r.id) AS total_reports,
               SUM(CASE WHEN r.classification LIKE N'تم%' THEN 1 ELSE 0 END) AS resolved,
               SUM(CASE WHEN r.classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
        FROM customer_detail_by_A c
        LEFT JOIN Customer_service_reports_by_A r
               ON c.customer_id = r.customer_id AND r.resolved_date >= {date_from.replace('-','') if date_from else '0'}
               AND r.resolved_date <= {date_to.replace('-','') if date_to else '99999999'}
        WHERE 1=1{search_clause}
        GROUP BY c.customer_id, c.customer_name, c.customer_phone
        ORDER BY total_reports DESC
    """
    cursor.execute(query)
    customers = cursor.fetchall()
    conn.close()

    return render(request, 'customers/index.html', {
        'customers': customers, 'search': search, 'is_manager': True,
        'date_from': date_from, 'date_to': date_to,
        'month_label': month_label,
        'selected_month': sel_month, 'selected_year': sel_year,
        'available_years': available_years,
    })


@login_required
def customer_detail(request, customer_id):
    if get_role(request.user) != 'visitor' and not is_manager_level(request.user):
        return redirect('home')

    today = date.today()
    default_from = today.replace(day=1).strftime('%Y-%m-%d')
    last_day     = calendar.monthrange(today.year, today.month)[1]
    default_to   = today.replace(day=last_day).strftime('%Y-%m-%d')
    date_from = request.GET.get('from', default_from)
    date_to   = request.GET.get('to',   default_to)
    sel_month, sel_year, month_label, available_years = _month_year_context(date_from, today)

    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        customer = next((c for c in vdata['customers'] if c['customer_id'] == customer_id), None)
        reports = [r for r in vdata['reports'] if r['customer_name'] == customer['customer_name']]
        if date_from:
            reports = [r for r in reports if r['resolved_date'] >= int(date_from.replace('-',''))]
        if date_to:
            reports = [r for r in reports if r['resolved_date'] <= int(date_to.replace('-',''))]
        reports = sorted(reports, key=lambda r: (r['resolved_date'], r.get('resolved_time', '')), reverse=True)
        return render(request, 'customers/detail.html', {
            'customer': customer, 'reports': reports, 'is_manager': True,
            'date_from': date_from, 'date_to': date_to,
            'month_label': month_label,
            'selected_month': sel_month, 'selected_year': sel_year,
            'available_years': available_years,
        })

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    cursor.execute(f"SELECT * FROM customer_detail_by_A WHERE customer_id = {customer_id}")
    customer = cursor.fetchone()

    where = f"WHERE customer_id = {customer_id}"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-','')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-','')}"
    cursor.execute(f"SELECT * FROM Customer_service_reports_by_A {where} ORDER BY resolved_date DESC, resolved_time DESC")
    reports = cursor.fetchall()
    conn.close()

    return render(request, 'customers/detail.html', {
        'customer': customer, 'reports': reports, 'is_manager': True,
        'date_from': date_from, 'date_to': date_to,
        'month_label': month_label,
        'selected_month': sel_month, 'selected_year': sel_year,
        'available_years': available_years,
    })
