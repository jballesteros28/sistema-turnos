from clientes.models import Cliente
from negocio.models import Negocio
from profesional.models import Profesional
from servicio.models import Servicio
from sucursal.models import Sucursal

from .permissions import (
    filtrar_por_negocios_permitidos,
    get_negocios_permitidos,
    get_profesionales_permitidos_para_turnos,
)


def limitar_querysets_por_usuario(form, user, *, turnos=False):
    if not getattr(user, "is_authenticated", False):
        return

    if "negocio" in form.fields:
        form.fields["negocio"].queryset = get_negocios_permitidos(user).order_by("nombre")

    if "sucursal" in form.fields:
        form.fields["sucursal"].queryset = filtrar_por_negocios_permitidos(
            Sucursal.objects.select_related("negocio"),
            user,
        ).order_by("negocio__nombre", "nombre")

    if "sucursales" in form.fields:
        form.fields["sucursales"].queryset = filtrar_por_negocios_permitidos(
            Sucursal.objects.select_related("negocio"),
            user,
        ).order_by("negocio__nombre", "nombre")

    if "cliente" in form.fields:
        form.fields["cliente"].queryset = filtrar_por_negocios_permitidos(
            Cliente.objects.select_related("negocio"),
            user,
        ).order_by("negocio__nombre", "apellido", "nombre")

    if "profesional" in form.fields:
        if turnos:
            profesionales = get_profesionales_permitidos_para_turnos(user)
        else:
            profesionales = filtrar_por_negocios_permitidos(
                Profesional.objects.select_related("negocio"),
                user,
            )
        form.fields["profesional"].queryset = profesionales.order_by(
            "negocio__nombre",
            "apellido",
            "nombre",
        )

    if "servicio" in form.fields:
        form.fields["servicio"].queryset = filtrar_por_negocios_permitidos(
            Servicio.objects.select_related("negocio"),
            user,
        ).order_by("negocio__nombre", "nombre")

    if "servicios" in form.fields:
        form.fields["servicios"].queryset = filtrar_por_negocios_permitidos(
            Servicio.objects.select_related("negocio"),
            user,
        ).order_by("negocio__nombre", "nombre")
