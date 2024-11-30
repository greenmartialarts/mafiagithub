from django.core.management.base import BaseCommand
from myapp.db import initialize_database, test_connection

class Command(BaseCommand):
    help = 'Initialize database and test connection'

    def handle(self, *args, **options):
        self.stdout.write('Initializing database...')
        
        if initialize_database():
            self.stdout.write(self.style.SUCCESS('Database initialized successfully'))
        else:
            self.stdout.write(self.style.ERROR('Database initialization failed'))
            return
            
        if test_connection():
            self.stdout.write(self.style.SUCCESS('Database connection test successful'))
        else:
            self.stdout.write(self.style.ERROR('Database connection test failed')) 