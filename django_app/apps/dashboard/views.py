from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import get_visitor_data
from datetime import date
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


def _date_int(date_str):
    return int(date_str.replace('-', ''))


def _empty_context():
    """بيرجع context فاضي بأصفار لو فيه مشكلة في DB"""
    return {
        'total_reports':           0,
        'total_resolved':          0,
        'total_unresolved':        0,
        'total_customers':         0,
        'top_agents_resolved':     [],
        'top_customers':           [],
        'common_problems':         [],
        'resolved_pct':            0,
        'unresolved_pct':          0,
        'traffic_by_date':         [],
        'avg_resolution_overall':  0,
        'avg_resolution_by_agent': [],
        'db_error':                True,
    }


@login_required
def home(request):
    today = date.today()
    date_from, date_to, month_label, filter_mode, filter_month_year = _resolve_filter(request, today)

    base_ctx = {
        'is_manager':        is_manager_level(request.user),
        'date_from':         date_from,
        'date_to':           date_to,
        'month_label':       month_label,
        'filter_mode':       filter_mode,
        'filter_month_year': filter_month_year,
    }

    # ─── Visitor mode ────────────────────────────────────────────────────────
    if get_role(request.user) == 'visitor':
        try:
            vdata = get_visitor_data(request)
            df_int = _date_int(date_from)
            dt_int = _date_int(date_to)

            all_reports = vdata['reports']
            filtered    = [r for r in all_reports if df_int <= r['resolved_date'] <= dt_int]

            total_reports    = len(filtered)
            total_resolved   = sum(1 for r in filtered if r['classification'].startswith('تم حل'))
            total_unresolved = sum(1 for r in filtered if 'لم يتم' in r['classification'])
            resolved_pct     = round(total_resolved   / total_reports * 100) if total_reports else 0
            unresolved_pct   = round(total_unresolved / total_reports * 100) if total_reports else 0
            total_customers  = vdata['total_customers']

            avg_mins = [r['resolution_minutes'] for r in filtered if r.get('resolution_minutes')]
            avg_resolution_overall = round(sum(avg_mins) / len(avg_mins)) if avg_mins else 0

            agents_map = {}
            for r in filtered:
                a = r['agent_name']
                if a not in agents_map:
                    agents_map[a] = {'agent_name': a, 'total': 0, 'resolved': 0, 'unresolved': 0}
                agents_map[a]['total'] += 1
                if r['classification'].startswith('تم حل'):
                    agents_map[a]['resolved'] += 1
                if 'لم يتم' in r['classification']:
                    agents_map[a]['unresolved'] += 1
            top_agents_resolved = sorted(agents_map.values(), key=lambda x: x['total'], reverse=True)[:5]

            cust_map = {}
            for r in filtered:
                c = r['customer_name']
                cust_map[c] = cust_map.get(c, 0) + 1
            top_customers = sorted(
                [{'customer_name': k, 'total': v} for k, v in cust_map.items()],
                key=lambda x: x['total'], reverse=True
            )[:5]

            prob_map = {}
            for r in filtered:
                cl = r['classification']
                prob_map[cl] = prob_map.get(cl, 0) + 1
            common_problems = sorted(
                [{'classification': k, 'total': v} for k, v in prob_map.items()],
                key=lambda x: x['total'], reverse=True
            )[:5]

            traffic_map = {}
            for r in filtered:
                d_str = str(r['resolved_date'])
                label = f"{d_str[6:8]}/{d_str[4:6]}/{d_str[:4]}"
                traffic_map[label] = traffic_map.get(label, 0) + 1
            traffic_by_date = [{'date': k, 'count': v} for k, v in sorted(traffic_map.items())]

            agent_mins = {}
            for r in filtered:
                if r.get('resolution_minutes'):
                    a = r['agent_name']
                    if a not in agent_mins:
                        agent_mins[a] = []
                    agent_mins[a].append(r['resolution_minutes'])
            avg_resolution_by_agent = sorted([
                {'name': a, 'avg': round(sum(mins)/len(mins))}
                for a, mins in agent_mins.items()
            ], key=lambda x: x['avg'], reverse=True)[:8]

            return render(request, 'dashboard/home.html', {
                **base_ctx,
                'total_reports':           total_reports,
                'total_resolved':          total_resolved,
                'total_unresolved':        total_unresolved,
                'total_customers':         total_customers,
                'top_agents_resolved':     top_agents_resolved,
                'top_customers':           top_customers,
                'common_problems':         common_problems,
                'resolved_pct':            resolved_pct,
                'unresolved_pct':          unresolved_pct,
                'traffic_by_date':         traffic_by_date,
                'avg_resolution_overall':  avg_resolution_overall,
                'avg_resolution_by_agent': avg_resolution_by_agent,
                'is_manager':              True,
            })
        except Exception:
            return render(request, 'dashboard/home.html', {**base_ctx, **_empty_context()})

    # ─── Real DB mode ────────────────────────────────────────────────────────
    try:
        conn   = get_connection()
        cursor = conn.cursor(as_dict=True)

        df_int = _date_int(date_from)
        dt_int = _date_int(date_to)

        where = f"WHERE resolved_date BETWEEN {df_int} AND {dt_int}"
        if not is_manager_level(request.user):
            where += f" AND agent_name = '{request.user.first_name or request.user.username}'"

        cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where}")
        total_reports = cursor.fetchone()['total']

        cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where} AND classification LIKE N'تم حل%'")
        total_resolved = cursor.fetchone()['total']

        cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where} AND classification LIKE N'لم يتم%'")
        total_unresolved = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) AS total FROM customer_detail_by_A")
        total_customers = cursor.fetchone()['total']

        resolved_pct   = round(total_resolved   / total_reports * 100) if total_reports else 0
        unresolved_pct = round(total_unresolved / total_reports * 100) if total_reports else 0

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
            GROUP BY agent_name ORDER BY avg DESC
        """)
        avg_resolution_by_agent = [
            {'name': r['name'], 'avg': round(r['avg'])} for r in cursor.fetchall()
        ]

        cursor.execute(f"""
            SELECT resolved_date, COUNT(*) AS cnt
            FROM Customer_service_reports_by_A {where}
            GROUP BY resolved_date ORDER BY resolved_date
        """)
        traffic_by_date = []
        for r in cursor.fetchall():
            d_str = str(r['resolved_date'])
            label = f"{d_str[6:8]}/{d_str[4:6]}/{d_str[:4]}"
            traffic_by_date.append({'date': label, 'count': r['cnt']})

        conn.close()

        return render(request, 'dashboard/home.html', {
            **base_ctx,
            'total_reports':           total_reports,
            'total_resolved':          total_resolved,
            'total_unresolved':        total_unresolved,
            'total_customers':         total_customers,
            'top_agents_resolved':     top_agents_resolved,
            'top_customers':           top_customers,
            'common_problems':         common_problems,
            'resolved_pct':            resolved_pct,
            'unresolved_pct':          unresolved_pct,
            'traffic_by_date':         traffic_by_date,
            'avg_resolution_overall':  avg_resolution_overall,
            'avg_resolution_by_agent': avg_resolution_by_agent,
        })

    except Exception:
        return render(request, 'dashboard/home.html', {**base_ctx, **_empty_context()})
