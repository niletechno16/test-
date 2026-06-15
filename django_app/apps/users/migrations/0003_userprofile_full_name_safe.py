from django.db import migrations, models


def add_full_name_if_missing(apps, schema_editor):
    """يضيف الـ column بـ raw SQL لو مش موجود — آمن تماماً"""
    db = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        if db == 'sqlite':
            cursor.execute("PRAGMA table_info(users_userprofile)")
            cols = [row[1] for row in cursor.fetchall()]
            if 'full_name' not in cols:
                cursor.execute(
                    "ALTER TABLE users_userprofile ADD COLUMN full_name VARCHAR(200) NOT NULL DEFAULT ''"
                )
        else:
            # SQL Server / PostgreSQL / MySQL
            try:
                cursor.execute("""
                    IF NOT EXISTS (
                        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'users_userprofile'
                          AND COLUMN_NAME = 'full_name'
                    )
                    ALTER TABLE users_userprofile ADD full_name NVARCHAR(200) NOT NULL DEFAULT ''
                """)
            except Exception:
                pass  # لو مش SQL Server جرب syntax تاني
            try:
                cursor.execute(
                    "ALTER TABLE users_userprofile ADD COLUMN IF NOT EXISTS full_name VARCHAR(200) NOT NULL DEFAULT ''"
                )
            except Exception:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_notification_conv_id'),
    ]

    operations = [
        migrations.RunPython(add_full_name_if_missing, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='userprofile',
                    name='full_name',
                    field=models.CharField(blank=True, default='', max_length=200),
                ),
            ],
            database_operations=[],  # الـ column اتضاف في RunPython فوق
        ),
    ]
