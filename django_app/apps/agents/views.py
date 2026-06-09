from urllib import request

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data


@login_required
def agents_list(request):
    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')
    search    = request.GET.get('search', '')

    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        agents = vdata['agents']
        if search:
            agents = [a for a in agents if search in a['agent_name']]
        return render(request, 'agents/index.html', {
            'agents': agents, 'is_manager': True,
            'search': search, 'date_from': date_from, 'date_to': date_to,
        })
    conn = get_connection()
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
               SUM(CASE WHEN classification LIKE N'تم%' THEN 1 ELSE 0 END) AS resolved,
               SUM(CASE WHEN classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_id, agent_name ORDER BY total DESC
    """)
    agents = cursor.fetchall()
    conn.close()

    return render(request, 'agents/index.html', {
        'agents': agents, 'is_manager': is_manager_level(request.user),
        'search': search, 'date_from': date_from, 'date_to': date_to,
    })


@login_required
def agent_detail(request, agent_id):
    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')

    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        agent = next((a for a in vdata['agents'] if a['agent_id'] == agent_id), None)
        agent_reports = [r for r in vdata['reports'] if r['agent_id'] == agent_id]
        if date_from:
            date_from_int = int(date_from.replace('-', ''))
            agent_reports = [r for r in agent_reports if r['resolved_date'] >= date_from_int]
        if date_to:
            date_to_int = int(date_to.replace('-', ''))
            agent_reports = [r for r in agent_reports if r['resolved_date'] <= date_to_int]
        return render(request, 'agents/detail.html', {
            'agent': agent, 'reports': agent_reports,
            'is_manager': True, 'date_from': date_from, 'date_to': date_to,
        })

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    where = f"WHERE agent_id = {agent_id}"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"

    cursor.execute(f"SELECT TOP 1 agent_name FROM Customer_service_reports_by_A WHERE agent_id = {agent_id}")
    agent = cursor.fetchone()

    cursor.execute(f"SELECT * FROM Customer_service_reports_by_A {where} ORDER BY created_at DESC")
    reports = cursor.fetchall()
    conn.close()

    return render(request, 'agents/detail.html', {
        'agent': agent, 'reports': reports,
        'is_manager': is_manager_level(request.user),
        'date_from': date_from, 'date_to': date_to,
    })