from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
from datetime import date, datetime
import calendar


ARABIC_MONTHS = {
    1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',
    7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'
}


def _make_month_label(date_from_str, date_to_str):
    """بيعمل label للفترة المختارة بناءً على التواريخ المفلترة"""
    try:
        d_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        d_to   = datetime.strptime(date_to_str,   '%Y-%m-%d').date()
        if d_from.year == d_to.year and d_from.month == d_to.month:
            return f"{ARABIC_MONTHS[d_from.month]} {d_from.year}"
        elif d_from.year == d_to.year:
            return f"{ARABIC_MONTHS[d_from.month]} – {ARABIC_MONTHS[d_to.month]} {d_from.year}"
        else:
            return f"{ARABIC_MONTHS[d_from.month]} {d_from.year} – {ARABIC_MONTHS[d_to.month]} {d_to.year}"
    except Exception:
        today = date.today()
        return f"{ARABIC_MONTHS[today.month]} {today.year}"


@login_required
def home(request):
    today = date.today()
    # الافتراضي: أول وآخر يوم في الشهر الحالي
    default_from = today.replace(day=1).strftime('%Y-%m-%d')
    last_day     = calendar.monthrange(today.year, today.month)[1]
    default_to   = today.replace(day=last_day).strftime('%Y-%m-%d')

    date_from = request.GET.get('from', default_from)
    date_to   = request.GET.get('to',   default_to)

    # label ديناميكي بناءً على الفلتر المختار
    month_label = _make_month_label(date_from, date_to)

    # Visitor → بيانات وهمية
    if get_role(request.user) == 'visitor':
        vdata = get_visitor_data(request)
        return render(request, 'dashboard/home.html', {
            'total_reports':               vdata['total_reports'],
            'total_resolved':              vdata['total_resolved'],
            'total_unresolved':            vdata['total_unresolved'],
            'total_customers':             vdata['total_customers'],
            'top_agents_resolved':         vdata['top_agents_resolved'],
            'top_customers':               vdata['top_customers'],
            'common_problems':             vdata['common_problems'],
            'resolved_pct':                vdata['resolved_pct'],
            'unresolved_pct':              vdata['unresolved_pct'],
            'traffic_by_date':             vdata['traffic_by_date'],
            'avg_resolution_overall':      vdata['avg_resolution_overall'],
            'avg_resolution_by_customer':  vdata['avg_resolution_by_customer'],
            'avg_resolution_by_agent':     vdata['avg_resolution_by_agent'],
            'is_manager':                  True,
            'date_from':                   date_from,
            'date_to':                     date_to,
            'month_label':                 month_label,
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

    cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where} AND classification LIKE N'تم حل%'")
    total_resolved = cursor.fetchone()['total']

    cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where} AND classification LIKE N'لم يتم%'")
    total_unresolved = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM customer_detail_by_A")
    total_customers = cursor.fetchone()['total']

    cursor.execute(f"""
        SELECT TOP 5 agent_name,
               COUNT(*) AS total,
               SUM(CASE WHEN classification LIKE N'تم حل%' THEN 1 ELSE 0 END) AS resolved,
               SUM(CASE WHEN classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
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
    cursor.execute(f"""
        SELECT AVG(CAST(resolution_minutes AS FLOAT)) AS avg_mins
        FROM Customer_service_reports_by_A {where}
        AND resolution_minutes IS NOT NULL
    """)
    row = cursor.fetchone()
    avg_resolution_overall = round(row['avg_mins']) if row and row['avg_mins'] else 0

    cursor.execute(f"""
        SELECT TOP 8 agent_name AS name,
               AVG(CAST(resolution_minutes AS FLOAT)) AS avg
        FROM Customer_service_reports_by_A {where}
        AND resolution_minutes IS NOT NULL
        GROUP BY agent_name
        ORDER BY avg DESC
    """)
    avg_resolution_by_agent = [
        {'name': r['name'], 'avg': round(r['avg'])} for r in cursor.fetchall()
    ]

    # ترافيك التقارير بالتاريخ (resolved_date مخزن كـ YYYYMMDD int)
    cursor.execute(f"""
        SELECT resolved_date, COUNT(*) AS cnt
        FROM Customer_service_reports_by_A {where}
        AND resolved_date IS NOT NULL
        GROUP BY resolved_date
        ORDER BY resolved_date
    """)
    traffic_by_date = []
    for r in cursor.fetchall():
        try:
            d = str(r['resolved_date'])  # e.g. '20260101'
            formatted = f"{d[6:8]}/{d[4:6]}/{d[0:4]}"  # '01/01/2026'
            traffic_by_date.append({'date': formatted, 'count': r['cnt']})
        except Exception:
            pass

    # متوسط وقت الحل لكل عميل
    cursor.execute(f"""
        SELECT TOP 8 customer_name AS name,
               AVG(CAST(resolution_minutes AS FLOAT)) AS avg
        FROM Customer_service_reports_by_A {where}
        AND resolution_minutes IS NOT NULL
        GROUP BY customer_name
        ORDER BY avg DESC
    """)
    avg_resolution_by_customer = [
        {'name': r['name'], 'avg': round(r['avg'])} for r in cursor.fetchall()
    ]

    conn.close()

    resolved_pct   = round(total_resolved / total_reports * 100) if total_reports else 0
    unresolved_pct = round(total_unresolved / total_reports * 100) if total_reports else 0

    # تأكد إن المجموع منطقي — لو الاثنين صفر مع وجود تقارير، يبقى فيه تصنيفات أخرى

    return render(request, 'dashboard/home.html', {
        'total_reports':               total_reports,
        'total_resolved':              total_resolved,
        'total_unresolved':            total_unresolved,
        'total_customers':             total_customers,
        'top_agents_resolved':         top_agents_resolved,
        'top_customers':               top_customers,
        'common_problems':             common_problems,
        'resolved_pct':                resolved_pct,
        'unresolved_pct':              unresolved_pct,
        'traffic_by_date':             traffic_by_date,
        'avg_resolution_overall':      avg_resolution_overall,
        'avg_resolution_by_customer':  avg_resolution_by_customer,
        'avg_resolution_by_agent':     avg_resolution_by_agent,
        'is_manager':                  is_manager_level(request.user),
        'date_from':                   date_from,
        'date_to':                     date_to,
        'month_label':                 month_label,
    })