import requests
from fastapi import APIRouter, Request
from datetime import datetime, timezone, timedelta
from fastapi_app.config.settings import CHATWOOT_URL, ACCOUNT_ID, ACCESS_TOKEN
from fastapi_app.ai.analyzer import analyze_chat
from fastapi_app.utils.parser import parse_ai_result
from fastapi_app.database.operations import save_customer, save_to_db

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "alive"}


@router.post("/webhook")
async def chatwoot_webhook(request: Request):

    payload = await request.json()
    status = payload.get("status")

    if status == "resolved":

        conv_id        = payload.get("id")
        customer_id    = payload.get("meta", {}).get("sender", {}).get("id")
        customer_name  = payload.get("meta", {}).get("sender", {}).get("name", "Unknown")
        customer_phone = payload.get("meta", {}).get("sender", {}).get("phone_number", "No Phone")
        agent_id       = payload.get("meta", {}).get("assignee", {}).get("id")
        agent_name     = payload.get("meta", {}).get("assignee", {}).get("name", "Unassigned")

        cairo_tz = timezone(timedelta(hours=3))

        resolved_at_raw = payload.get("resolved_at") or payload.get("updated_at")
        if resolved_at_raw:
            try:
                resolved_dt = datetime.fromtimestamp(int(resolved_at_raw), tz=cairo_tz)
            except Exception:
                try:
                    resolved_dt = datetime.fromisoformat(str(resolved_at_raw).replace("Z", "+00:00")).astimezone(cairo_tz)
                except Exception:
                    resolved_dt = datetime.now(cairo_tz)
        else:
            resolved_dt = datetime.now(cairo_tz)

        resolved_date = int(resolved_dt.strftime("%Y%m%d"))
        resolved_time = resolved_dt.strftime("%I:%M %p")

        print("\n" + "="*50)
        print(f"🎯 STATUS: RESOLVED")
        print(f"🪪 Customer ID: {customer_id}")
        print(f"{'👤 Customer'} : {customer_name}")
        print(f"{ '📞 Phone'}    : {customer_phone}")
        print(f"🪪 Agent ID  : {agent_id}")
        print(f"{'👨‍💻 Agent'}    : {agent_name}")
        print(f"🆔 Conv ID   : {conv_id}")
        print(f"📅 Date      : {resolved_date}")
        print(f"🕐 Time      : {resolved_time}")

        api_url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conv_id}/messages"

        headers = {
            "api_access_token": ACCESS_TOKEN,
            "api-access-token": ACCESS_TOKEN,
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                messages_list = data.get('payload') if isinstance(data, dict) else data

                full_chat_text = ""

                if messages_list:
                    for msg in reversed(messages_list):
                        content = msg.get("content")
                        sender  = msg.get("sender")
                        s_name  = sender.get("name") if sender else "System"

                        if content:
                            full_chat_text += f"[{s_name}]: {content}\n"

                    ai_raw = analyze_chat(full_chat_text)
                    summary, classification = parse_ai_result(ai_raw)

                    print(f"📋 الخلاصة    : {summary}")
                    print(f"🏷️  التصنيف    : {classification}")
                    print("="*50 + "\n")

                    save_customer(
                        customer_id=customer_id,
                        customer_name=customer_name,
                        customer_phone=customer_phone
                    )

                    save_to_db(
                        customer_id=customer_id,
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        classification=classification,
                        agent_id=agent_id,
                        agent_name=agent_name,
                        conv_id=conv_id,
                        resolved_date=resolved_date,
                        resolved_time=resolved_time,
                        summary=summary
                    )

            else:
                print(f"❌ Chatwoot API Error: {response.status_code}")

        except Exception as e:
            print("⚠️ Error:", str(e))

    return {"status": "success"}