from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
import calendar
from datetime import date


@login_required
def reports_list(request):
    date_from    = request.GET.get('from', '')
    date_to      = request.GET.get('to', '')
    agent_filter = request.GET.get('agent', '')
    class_filter = request.GET.get('classification', '')
    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        data = vdata['reports']
        if date_from:
            date_from_int = int(date_from.replace('-', ''))
            data = [r for r in data if r['resolved_date'] >= date_from_int]
        if date_to:
            date_to_int = int(date_to.replace('-', ''))
            data = [r for r in data if r['resolved_date'] <= date_to_int]
        if agent_filter:
            data = [r for r in data if r['agent_name'] == agent_filter]
        if class_filter:
            data = [r for r in data if class_filter in r['classification']]
        agents = list(set(r['agent_name'] for r in vdata['reports']))
        return render(request, 'reports/list.html', {
            'data': data, 'agents': agents, 'is_manager': True,
            'filters': {'agent': agent_filter, 'from': date_from, 'to': date_to, 'classification': class_filter},
        })
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    where = "WHERE 1=1"
    if not is_manager_level(request.user):
        where += f" AND agent_name = '{request.user.first_name or request.user.username}'"
    if agent_filter:
        where += f" AND agent_name = '{agent_filter}'"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"
    if class_filter:
        where += f" AND classification LIKE N'%{class_filter}%'"

    cursor.execute(f"SELECT * FROM Customer_service_reports_by_A {where} ORDER BY created_at DESC")
    data = cursor.fetchall()

    agents = []
    if is_manager_level(request.user):
        cursor.execute("SELECT DISTINCT agent_name FROM Customer_service_reports_by_A")
        agents = [r['agent_name'] for r in cursor.fetchall()]
    conn.close()

    return render(request, 'reports/list.html', {
        'data': data, 'agents': agents, 'is_manager': is_manager_level(request.user),
        'filters': {'agent': agent_filter, 'from': date_from, 'to': date_to, 'classification': class_filter},
    })


@login_required
def monthly(request):
    year  = int(request.GET.get('year',  date.today().year))
    month = int(request.GET.get('month', date.today().month))
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years  = list(range(date.today().year - 2, date.today().year + 1))

    if get_role(request.user) == 'visitor':
        return render(request, 'reports/monthly.html', {
            'data': FAKE_MONTHLY, 'months': months, 'years': years,
            'selected_month': month, 'selected_year': year, 'is_manager': True,
        })

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    month_start = int(f"{year}{month:02d}01")
    month_end   = int(f"{year}{month:02d}{calendar.monthrange(year, month)[1]}")

    where = f"WHERE resolved_date BETWEEN {month_start} AND {month_end}"
    if not is_manager_level(request.user):
        where += f" AND agent_name = '{request.user.first_name or request.user.username}'"

    cursor.execute(f"""
        SELECT agent_name, COUNT(*) AS total,
               SUM(CASE WHEN classification LIKE N'تم%' THEN 1 ELSE 0 END) AS resolved,
               SUM(CASE WHEN classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_name ORDER BY total DESC
    """)
    data = cursor.fetchall()
    conn.close()

    return render(request, 'reports/monthly.html', {
        'data': data, 'months': months, 'years': years,
        'selected_month': month, 'selected_year': year,
        'is_manager': is_manager_level(request.user),
    })

    