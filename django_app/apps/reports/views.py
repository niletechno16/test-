from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
import calendar
from datetime import date

ARABIC_MONTHS = {
    1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',
    7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'
}


def _resolve_filter(request, today):
    default_from = today.replace(day=1).strftime('%Y-%m-%d')
    last_day     = calendar.monthrange(today.year, today.month)[1]
    default_to   = today.replace(day=last_day).strftime('%Y-%m-%d')

    filter_mode       = request.GET.get('filter_mode', 'monthyear')
    filter_month_year = request.GET.get('month_year', '')

    if filter_mode == 'monthyear' and filter_month_year:
        try:
            y, m = int(filter_month_year[:4]), int(filter_month_year[5:7])
            ld   = calendar.monthrange(y, m)[1]
            date_from   = f"{y}-{m:02d}-01"
            date_to     = f"{y}-{m:02d}-{ld:02d}"
            month_label = f"{ARABIC_MONTHS[m]} {y}"
        except (ValueError, IndexError):
            date_from, date_to = default_from, default_to
            month_label = f"{ARABIC_MONTHS[today.month]} {today.year}"
            filter_month_year = today.strftime('%Y-%m')
    elif filter_mode == 'exact':
        date_from   = request.GET.get('from', default_from)
        date_to     = request.GET.get('to',   default_to)
        month_label = f"{date_from} ← {date_to}"
        filter_month_year = ''
    else:
        date_from, date_to = default_from, default_to
        month_label       = f"{ARABIC_MONTHS[today.month]} {today.year}"
        filter_month_year = today.strftime('%Y-%m')

    return date_from, date_to, month_label, filter_mode, filter_month_year


@login_required
def reports_list(request):
    today = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)

    agent_filter = request.GET.get('agent', '')
    class_filter = request.GET.get('classification', '')

    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        data  = vdata['reports']
        if date_from:
            data = [r for r in data if r['resolved_date'] >= int(date_from.replace('-', ''))]
        if date_to:
            data = [r for r in data if r['resolved_date'] <= int(date_to.replace('-', ''))]
        if agent_filter:
            data = [r for r in data if r['agent_name'] == agent_filter]
        if class_filter:
            data = [r for r in data if class_filter in r['classification']]
        data = sorted(data, key=lambda r: (r['resolved_date'], r.get('resolved_time', '')), reverse=True)
        for r in data:
            c = r.get('classification', '')
            r['classification_type'] = 'resolved' if c.startswith('تم حل') else ('unresolved' if 'لم يتم' in c else 'other')
        agents = list(set(r['agent_name'] for r in vdata['reports']))
        return render(request, 'reports/list.html', {
            'data': data, 'agents': agents, 'is_manager': True,
            'month_label': month_label,
            'filter_mode': filter_mode, 'filter_month_year': filter_month_year,
            'filters': {'agent': agent_filter, 'from': date_from, 'to': date_to, 'classification': class_filter},
        })

    conn   = get_connection()
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

    cursor.execute(f"SELECT * FROM Customer_service_reports_by_A {where} ORDER BY resolved_date DESC, resolved_time DESC")
    data = cursor.fetchall()
    for r in data:
        c = r.get('classification', '') or ''
        r['classification_type'] = 'resolved' if c.startswith('تم حل') else ('unresolved' if 'لم يتم' in c else 'other')

    agents = []
    if is_manager_level(request.user):
        cursor.execute("SELECT DISTINCT agent_name FROM Customer_service_reports_by_A")
        agents = [r['agent_name'] for r in cursor.fetchall()]
    conn.close()

    return render(request, 'reports/list.html', {
        'data': data, 'agents': agents, 'is_manager': is_manager_level(request.user),
        'month_label': month_label,
        'filter_mode': filter_mode, 'filter_month_year': filter_month_year,
        'filters': {'agent': agent_filter, 'from': date_from, 'to': date_to, 'classification': class_filter},
    })


@login_required
def monthly(request):
    year  = int(request.GET.get('year',  date.today().year))
    month = int(request.GET.get('month', date.today().month))
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years  = list(range(date.today().year - 2, date.today().year + 1))

    if get_role(request.user) == 'visitor':
        vdata       = get_visitor_data(request)
        month_start = int(f"{year}{month:02d}01")
        month_end   = int(f"{year}{month:02d}{calendar.monthrange(year, month)[1]}")
        month_reps  = [r for r in vdata['reports'] if month_start <= r['resolved_date'] <= month_end]
        agents_seen = {}
        for r in month_reps:
            a = r['agent_name']
            if a not in agents_seen:
                agents_seen[a] = {'agent_name': a, 'total': 0, 'resolved': 0, 'unresolved': 0}
            agents_seen[a]['total'] += 1
            if r['classification'].startswith('تم حل'):
                agents_seen[a]['resolved'] += 1
            else:
                agents_seen[a]['unresolved'] += 1
        visitor_monthly = sorted(agents_seen.values(), key=lambda x: x['total'], reverse=True)
        return render(request, 'reports/monthly.html', {
            'data': visitor_monthly, 'months': months, 'years': years,
            'selected_month': month, 'selected_year': year, 'is_manager': True,
        })

    conn   = get_connection()
    cursor = conn.cursor(as_dict=True)

    month_start = int(f"{year}{month:02d}01")
    month_end   = int(f"{year}{month:02d}{calendar.monthrange(year, month)[1]}")

    where = f"WHERE resolved_date BETWEEN {month_start} AND {month_end}"
    if not is_manager_level(request.user):
        where += f" AND agent_name = '{request.user.first_name or request.user.username}'"

    cursor.execute(f"""
        SELECT agent_name, COUNT(*) AS total,
               SUM(CASE WHEN classification LIKE N'تم حل%' THEN 1 ELSE 0 END) AS resolved,
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
