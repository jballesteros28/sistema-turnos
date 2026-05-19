import os
from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from clientes.models import Cliente
from configuracion_negocio.models import ConfiguracionNegocio
from disponibilidad.models import Disponibilidad
from negocio.models import Negocio, TipoNegocio
from profesional.models import Profesional, TipoProfesional
from servicio.models import Servicio
from sucursal.models import Sucursal
from usuarios.models import MiembroNegocio, RolMiembroNegocio


DEMO_PASSWORD = "Admin12345!"
DEMO_NEGOCIO = "Negocio Demo"
DIAS_DEMO = [0, 1, 2, 3, 4]


class Command(BaseCommand):
    help = "Crea usuarios y datos minimos de demo para desarrollo local."

    def add_arguments(self, parser):
        parser.add_argument(
            "--render-safe",
            action="store_true",
            help=(
                "Modo idempotente para deploy. Solo crea datos demo si "
                "CREATE_DEMO_USERS=True."
            ),
        )

    def handle(self, *args, **options):
        render_safe = options["render_safe"]
        if render_safe and not _env_bool("CREATE_DEMO_USERS", False):
            self.stdout.write(
                self.style.WARNING(
                    "Usuarios demo no creados: CREATE_DEMO_USERS no esta en True."
                )
            )
            return

        negocio = self._ensure_negocio()
        sucursal = self._ensure_sucursal(negocio)
        servicio = self._ensure_servicio(negocio)
        profesional = self._ensure_profesional(negocio, sucursal, servicio)
        cliente = self._ensure_cliente(negocio)
        disponibilidad = self._ensure_disponibilidad(negocio, sucursal, profesional)
        configuracion = self._ensure_configuracion(negocio)

        usuarios = {
            "superuser": self._ensure_user(
                "superuser",
                "superuser@example.local",
                is_superuser=True,
            ),
            "superadmin": self._ensure_user(
                "superadmin",
                "superadmin@example.local",
            ),
            "admin_negocio": self._ensure_user(
                "admin_negocio",
                "admin_negocio@example.local",
            ),
            "recepcionista": self._ensure_user(
                "recepcionista",
                "recepcionista@example.local",
            ),
            "profesional": self._ensure_user(
                "profesional",
                "profesional@example.local",
            ),
            "sin_membresia": self._ensure_user(
                "sin_membresia",
                "sin_membresia@example.local",
            ),
        }

        self._ensure_miembro(
            usuarios["superadmin"],
            negocio,
            RolMiembroNegocio.SUPERADMIN,
        )
        self._ensure_miembro(
            usuarios["admin_negocio"],
            negocio,
            RolMiembroNegocio.ADMIN_NEGOCIO,
        )
        self._ensure_miembro(
            usuarios["recepcionista"],
            negocio,
            RolMiembroNegocio.RECEPCIONISTA,
        )
        self._ensure_miembro(
            usuarios["profesional"],
            negocio,
            RolMiembroNegocio.PROFESIONAL,
            profesional=profesional,
        )

        self.stdout.write(self.style.SUCCESS("Usuarios demo listos."))
        self.stdout.write(f"Negocio: {negocio.nombre}")
        self.stdout.write(f"Sucursal: {sucursal.nombre}")
        self.stdout.write(f"Servicio: {servicio.nombre}")
        self.stdout.write(f"Profesional: {profesional.nombre_visible}")
        self.stdout.write(f"Cliente: {cliente.nombre_visible}")
        self.stdout.write(f"Disponibilidad: {disponibilidad}")
        self.stdout.write(f"Configuracion: {configuracion}")
        if not render_safe:
            self.stdout.write("Password demo: documentada en README.")

    def _ensure_user(self, username, email, *, is_superuser=False):
        User = get_user_model()
        user, _created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        user.email = email
        user.is_active = True
        if is_superuser:
            user.is_staff = True
            user.is_superuser = True
        user.set_password(DEMO_PASSWORD)
        user.save()
        return user

    def _ensure_negocio(self):
        negocio, _created = Negocio.objects.get_or_create(
            nombre=DEMO_NEGOCIO,
            defaults={
                "slug": "negocio-demo",
                "tipo_negocio": TipoNegocio.OTRO,
                "email_principal": "demo@example.local",
                "telefono_principal": "1111111111",
                "ciudad": "Cordoba",
                "pais": "Argentina",
                "direccion_principal": "Av. Demo 123",
            },
        )
        return negocio

    def _ensure_sucursal(self, negocio):
        sucursal, _created = Sucursal.objects.get_or_create(
            negocio=negocio,
            slug="sucursal-demo",
            defaults={
                "nombre": "Sucursal Demo",
                "direccion": "Av. Demo 123",
                "ciudad": "Cordoba",
                "pais": "Argentina",
                "es_principal": True,
                "acepta_turnos": True,
            },
        )
        if not sucursal.acepta_turnos:
            sucursal.acepta_turnos = True
            sucursal.save(update_fields=["acepta_turnos", "actualizado_en"])
        return sucursal

    def _ensure_servicio(self, negocio):
        servicio, _created = Servicio.objects.get_or_create(
            negocio=negocio,
            slug="servicio-demo",
            defaults={
                "nombre": "Servicio Demo",
                "duracion_minutos": 60,
                "precio": 1000,
            },
        )
        return servicio

    def _ensure_profesional(self, negocio, sucursal, servicio):
        profesional, _created = Profesional.objects.get_or_create(
            negocio=negocio,
            slug="profesional-demo",
            defaults={
                "nombre": "Profesional",
                "apellido": "Demo",
                "nombre_visible": "Profesional Demo",
                "tipo_profesional": TipoProfesional.PROFESIONAL,
                "email": "profesional@example.local",
                "acepta_turnos": True,
            },
        )
        if not profesional.acepta_turnos:
            profesional.acepta_turnos = True
            profesional.save(update_fields=["acepta_turnos", "actualizado_en"])
        profesional.sucursales.add(sucursal)
        profesional.servicios.add(servicio)
        return profesional

    def _ensure_cliente(self, negocio):
        cliente, _created = Cliente.objects.get_or_create(
            negocio=negocio,
            slug="cliente-demo",
            defaults={
                "nombre": "Cliente",
                "apellido": "Demo",
                "nombre_visible": "Cliente Demo",
                "telefono": "2222222222",
                "email": "cliente@example.local",
            },
        )
        return cliente

    def _ensure_disponibilidad(self, negocio, sucursal, profesional):
        disponibilidad = (
            Disponibilidad.objects.filter(
                negocio=negocio,
                sucursal=sucursal,
                profesional=profesional,
                hora_inicio=time(9, 0),
                hora_fin=time(18, 0),
            )
            .order_by("pk")
            .first()
        )

        if disponibilidad is None:
            return Disponibilidad.objects.create(
                negocio=negocio,
                sucursal=sucursal,
                profesional=profesional,
                dia_semana=0,
                dias_semana=DIAS_DEMO,
                hora_inicio=time(9, 0),
                hora_fin=time(18, 0),
                activo=True,
            )

        update_fields = []
        if disponibilidad.dias_semana_normalizados() != DIAS_DEMO:
            disponibilidad.dias_semana = DIAS_DEMO
            disponibilidad.dia_semana = DIAS_DEMO[0]
            update_fields.extend(["dias_semana", "dia_semana"])
        if not disponibilidad.activo:
            disponibilidad.activo = True
            update_fields.append("activo")
        if update_fields:
            update_fields.append("actualizado_en")
            disponibilidad.save(update_fields=update_fields)
        return disponibilidad

    def _ensure_configuracion(self, negocio):
        configuracion, _created = ConfiguracionNegocio.objects.get_or_create(
            negocio=negocio,
        )
        return configuracion

    def _ensure_miembro(self, user, negocio, rol, *, profesional=None):
        miembro, _created = MiembroNegocio.objects.update_or_create(
            user=user,
            negocio=negocio,
            defaults={
                "rol": rol,
                "profesional": profesional,
                "activo": True,
            },
        )
        return miembro


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in ("1", "true", "yes", "y", "on"):
        return True
    if normalized in ("0", "false", "no", "n", "off"):
        return False
    return default
