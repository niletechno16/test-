import random
from datetime import date, timedelta


def generate_visitor_data():
    random.seed()  # seed جديد كل مرة

    # ---------------- الأسماء ----------------
    agent_names = random.sample([
        'أحمد محمد', 'سارة علي', 'محمد خالد', 'نورا حسن', 'عمر يوسف',
        'مريم إبراهيم', 'كريم عبد الله', 'دينا سامي', 'يوسف طارق', 'رنا وليد'
    ], random.randint(4, 7))

    customer_names = random.sample([
        'شركة النيل', 'مؤسسة الأهرام', 'مجموعة الفجر', 'شركة الوادي',
        'مؤسسة الدلتا', 'شركة سيناء', 'مجموعة الرافدين', 'شركة الشروق',
        'مؤسسة الهلال', 'شركة الربيع'
    ], random.randint(5, 8))

    problem_types = [
        'انقطاع الإنترنت', 'بطء الشبكة', 'عطل في الجهاز', 'مشكلة في الإيميل',
        'نسيان كلمة المرور', 'فيروس في الجهاز', 'مشكلة في الطابعة',
        'انقطاع الكهرباء', 'مشكلة في البرنامج', 'مشكلة في الشاشة'
    ]

    # ---------------- توليد التقارير ----------------
    reports = []
    report_id = 1
    base_date = date(2026, 1, 1)

    for agent_idx, agent_name in enumerate(agent_names):
        agent_id = agent_idx + 1
        num_reports = random.randint(8, 20)

        for _ in range(num_reports):
            customer_name = random.choice(customer_names)
            problem = random.choice(problem_types)
            resolved = random.random() < 0.75  # 75% نسبة حل
            days_offset = random.randint(0, 150)
            report_date = base_date + timedelta(days=days_offset)
            hour = random.randint(8, 17)
            minute = random.randint(0, 59)
            ampm = 'AM' if hour < 12 else 'PM'
            hour_12 = hour if hour <= 12 else hour - 12

            classification = f"تم حل مشكلة: {problem}" if resolved else f"لم يتم حل مشكلة: {problem}"
            summary = f"تواصل العميل بخصوص {problem}. {'تم حل المشكلة بنجاح.' if resolved else 'المشكلة قيد المتابعة.'}"

            resolution_minutes = random.randint(5, 120)

            reports.append({
                'conv_id': report_id,
                'customer_name': customer_name,
                'customer_phone': f"01{random.randint(0,2)}{random.randint(10000000, 99999999)}",
                'agent_name': agent_name,
                'agent_id': agent_id,
                'classification': classification,
                'summary': summary,
                'resolved_date': int(report_date.strftime('%Y%m%d')),
                'resolved_time': f"{hour_12:02d}:{minute:02d} {ampm}",
                'created_at': report_date,
                'resolution_minutes': resolution_minutes,
            })
            report_id += 1

    # ---------------- إحصائيات الأجنت ----------------
    agents = []
    for agent_idx, agent_name in enumerate(agent_names):
        agent_id = agent_idx + 1
        agent_reports = [r for r in reports if r['agent_name'] == agent_name]
        total = len(agent_reports)
        resolved = sum(1 for r in agent_reports if r['classification'].startswith('تم حل'))
        unresolved = total - resolved
        mins = [r['resolution_minutes'] for r in agent_reports if r['resolution_minutes'] is not None]
        avg_resolution_minutes = round(sum(mins) / len(mins)) if mins else None
        agents.append({
            'agent_id': agent_id,
            'agent_name': agent_name,
            'total': total,
            'resolved': resolved,
            'unresolved': unresolved,
            'avg_resolution_minutes': avg_resolution_minutes,
        })

    agents.sort(key=lambda x: x['total'], reverse=True)

    # ---------------- إحصائيات العملاء ----------------
    customers = []
    for idx, customer_name in enumerate(customer_names):
        customer_reports = [r for r in reports if r['customer_name'] == customer_name]
        total = len(customer_reports)
        resolved = sum(1 for r in customer_reports if r['classification'].startswith('تم حل'))
        unresolved = total - resolved
        phone = f"01{random.randint(0,2)}{random.randint(10000000, 99999999)}"
        mins = [r['resolution_minutes'] for r in customer_reports if r['resolution_minutes'] is not None]
        avg_resolution_minutes = round(sum(mins) / len(mins)) if mins else None
        customers.append({
            'customer_id': idx + 101,
            'customer_name': customer_name,
            'customer_phone': phone,
            'total_reports': total,
            'resolved': resolved,
            'unresolved': unresolved,
            'avg_resolution_minutes': avg_resolution_minutes,
        })

    customers.sort(key=lambda x: x['total_reports'], reverse=True)

    # ---------------- إحصائيات عامة ----------------
    total_reports = len(reports)
    total_resolved = sum(1 for r in reports if r['classification'].startswith('تم حل'))
    total_unresolved = total_reports - total_resolved

    # ---------------- أكثر المشاكل ----------------
    problem_counts = {}
    for r in reports:
        clf = r['classification']
        key = clf.split(':')[-1].strip() if ':' in clf else clf
        problem_counts[key] = problem_counts.get(key, 0) + 1

    common_problems = sorted(
        [{'classification': k, 'total': v} for k, v in problem_counts.items()],
        key=lambda x: x['total'], reverse=True
    )[:5]

    # ---------------- أكثر العملاء ----------------
    top_customers = sorted(
        [{'customer_name': c['customer_name'], 'total': c['total_reports']} for c in customers],
        key=lambda x: x['total'], reverse=True
    )[:5]

    # ---------------- التقارير الشهرية ----------------
    monthly = []
    for agent in agents:
        agent_reports = [r for r in reports if r['agent_name'] == agent['agent_name']]
        resolved = sum(1 for r in agent_reports if r['classification'].startswith('تم حل'))
        unresolved = len(agent_reports) - resolved
        monthly.append({
            'agent_name': agent['agent_name'],
            'total': len(agent_reports),
            'resolved': resolved,
            'unresolved': unresolved,
        })

    # ---------------- ترافيك الرسائل (شهري، مع ضمان عدم النزول للصفر) ----------------
    from collections import defaultdict
    monthly_counts = defaultdict(int)
    for r in reports:
        d = r['created_at']
        if hasattr(d, 'strftime'):
            key = d.strftime('%Y-%m')
        else:
            key = str(d)[:7]  # "2026-01"
        monthly_counts[key] += 1

    # تأكد إن كل شهر من يناير لآخر شهر فيه قيمة (مينفعش يبقى صفر)
    if monthly_counts:
        all_months = sorted(monthly_counts.keys())
        first = all_months[0]
        last  = all_months[-1]
        from datetime import date as _date
        fy, fm = int(first[:4]), int(first[5:7])
        ly, lm = int(last[:4]),  int(last[5:7])
        cur_y, cur_m = fy, fm
        while (cur_y, cur_m) <= (ly, lm):
            key = f"{cur_y}-{cur_m:02d}"
            if key not in monthly_counts:
                # شهر فاضي → أعطيه قيمة صغيرة عشوائية بين 3 و 8
                monthly_counts[key] = random.randint(3, 8)
            cur_m += 1
            if cur_m > 12:
                cur_m = 1
                cur_y += 1

    traffic_by_date = sorted(
        [{'date': k, 'count': v} for k, v in monthly_counts.items()],
        key=lambda x: x['date']
    )

    # ---------------- متوسط وقت الحل الكلي ----------------
    all_mins = [r['resolution_minutes'] for r in reports if r['resolution_minutes'] is not None]
    avg_resolution_overall = round(sum(all_mins) / len(all_mins)) if all_mins else 0

    # ---------------- متوسط وقت الحل لكل عميل ----------------
    avg_resolution_by_customer = []
    for c in customers:
        if c['avg_resolution_minutes']:
            avg_resolution_by_customer.append({
                'name': c['customer_name'],
                'avg': c['avg_resolution_minutes'],
            })
    avg_resolution_by_customer.sort(key=lambda x: x['avg'], reverse=True)

    # ---------------- متوسط وقت الحل لكل أيجنت ----------------
    avg_resolution_by_agent = []
    for a in agents:
        if a['avg_resolution_minutes']:
            avg_resolution_by_agent.append({
                'name': a['agent_name'],
                'avg': a['avg_resolution_minutes'],
            })
    avg_resolution_by_agent.sort(key=lambda x: x['avg'], reverse=True)

    return {
        'reports': reports,
        'agents': agents,
        'customers': customers,
        'total_reports': total_reports,
        'total_resolved': total_resolved,
        'total_unresolved': total_unresolved,
        'total_customers': len(customers),
        'top_agents_resolved': agents[:5],
        'top_customers': top_customers,
        'common_problems': common_problems,
        'resolved_pct': round(total_resolved / total_reports * 100) if total_reports else 0,
        'unresolved_pct': round(total_unresolved / total_reports * 100) if total_reports else 0,
        'monthly': monthly,
        'traffic_by_date': traffic_by_date,
        'avg_resolution_overall':      avg_resolution_overall,
        'avg_resolution_by_customer':  avg_resolution_by_customer,
        'avg_resolution_by_agent':     avg_resolution_by_agent,
    }


import json

def get_visitor_data(request):
    if 'visitor_data' not in request.session:
        data = generate_visitor_data()
        # نحول الداتا لـ JSON ونحفظها في الـ session
        request.session['visitor_data'] = json.dumps(data, default=str)
        request.session.modified = True
    
    return json.loads(request.session['visitor_data'])