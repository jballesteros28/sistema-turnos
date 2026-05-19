from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Envia un email simple para probar la configuracion actual."

    def add_arguments(self, parser):
        parser.add_argument("destinatario", help="Email de destino para la prueba.")

    def handle(self, *args, **options):
        destinatario = options["destinatario"]
        asunto = "Prueba de email - Sistema de Turnos"
        cuerpo = (
            "Este es un correo de prueba enviado desde la configuracion actual "
            "del sistema."
        )
        password = settings.EMAIL_HOST_PASSWORD or ""

        self.stdout.write(f"Backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"Host: {settings.EMAIL_HOST}")
        self.stdout.write(f"Port: {settings.EMAIL_PORT}")
        self.stdout.write(f"User: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"SSL: {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"From: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"Password: {_format_password(password)}")

        if _is_smtp_backend(settings.EMAIL_BACKEND) and not password:
            raise CommandError(
                "EMAIL_HOST_PASSWORD no esta cargada. "
                "Revisa .env y diagnosticar_env."
            )

        try:
            enviados = send_mail(
                subject=asunto,
                message=cuerpo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(
                "No se pudo enviar el email de prueba "
                f"({exc.__class__.__name__}: {exc})"
            ) from exc

        if not enviados:
            raise CommandError("El backend de email no envio el mensaje de prueba.")

        self.stdout.write(
            self.style.SUCCESS(
                f"SUCCESS: Email de prueba enviado correctamente a {destinatario}."
            )
        )


def _is_smtp_backend(backend):
    return backend == "django.core.mail.backends.smtp.EmailBackend"


def _format_password(password):
    if password:
        return f"cargada ({len(password)} caracteres)"
    return "no cargada"
