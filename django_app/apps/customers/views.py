from urllib import request
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data

@login_required
def customers_list(request):
    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')
    search    = request.GET.get('search', '')
    if get_role(request.user) != 'visitor' and not is_manager_level(request.user):
        return redirect('home')

    search = request.GET.get('search', '')

    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        customers = vdata['customers']
        if search:
            customers = [c for c in customers if search in c['customer_name'] or search in c['customer_phone']]
        return render(request, 'customers/index.html', {
            'customers': customers, 'search': search, 'is_manager': True,
            'date_from': date_from, 'date_to': date_to,
        })

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    query = """
        SELECT c.*,
               COUNT(r.id) AS total_reports,
               SUM(CASE WHEN r.classification LIKE N'تم%' THEN 1 ELSE 0 END) AS resolved,
               SUM(CASE WHEN r.classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
        FROM customer_detail_by_A c
        LEFT JOIN Customer_service_reports_by_A r ON c.customer_id = r.customer_id
    """
    if search:
        query += f" WHERE c.customer_name LIKE N'%{search}%' OR c.customer_phone LIKE N'%{search}%'"
    query += " GROUP BY c.customer_id, c.customer_name, c.customer_phone ORDER BY total_reports DESC"

    cursor.execute(query)
    customers = cursor.fetchall()
    conn.close()

    return render(request, 'customers/index.html', {
        'customers': customers, 'search': search, 'is_manager': True,
    })


@login_required
def customer_detail(request, customer_id):
    if get_role(request.user) != 'visitor' and not is_manager_level(request.user):
        return redirect('home')

    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        customer = next((c for c in vdata['customers'] if c['customer_id'] == customer_id), None)
        reports = [r for r in vdata['reports'] if r['customer_name'] == customer['customer_name']]
        return render(request, 'customers/detail.html', {
            'customer': customer, 'reports': reports, 'is_manager': True,
        })

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    cursor.execute(f"SELECT * FROM customer_detail_by_A WHERE customer_id = {customer_id}")
    customer = cursor.fetchone()

    cursor.execute(f"SELECT * FROM Customer_service_reports_by_A WHERE customer_id = {customer_id} ORDER BY created_at DESC")
    reports = cursor.fetchall()
    conn.close()

    return render(request, 'customers/detail.html', {
        'customer': customer, 'reports': reports, 'is_manager': True,
    })