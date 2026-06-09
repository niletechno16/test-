from fastapi_app.database.connection import get_connection
from fastapi_app.config.settings import TABLE_NAME, CUSTOMER_TABLE


def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = '{TABLE_NAME}'
            )
            BEGIN
                CREATE TABLE {TABLE_NAME} (
                    id               INT IDENTITY(1,1) PRIMARY KEY,
                    customer_id      INT,
                    customer_name    NVARCHAR(255),
                    customer_phone   NVARCHAR(50),
                    classification   NVARCHAR(500),
                    agent_id         INT,
                    agent_name       NVARCHAR(255),
                    conv_id          NVARCHAR(50),
                    resolved_date    BIGINT,
                    resolved_time    NVARCHAR(20),
                    summary          NVARCHAR(MAX),
                    created_at       DATETIME DEFAULT GETDATE()
                )
            END
        """)

        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = '{CUSTOMER_TABLE}'
            )
            BEGIN
                CREATE TABLE {CUSTOMER_TABLE} (
                    customer_id    INT PRIMARY KEY,
                    customer_name  NVARCHAR(255),
                    customer_phone NVARCHAR(50)
                )
            END
        """)

        conn.commit()
        conn.close()
        print(f"✅ DB ready — tables '{TABLE_NAME}' & '{CUSTOMER_TABLE}' exist or just created")
    except Exception as e:
        print(f"❌ DB init failed: {str(e)}")