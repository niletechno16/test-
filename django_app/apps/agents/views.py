from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
from datetime import date
from collections import defaultdict
import calendar

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


def _filter_reports(reports, date_from, date_to):
    df = int(date_from.replace('-', ''))
    dt = int(date_to.replace('-', ''))
    return [r for r in reports if df <= r['resolved_date'] <= dt]


def _agents_from_reports(all_agents, filtered_reports):
    """يحسب إحصائيات الأيجنت من الـ reports المفلترة."""
    stats = defaultdict(lambda: {'total': 0, 'resolved': 0, 'unresolved': 0, 'mins': []})
    for r in filtered_reports:
        a = r['agent_name']
        stats[a]['total'] += 1
        if r['classification'].startswith('تم حل'):
            stats[a]['resolved'] += 1
        else:
            stats[a]['unresolved'] += 1
        if r.get('resolution_minutes'):
            stats[a]['mins'].append(r['resolution_minutes'])

    result = []
    for agent in all_agents:
        name = agent['agent_name']
        s    = stats.get(name, {'total': 0, 'resolved': 0, 'unresolved': 0, 'mins': []})
        mins = s['mins']
        result.append({
            'agent_id':               agent['agent_id'],
            'agent_name':             name,
            'total':                  s['total'],
            'resolved':               s['resolved'],
            'unresolved':             s['unresolved'],
            'avg_resolution_minutes': round(sum(mins)/len(mins)) if mins else None,
        })
    return sorted(result, key=lambda x: x['total'], reverse=True)


@login_required
def agents_list(request):
    today  = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)
    search = request.GET.get('search', '')

    if get_role(request.user) == 'visitor':
        vdata            = get_visitor_data(request)
        filtered_reports = _filter_reports(vdata['reports'], date_from, date_to)
        agents           = _agents_from_reports(vdata['agents'], filtered_reports)
        if search:
            agents = [a for a in agents if search in a['agent_name']]
        return render(request, 'agents/index.html', {
            'agents': agents, 'is_manager': True,
            'search': search, 'date_from': date_from, 'date_to': date_to,
            'month_label': month_label,
            'filter_mode': filter_mode, 'filter_month_year': filter_month_year,
        })

    conn   = get_connection()
    cursor = conn.cursor(as_dict=True)

    where = "WHERE 1=1"
    if not is_manager_level(request.user):
        where += f" AND agent_name = '{request.user.first_name or request.user.username}'"
    if search:
        where += f" AND agent_name LIKE N'%{search}%'"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"

    cursor.execute(f"""
        SELECT agent_id, agent_name, COUNT(*) AS total,
               SUM(CASE WHEN classification LIKE N'تم حل%' THEN 1 ELSE 0 END) AS resolved,
               SUM(CASE WHEN classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved,
               AVG(CAST(resolution_minutes AS FLOAT)) AS avg_resolution_minutes
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_id, agent_name ORDER BY total DESC
    """)
    agents = cursor.fetchall()
    conn.close()

    return render(request, 'agents/index.html', {
        'agents': agents, 'is_manager': is_manager_level(request.user),
        'search': search, 'date_from': date_from, 'date_to': date_to,
        'month_label': month_label,
        'filter_mode': filter_mode, 'filter_month_year': filter_month_year,
    })


@login_required
def agent_detail(request, agent_id):
    today = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)

    if get_role(request.user) == 'visitor':
        vdata         = get_visitor_data(request)
        agent         = next((a for a in vdata['agents'] if a['agent_id'] == agent_id), None)
        agent_reports = _filter_reports(
            [r for r in vdata['reports'] if r['agent_id'] == agent_id],
            date_from, date_to
        )
        agent_reports = sorted(agent_reports, key=lambda r: (r['resolved_date'], r.get('resolved_time', '')), reverse=True)
        return render(request, 'agents/detail.html', {
            'agent': agent, 'reports': agent_reports,
            'is_manager': True, 'date_from': date_from, 'date_to': date_to,
            'month_label': month_label,
            'filter_mode': filter_mode, 'filter_month_year': filter_month_year,
        })

    conn   = get_connection()
    cursor = conn.cursor(as_dict=True)

    cursor.execute(f"SELECT TOP 1 agent_id, agent_name FROM Customer_service_reports_by_A WHERE agent_id = {agent_id}")
    agent = cursor.fetchone()

    where = f"WHERE agent_id = {agent_id}"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"

    cursor.execute(f"SELECT * FROM Customer_service_reports_by_A {where} ORDER BY resolved_date DESC, resolved_time DESC")
    reports = cursor.fetchall()
    conn.close()

    return render(request, 'agents/detail.html', {
        'agent': agent, 'reports': reports,
        'is_manager': is_manager_level(request.user),
        'date_from': date_from, 'date_to': date_to,
        'month_label': month_label,
        'filter_mode': filter_mode, 'filter_month_year': filter_month_year,
    })
