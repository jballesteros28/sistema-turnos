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

        try:
            enviados = send_mail(
                subject=asunto,
                message=cuerpo,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f"No se pudo enviar el email de prueba: {exc}") from exc

        if not enviados:
            raise CommandError("El backend de email no envio el mensaje de prueba.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Email de prueba enviado correctamente a {destinatario}."
            )
        )
