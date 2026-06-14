import random
import json
from datetime import date, timedelta
from collections import defaultdict


# ─── ثوابت الأسماء ───────────────────────────────────────────────────────────
AGENT_NAMES = [
    'أحمد محمد', 'سارة علي', 'محمد خالد', 'نورا حسن', 'عمر يوسف',
    'مريم إبراهيم', 'كريم عبد الله', 'دينا سامي', 'يوسف طارق', 'رنا وليد'
]

CUSTOMER_NAMES = [
    'شركة النيل', 'مؤسسة الأهرام', 'مجموعة الفجر', 'شركة الوادي',
    'مؤسسة الدلتا', 'شركة سيناء', 'مجموعة الرافدين', 'شركة الشروق',
    'مؤسسة الهلال', 'شركة الربيع'
]

PROBLEM_TYPES = [
    'انقطاع الإنترنت', 'بطء الشبكة', 'عطل في الجهاز', 'مشكلة في الإيميل',
    'نسيان كلمة المرور', 'فيروس في الجهاز', 'مشكلة في الطابعة',
    'انقطاع الكهرباء', 'مشكلة في البرنامج', 'مشكلة في الشاشة'
]


def _build_base_data(agent_names, customer_names, year):
    """يولّد تقارير ثابتة لكل السنة من 1 يناير حتى 31 ديسمبر،
    بـ seed ثابت لكل سنة عشان الداتا ما تتغيرش لو فتح المتصفح تاني."""
    rng = random.Random(year * 997)   # seed ثابت لكل سنة

    reports = []
    report_id = 1
    start = date(year, 1, 1)
    end   = date(year, 12, 31)
    total_days = (end - start).days + 1

    for agent_idx, agent_name in enumerate(agent_names):
        # كل أيجنت بين 2 و 5 تقارير في اليوم في المتوسط
        num_reports = rng.randint(int(total_days * 1.5), int(total_days * 3.5))

        for _ in range(num_reports):
            customer_name = rng.choice(customer_names)
            problem       = rng.choice(PROBLEM_TYPES)
            resolved      = rng.random() < 0.75
            report_date   = start + timedelta(days=rng.randint(0, total_days - 1))
            hour          = rng.randint(8, 17)
            minute        = rng.randint(0, 59)
            ampm          = 'AM' if hour < 12 else 'PM'
            hour_12       = hour if hour <= 12 else hour - 12

            classification    = f"تم حل مشكلة: {problem}" if resolved else f"لم يتم حل مشكلة: {problem}"
            summary           = f"تواصل العميل بخصوص {problem}. {'تم حل المشكلة بنجاح.' if resolved else 'المشكلة قيد المتابعة.'}"
            resolution_minutes = rng.randint(5, 120)

            reports.append({
                'conv_id':           report_id,
                'customer_name':     customer_name,
                'customer_phone':    f"01{rng.randint(0,2)}{rng.randint(10000000, 99999999)}",
                'agent_name':        agent_name,
                'agent_id':          agent_idx + 1,
                'classification':    classification,
                'summary':           summary,
                'resolved_date':     int(report_date.strftime('%Y%m%d')),
                'resolved_time':     f"{hour_12:02d}:{minute:02d} {ampm}",
                'created_at':        report_date.strftime('%Y-%m-%d'),
                'resolution_minutes': resolution_minutes,
                'status_label':       'Resolved' if resolved else 'Unresolved',
            })
            report_id += 1

    return reports


