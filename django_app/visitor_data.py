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

            reports.append({
                'id': report_id,
                'customer_name': customer_name,
                'customer_phone': f"01{random.randint(0,2)}{random.randint(10000000, 99999999)}",
                'agent_name': agent_name,
                'agent_id': agent_id,
                'classification': classification,
                'summary': summary,
                'resolved_date': int(report_date.strftime('%Y%m%d')),
                'resolved_time': f"{hour_12:02d}:{minute:02d} {ampm}",
                'created_at': report_date,
            })
            report_id += 1

    # ---------------- إحصائيات الأجنت ----------------
    agents = []
    for agent_idx, agent_name in enumerate(agent_names):
        agent_id = agent_idx + 1
        agent_reports = [r for r in reports if r['agent_name'] == agent_name]
        total = len(agent_reports)
        resolved = sum(1 for r in agent_reports if 'تم حل' in r['classification'])
        unresolved = total - resolved
        agents.append({
            'agent_id': agent_id,
            'agent_name': agent_name,
            'total': total,
            'resolved': resolved,
            'unresolved': unresolved,
        })

    agents.sort(key=lambda x: x['total'], reverse=True)

    # ---------------- إحصائيات العملاء ----------------
    customers = []
    for idx, customer_name in enumerate(customer_names):
        customer_reports = [r for r in reports if r['customer_name'] == customer_name]
        total = len(customer_reports)
        resolved = sum(1 for r in customer_reports if 'تم حل' in r['classification'])
        unresolved = total - resolved
        phone = f"01{random.randint(0,2)}{random.randint(10000000, 99999999)}"
        customers.append({
            'customer_id': idx + 101,
            'customer_name': customer_name,
            'customer_phone': phone,
            'total_reports': total,
            'resolved': resolved,
            'unresolved': unresolved,
        })

    customers.sort(key=lambda x: x['total_reports'], reverse=True)

    # ---------------- إحصائيات عامة ----------------
    total_reports = len(reports)
    total_resolved = sum(1 for r in reports if 'تم حل' in r['classification'])
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
        resolved = sum(1 for r in agent_reports if 'تم حل' in r['classification'])
        unresolved = len(agent_reports) - resolved
        monthly.append({
            'agent_name': agent['agent_name'],
            'total': len(agent_reports),
            'resolved': resolved,
            'unresolved': unresolved,
        })

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
    }


import json

def get_visitor_data(request):
    if 'visitor_data' not in request.session:
        data = generate_visitor_data()
        # نحول الداتا لـ JSON ونحفظها في الـ session
        request.session['visitor_data'] = json.dumps(data, default=str)
        request.session.modified = True
    
    return json.loads(request.session['visitor_data'])