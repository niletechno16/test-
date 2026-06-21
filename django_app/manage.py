import os
import sys
import django
from django.core.management import call_command, execute_from_command_line

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

# كود Pella - بيتشغل لما uvicorn يلود الملف
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
call_command('collectstatic', '--noinput', verbosity=0)

from config.asgi import application