def _build_extra_days(agent_names, customer_names, from_date, to_date, id_start):
    """يولّد تقارير ليوم أو أكثر بـ seed مبني على التاريخ (ثابت لكل يوم)."""
    reports = []
    report_id = id_start
    cur = from_date

    while cur <= to_date:
        # seed = تاريخ + اسم الأيجنت → ثابت لكل يوم بالظبط
        day_seed = cur.year * 10000 + cur.month * 100 + cur.day
        rng = random.Random(day_seed)

        for agent_idx, agent_name in enumerate(agent_names):
            num = rng.randint(2, 5)
            for _ in range(num):
                customer_name = rng.choice(customer_names)
                problem       = rng.choice(PROBLEM_TYPES)
                resolved      = rng.random() < 0.75
                hour          = rng.randint(8, 17)
                minute        = rng.randint(0, 59)
                ampm          = 'AM' if hour < 12 else 'PM'
                hour_12       = hour if hour <= 12 else hour - 12

                reports.append({
                    'conv_id':            report_id,
                    'customer_name':      customer_name,
                    'customer_phone':     f"01{rng.randint(0,2)}{rng.randint(10000000, 99999999)}",
                    'agent_name':         agent_name,
                    'agent_id':           agent_idx + 1,
                    'classification':     f"تم حل مشكلة: {problem}" if resolved else f"لم يتم حل مشكلة: {problem}",
                    'summary':            f"تواصل العميل بخصوص {problem}. {'تم حل المشكلة بنجاح.' if resolved else 'المشكلة قيد المتابعة.'}",
                    'resolved_date':      int(cur.strftime('%Y%m%d')),
                    'resolved_time':      f"{hour_12:02d}:{minute:02d} {ampm}",
                    'created_at':         cur.strftime('%Y-%m-%d'),
                    'resolution_minutes': rng.randint(5, 120),
                    'status_label':       'Resolved' if resolved else 'Unresolved',
                })
                report_id += 1
        cur += timedelta(days=1)

    return reports


def _compute_summary(reports, customer_names):
    """يحسب كل الإحصائيات من الـ reports."""
    # agents
    agents_map = defaultdict(lambda: {'total': 0, 'resolved': 0, 'unresolved': 0, 'mins': []})
    for r in reports:
        a = r['agent_name']
        agents_map[a]['agent_name'] = a
        agents_map[a]['total']      += 1
        if r['classification'].startswith('تم حل'):
            agents_map[a]['resolved'] += 1
        else:
            agents_map[a]['unresolved'] += 1
        if r['resolution_minutes']:
            agents_map[a]['mins'].append(r['resolution_minutes'])

    agents = []
    for idx, (name, d) in enumerate(agents_map.items()):
        avg = round(sum(d['mins']) / len(d['mins'])) if d['mins'] else None
        agents.append({
            'agent_id':               idx + 1,
            'agent_name':             name,
            'total':                  d['total'],
            'resolved':               d['resolved'],
            'unresolved':             d['unresolved'],
            'avg_resolution_minutes': avg,
        })
    agents.sort(key=lambda x: x['total'], reverse=True)

    # customers
    cust_map = defaultdict(lambda: {'total': 0, 'resolved': 0, 'unresolved': 0, 'mins': [], 'phone': ''})
    rng_phone = random.Random(42)
    for r in reports:
        c = r['customer_name']
        cust_map[c]['total'] += 1
        if r['classification'].startswith('تم حل'):
            cust_map[c]['resolved'] += 1
        else:
            cust_map[c]['unresolved'] += 1
        if r['resolution_minutes']:
            cust_map[c]['mins'].append(r['resolution_minutes'])
        if not cust_map[c]['phone']:
            cust_map[c]['phone'] = f"01{rng_phone.randint(0,2)}{rng_phone.randint(10000000,99999999)}"

    customers = []
    for idx, (name, d) in enumerate(cust_map.items()):
        avg = round(sum(d['mins']) / len(d['mins'])) if d['mins'] else None
        customers.append({
            'customer_id':            idx + 101,
            'customer_name':          name,
            'customer_phone':         d['phone'],
            'total_reports':          d['total'],
            'resolved':               d['resolved'],
            'unresolved':             d['unresolved'],
            'avg_resolution_minutes': avg,
        })
    customers.sort(key=lambda x: x['total_reports'], reverse=True)

    total_reports    = len(reports)
    total_resolved   = sum(1 for r in reports if r['classification'].startswith('تم حل'))
    total_unresolved = total_reports - total_resolved

    # common problems
    prob_map = defaultdict(int)
    for r in reports:
        clf = r['classification']
        key = clf.split(':')[-1].strip() if ':' in clf else clf
        prob_map[key] += 1
    common_problems = sorted(
        [{'classification': k, 'total': v} for k, v in prob_map.items()],
        key=lambda x: x['total'], reverse=True
    )[:5]

    top_customers = sorted(
        [{'customer_name': c['customer_name'], 'total': c['total_reports']} for c in customers],
        key=lambda x: x['total'], reverse=True
    )[:5]

    # traffic by month
    monthly_counts = defaultdict(int)
    for r in reports:
        key = str(r['resolved_date'])[:6]  # YYYYMM
        label = f"{key[4:6]}/{key[:4]}"   # MM/YYYY
        monthly_counts[label] += 1
    traffic_by_date = sorted(
        [{'date': k, 'count': v} for k, v in monthly_counts.items()],
        key=lambda x: x['date']
    )

    all_mins = [r['resolution_minutes'] for r in reports if r['resolution_minutes']]
    avg_resolution_overall = round(sum(all_mins) / len(all_mins)) if all_mins else 0

    avg_resolution_by_agent = sorted([
        {'name': a['agent_name'], 'avg': a['avg_resolution_minutes']}
        for a in agents if a['avg_resolution_minutes']
    ], key=lambda x: x['avg'], reverse=True)

    avg_resolution_by_customer = sorted([
        {'name': c['customer_name'], 'avg': c['avg_resolution_minutes']}
        for c in customers if c['avg_resolution_minutes']
    ], key=lambda x: x['avg'], reverse=True)

    monthly = []
    for agent in agents:
        agent_reports = [r for r in reports if r['agent_name'] == agent['agent_name']]
        resolved   = sum(1 for r in agent_reports if r['classification'].startswith('تم حل'))
        monthly.append({
            'agent_name': agent['agent_name'],
            'total':      len(agent_reports),
            'resolved':   resolved,
            'unresolved': len(agent_reports) - resolved,
        })

    return {
        'reports':                   reports,
        'agents':                    agents,
        'customers':                 customers,
        'total_reports':             total_reports,
        'total_resolved':            total_resolved,
        'total_unresolved':          total_unresolved,
        'total_customers':           len(customers),
        'top_agents_resolved':       agents[:5],
        'top_customers':             top_customers,
        'common_problems':           common_problems,
        'resolved_pct':              round(total_resolved / total_reports * 100) if total_reports else 0,
        'unresolved_pct':            round(total_unresolved / total_reports * 100) if total_reports else 0,
        'monthly':                   monthly,
        'traffic_by_date':           traffic_by_date,
        'avg_resolution_overall':    avg_resolution_overall,
        'avg_resolution_by_agent':   avg_resolution_by_agent,
        'avg_resolution_by_customer': avg_resolution_by_customer,
    }


