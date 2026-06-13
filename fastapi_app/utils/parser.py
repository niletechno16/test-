def parse_ai_result(raw_text):
    prob_type = 0
    problem   = ""
    category  = ""
    summary   = ""
    try:
        for line in raw_text.splitlines():
            line = line.strip()
            if line.startswith("النوع:"):
                val = line.replace("النوع:", "").strip()
                prob_type = 1 if val == "1" else 0
            elif line.startswith("المشكلة:"):
                problem = line.replace("المشكلة:", "").strip()
            elif line.startswith("التصنيف:"):
                category = line.replace("التصنيف:", "").strip()
            elif line.startswith("الملخص:"):
                summary = line.replace("الملخص:", "").strip()
    except Exception:
        problem  = raw_text
        category = "غير محدد"
        summary  = raw_text

    if not problem:  problem  = raw_text
    if not category: category = "غير محدد"
    if not summary:  summary  = problem

    return prob_type, problem, category, summary
