from fastapi_app.database.connection import get_connection
from fastapi_app.config.settings import TABLE_NAME, CUSTOMER_TABLE


def save_customer(customer_id, customer_name, customer_phone):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT 1 FROM {CUSTOMER_TABLE} WHERE customer_id = %d
            )
            BEGIN
                INSERT INTO {CUSTOMER_TABLE} (customer_id, customer_name, customer_phone)
                VALUES (%d, %s, %s)
            END
        """, (customer_id, customer_id, customer_name, customer_phone))
        conn.commit()
        conn.close()
        print(f"✅ Customer check done — id: {customer_id}")
    except Exception as e:
        print(f"❌ Customer save failed: {str(e)}")


def save_to_db(customer_id, customer_name, customer_phone, classification, agent_id, agent_name, conv_id, resolved_date, resolved_time, summary):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {TABLE_NAME}
                (customer_id, customer_name, customer_phone, classification, agent_id, agent_name, conv_id, resolved_date, resolved_time, summary)
            VALUES (%d, %s, %s, %s, %d, %s, %s, %d, %s, %s)
        """, (
            customer_id,
            customer_name,
            customer_phone,
            classification,
            agent_id,
            agent_name,
            str(conv_id),
            resolved_date,
            resolved_time,
            summary
        ))
        conn.commit()
        conn.close()
        print(f"✅ Record saved to DB — conv_id: {conv_id} | customer_id: {customer_id}")
    except Exception as e:
        print(f"❌ DB insert failed: {str(e)}")