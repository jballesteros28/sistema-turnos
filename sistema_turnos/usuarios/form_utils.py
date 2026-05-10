from clientes.models import Cliente
from negocio.models import Negocio
from profesional.models import Profesional
from servicio.models import Servicio
from sucursal.models import Sucursal

from .permissions import (
    filtrar_por_negocios,
    get_negocios_gestionables,
    get_negocios_operacion,
    get_negocios_permitidos,
    get_profesionales_permitidos_para_turnos,
)


def limitar_querysets_por_usuario(
    form,
    user,
    *,
    turnos=False,
    gestion_negocio=False,
    gestion_operacion=False,
):
    if not getattr(user, "is_authenticated", False):
        return

    negocios_base = get_negocios_permitidos(user)
    if gestion_negocio:
        negocios_base = get_negocios_gestionables(user)
    elif gestion_operacion:
        negocios_base = get_negocios_operacion(user)

    if "negocio" in form.fields:
        form.fields["negocio"].queryset = negocios_base.order_by("nombre")

    if "sucursal" in form.fields:
        form.fields["sucursal"].queryset = filtrar_por_negocios(
            Sucursal.objects.select_related("negocio"),
            negocios_base,
        ).order_by("negocio__nombre", "nombre")

    if "sucursales" in form.fields:
        form.fields["sucursales"].queryset = filtrar_por_negocios(
            Sucursal.objects.select_related("negocio"),
            negocios_base,
        ).order_by("negocio__nombre", "nombre")

    if "cliente" in form.fields:
        form.fields["cliente"].queryset = filtrar_por_negocios(
            Cliente.objects.select_related("negocio"),
            negocios_base,
        ).order_by("negocio__nombre", "apellido", "nombre")

    if "profesional" in form.fields:
        if turnos and not gestion_operacion and not gestion_negocio:
            profesionales = get_profesionales_permitidos_para_turnos(user)
        else:
            profesionales = filtrar_por_negocios(
                Profesional.objects.select_related("negocio"),
                negocios_base,
            )
        form.fields["profesional"].queryset = profesionales.order_by(
            "negocio__nombre",
            "apellido",
            "nombre",
        )

    if "servicio" in form.fields:
        form.fields["servicio"].queryset = filtrar_por_negocios(
            Servicio.objects.select_related("negocio"),
            negocios_base,
        ).order_by("negocio__nombre", "nombre")

    if "servicios" in form.fields:
        form.fields["servicios"].queryset = filtrar_por_negocios(
            Servicio.objects.select_related("negocio"),
            negocios_base,
        ).order_by("negocio__nombre", "nombre")