def generate_visitor_data():
    today = date.today()
    year  = today.year

    # أسماء ثابتة لكل session (seed ثابت)
    rng_names     = random.Random(year * 13)
    agent_names   = rng_names.sample(AGENT_NAMES,   rng_names.randint(4, 7))
    customer_names = rng_names.sample(CUSTOMER_NAMES, rng_names.randint(5, 8))

    # تقارير السنة الكاملة بـ seed ثابت (لا تتغير بين الجلسات)
    all_reports = _build_base_data(agent_names, customer_names, year)

    # فلتر: نبقّي بس التقارير اللي تاريخها <= النهارده
    today_int   = int(today.strftime('%Y%m%d'))
    all_reports = [r for r in all_reports if r['resolved_date'] <= today_int]

    return _compute_summary(all_reports, customer_names)


def get_visitor_data(request):
    """
    بيرجع الداتا من الـ session.
    لو مفيش session أو الـ session القديمة من يوم تاني → يولّد جديد.
    كده لو عدى يوم جديد، أول request بيولّد داتا جديدة تشمل اليوم الجديد.
    """
    today_str = date.today().strftime('%Y-%m-%d')

    cached_date = request.session.get('visitor_data_date')
    if 'visitor_data' not in request.session or cached_date != today_str:
        data = generate_visitor_data()
        request.session['visitor_data']      = json.dumps(data, default=str)
        request.session['visitor_data_date'] = today_str
        request.session.modified = True

    return json.loads(request.session['visitor_data'])
