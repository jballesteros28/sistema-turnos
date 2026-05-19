import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea un superusuario desde variables de entorno para deploy."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")

        if not username or not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Superuser Render no creado: faltan variables "
                    "DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL o "
                    "DJANGO_SUPERUSER_PASSWORD."
                )
            )
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser Render '{username}' ya existe. Sin cambios."
                )
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Superuser Render '{username}' creado.")
        )
