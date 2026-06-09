def parse_ai_result(raw_text):
    summary = ""
    classification = ""
    try:
        for line in raw_text.splitlines():
            line = line.strip()
            if line.startswith("الخلاصة:"):
                summary = line.replace("الخلاصة:", "").strip()
            elif line.startswith("التصنيف:"):
                classification = line.replace("التصنيف:", "").strip()
            elif line.startswith("الملخص:"):
                summary = line.replace("الملخص:", "").strip()
    except Exception:
        summary = raw_text
        classification = "غير محدد"

    if not summary:
        summary = raw_text
    if not classification:
        classification = "غير محدد"

    return summary, classification