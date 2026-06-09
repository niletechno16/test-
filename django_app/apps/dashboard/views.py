from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
from datetime import date


@login_required
def home(request):
    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')

    # Visitor → بيانات وهمية
    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        return render(request, 'dashboard/home.html', {
            'total_reports':       vdata['total_reports'],
            'total_resolved':      vdata['total_resolved'],
            'total_unresolved':    vdata['total_unresolved'],
            'total_customers':     vdata['total_customers'],
            'top_agents_resolved': vdata['top_agents_resolved'],
            'top_customers':       vdata['top_customers'],
            'common_problems':     vdata['common_problems'],
            'resolved_pct':        vdata['resolved_pct'],
            'unresolved_pct':      vdata['unresolved_pct'],
            'is_manager':          True,
            'date_from':           date_from,
            'date_to':             date_to,
        })

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    where = "WHERE 1=1"
    if not is_manager_level(request.user):
        where += f" AND agent_name = '{request.user.first_name or request.user.username}'"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"

    cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where}")
    total_reports = cursor.fetchone()['total']

    cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where} AND classification LIKE N'تم%'")
    total_resolved = cursor.fetchone()['total']

    cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where} AND classification LIKE N'لم يتم%'")
    total_unresolved = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM customer_detail_by_A")
    total_customers = cursor.fetchone()['total']

    cursor.execute(f"""
        SELECT TOP 5 agent_name, COUNT(*) AS total
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_name ORDER BY total DESC
    """)
    top_agents_resolved = cursor.fetchall()

    cursor.execute(f"""
        SELECT TOP 5 customer_name, COUNT(*) AS total
        FROM Customer_service_reports_by_A {where}
        GROUP BY customer_name ORDER BY total DESC
    """)
    top_customers = cursor.fetchall()

    cursor.execute(f"""
        SELECT TOP 5 classification, COUNT(*) AS total
        FROM Customer_service_reports_by_A {where}
        GROUP BY classification ORDER BY total DESC
    """)
    common_problems = cursor.fetchall()
    conn.close()

    resolved_pct   = round(total_resolved / total_reports * 100) if total_reports else 0
    unresolved_pct = round(total_unresolved / total_reports * 100) if total_reports else 0

    return render(request, 'dashboard/home.html', {
        'total_reports':       total_reports,
        'total_resolved':      total_resolved,
        'total_unresolved':    total_unresolved,
        'total_customers':     total_customers,
        'top_agents_resolved': top_agents_resolved,
        'top_customers':       top_customers,
        'common_problems':     common_problems,
        'resolved_pct':        resolved_pct,
        'unresolved_pct':      unresolved_pct,
        'is_manager':          is_manager_level(request.user),
        'date_from':           date_from,
        'date_to':             date_to,
    })