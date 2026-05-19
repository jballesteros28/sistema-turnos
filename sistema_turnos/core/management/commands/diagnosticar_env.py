from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Muestra un diagnostico seguro de variables de entorno cargadas."

    def handle(self, *args, **options):
        password = settings.EMAIL_HOST_PASSWORD or ""

        self.stdout.write(f"BASE_DIR: {settings.BASE_DIR}")
        self.stdout.write("Rutas buscadas para .env:")
        for env_path in settings.ENV_PATHS:
            self.stdout.write(f"- {env_path}")

        if settings.ENV_FILE:
            self.stdout.write(f".env encontrado: {settings.ENV_FILE}")
        else:
            self.stdout.write(self.style.WARNING(".env encontrado: No"))

        self.stdout.write(
            f"EMAIL_BACKEND: {_format_loaded(settings.EMAIL_BACKEND)}"
        )
        self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(
            f"EMAIL_PORT: {settings.EMAIL_PORT} ({type(settings.EMAIL_PORT).__name__})"
        )
        self.stdout.write(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(
            f"EMAIL_HOST_PASSWORD: {_format_password(password)}"
        )
        self.stdout.write(
            f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS} "
            f"({type(settings.EMAIL_USE_TLS).__name__})"
        )
        self.stdout.write(
            f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL} "
            f"({type(settings.EMAIL_USE_SSL).__name__})"
        )
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(
            f"DJANGO_DEBUG: {settings.DEBUG} ({type(settings.DEBUG).__name__})"
        )
        self.stdout.write(f"DJANGO_ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        self.stdout.write(f"DATABASE_ENGINE: {settings.DATABASE_ENGINE}")


def _format_loaded(value):
    if value:
        return f"{value} (cargado)"
    return "no cargado"


def _format_password(password):
    if password:
        return f"cargada ({len(password)} caracteres)"
    return "no cargada"
