from django.db.models import Q

from negocio.models import Negocio

from .models import MiembroNegocio, RolMiembroNegocio


ROLES_GESTION_NEGOCIO = (
    RolMiembroNegocio.ADMIN_NEGOCIO,
)
ROLES_VER_NEGOCIO = (
    RolMiembroNegocio.ADMIN_NEGOCIO,
    RolMiembroNegocio.RECEPCIONISTA,
)
ROLES_GESTION_OPERATIVA = (
    RolMiembroNegocio.ADMIN_NEGOCIO,
    RolMiembroNegocio.RECEPCIONISTA,
)
ROLES_VER_TURNOS = (
    RolMiembroNegocio.ADMIN_NEGOCIO,
    RolMiembroNegocio.RECEPCIONISTA,
    RolMiembroNegocio.PROFESIONAL,
)


def get_membresias_usuario(user):
    if not getattr(user, "is_authenticated", False):
        return MiembroNegocio.objects.none()

    return MiembroNegocio.objects.filter(
        user=user,
        activo=True,
    ).select_related("user", "negocio", "profesional")


def es_superadmin(user):
    if not getattr(user, "is_authenticated", False):
        return False

    return user.is_superuser or get_membresias_usuario(user).filter(
        rol=RolMiembroNegocio.SUPERADMIN,
    ).exists()


def get_negocios_permitidos(user):
    if not getattr(user, "is_authenticated", False):
        return Negocio.objects.none()

    if es_superadmin(user):
        return Negocio.objects.all()

    return Negocio.objects.filter(
        miembros__user=user,
        miembros__activo=True,
    ).distinct()


def get_negocios_por_roles(user, roles):
    if not getattr(user, "is_authenticated", False):
        return Negocio.objects.none()

    if es_superadmin(user):
        return Negocio.objects.all()

    return Negocio.objects.filter(
        miembros__user=user,
        miembros__activo=True,
        miembros__rol__in=roles,
    ).distinct()


def get_negocios_visibles(user):
    return get_negocios_por_roles(user, ROLES_VER_NEGOCIO)


def get_negocios_gestionables(user):
    return get_negocios_por_roles(user, ROLES_GESTION_NEGOCIO)


def get_negocios_operacion(user):
    return get_negocios_por_roles(user, ROLES_GESTION_OPERATIVA)


def usuario_tiene_roles(user, roles):
    if not getattr(user, "is_authenticated", False):
        return False

    return es_superadmin(user) or get_membresias_usuario(user).filter(
        rol__in=roles,
    ).exists()


def usuario_tiene_roles_en_negocio(user, negocio, roles):
    if not negocio or not getattr(user, "is_authenticated", False):
        return False

    if es_superadmin(user):
        return True

    return get_membresias_usuario(user).filter(
        negocio=negocio,
        rol__in=roles,
    ).exists()


def usuario_puede_ver_negocio(user, negocio):
    return usuario_tiene_roles_en_negocio(user, negocio, ROLES_VER_NEGOCIO)


def usuario_puede_gestionar_negocio(user, negocio):
    return usuario_tiene_roles_en_negocio(user, negocio, ROLES_GESTION_NEGOCIO)


def usuario_puede_gestionar_operacion(user, negocio):
    return usuario_tiene_roles_en_negocio(user, negocio, ROLES_GESTION_OPERATIVA)


def usuario_puede_gestionar_algun_negocio(user):
    return usuario_tiene_roles(user, ROLES_GESTION_NEGOCIO)


def usuario_puede_gestionar_alguna_operacion(user):
    return usuario_tiene_roles(user, ROLES_GESTION_OPERATIVA)


def usuario_puede_ver_turnos(user):
    return usuario_tiene_roles(user, ROLES_VER_TURNOS)


def usuario_es_profesional(user, negocio):
    if not negocio or not getattr(user, "is_authenticated", False):
        return False

    return get_membresias_usuario(user).filter(
        negocio=negocio,
        rol=RolMiembroNegocio.PROFESIONAL,
    ).exists()


def get_profesional_para_negocio(user, negocio):
    if not negocio or not getattr(user, "is_authenticated", False):
        return None

    membresia = get_membresias_usuario(user).filter(
        negocio=negocio,
        rol=RolMiembroNegocio.PROFESIONAL,
        profesional__isnull=False,
    ).first()
    return membresia.profesional if membresia else None


def filtrar_por_negocios_permitidos(queryset, user, negocio_lookup="negocio"):
    if not getattr(user, "is_authenticated", False):
        return queryset.none()

    if es_superadmin(user):
        return queryset

    filtro = {f"{negocio_lookup}__in": get_negocios_permitidos(user)}
    return queryset.filter(**filtro)


def filtrar_por_negocios(queryset, negocios, negocio_lookup="negocio"):
    filtro = {f"{negocio_lookup}__in": negocios}
    return queryset.filter(**filtro)


def filtrar_por_negocios_visibles(queryset, user, negocio_lookup="negocio"):
    return filtrar_por_negocios(
        queryset,
        get_negocios_visibles(user),
        negocio_lookup=negocio_lookup,
    )


def filtrar_por_negocios_gestionables(queryset, user, negocio_lookup="negocio"):
    return filtrar_por_negocios(
        queryset,
        get_negocios_gestionables(user),
        negocio_lookup=negocio_lookup,
    )


def filtrar_por_negocios_operacion(queryset, user, negocio_lookup="negocio"):
    return filtrar_por_negocios(
        queryset,
        get_negocios_operacion(user),
        negocio_lookup=negocio_lookup,
    )


def filtrar_turnos_por_usuario(queryset, user):
    if not getattr(user, "is_authenticated", False):
        return queryset.none()

    if es_superadmin(user):
        return queryset

    membresias = get_membresias_usuario(user)
    negocios_operativos = membresias.filter(
        rol__in=ROLES_GESTION_OPERATIVA,
    ).values("negocio_id")
    profesionales_propios = membresias.filter(
        rol=RolMiembroNegocio.PROFESIONAL,
        profesional__isnull=False,
    ).values("profesional_id")

    return queryset.filter(
        Q(negocio_id__in=negocios_operativos)
        | Q(profesional_id__in=profesionales_propios)
    ).distinct()


def get_profesionales_permitidos_para_turnos(user):
    from profesional.models import Profesional

    queryset = Profesional.objects.select_related("negocio")
    if not getattr(user, "is_authenticated", False):
        return queryset.none()

    if es_superadmin(user):
        return queryset

    membresias = get_membresias_usuario(user)
    negocios_operativos = membresias.filter(
        rol__in=ROLES_GESTION_OPERATIVA,
    ).values("negocio_id")
    profesionales_propios = membresias.filter(
        rol=RolMiembroNegocio.PROFESIONAL,
        profesional__isnull=False,
    ).values("profesional_id")

    return queryset.filter(
        Q(negocio_id__in=negocios_operativos)
        | Q(id__in=profesionales_propios)
    ).distinct()


def get_profesionales_visibles(user):
    from profesional.models import Profesional

    queryset = Profesional.objects.select_related("negocio")
    if not getattr(user, "is_authenticated", False):
        return queryset.none()

    if es_superadmin(user):
        return queryset

    membresias = get_membresias_usuario(user)
    negocios_operativos = membresias.filter(
        rol__in=ROLES_GESTION_OPERATIVA,
    ).values("negocio_id")
    profesionales_propios = membresias.filter(
        rol=RolMiembroNegocio.PROFESIONAL,
        profesional__isnull=False,
    ).values("profesional_id")

    return queryset.filter(
        Q(negocio_id__in=negocios_operativos)
        | Q(id__in=profesionales_propios)
    ).distinct()


def usuario_tiene_membresias(user):
    if not getattr(user, "is_authenticated", False):
        return False
    return es_superadmin(user) or get_membresias_usuario(user).exists()


def get_permisos_ui(user):
    permisos = {
        "puede_ver_admin_django": False,
        "puede_ver_negocios": False,
        "puede_crear_negocios": False,
        "puede_gestionar_negocios": False,
        "puede_ver_catalogos": False,
        "puede_ver_clientes": False,
        "puede_gestionar_operacion": False,
        "puede_ver_disponibilidades": False,
        "puede_ver_excepciones": False,
        "puede_ver_turnos": False,
        "puede_crear_turnos": False,
        "puede_ver_agenda": False,
        "puede_ver_configuracion": False,
        "puede_gestionar_configuracion": False,
    }
    if not getattr(user, "is_authenticated", False):
        return permisos

    puede_gestionar_negocios = usuario_puede_gestionar_algun_negocio(user)
    puede_gestionar_operacion = usuario_puede_gestionar_alguna_operacion(user)
    puede_ver_negocios = usuario_tiene_roles(user, ROLES_VER_NEGOCIO)
    puede_ver_turnos = usuario_puede_ver_turnos(user)

    permisos.update(
        {
            "puede_ver_admin_django": user.is_staff,
            "puede_ver_negocios": puede_ver_negocios,
            "puede_crear_negocios": es_superadmin(user),
            "puede_gestionar_negocios": puede_gestionar_negocios,
            "puede_ver_catalogos": puede_gestionar_operacion,
            "puede_ver_clientes": puede_gestionar_operacion,
            "puede_gestionar_operacion": puede_gestionar_operacion,
            "puede_ver_disponibilidades": puede_gestionar_operacion,
            "puede_ver_excepciones": puede_gestionar_operacion,
            "puede_ver_turnos": puede_ver_turnos,
            "puede_crear_turnos": puede_gestionar_operacion,
            "puede_ver_agenda": puede_ver_turnos,
            "puede_ver_configuracion": puede_gestionar_negocios,
            "puede_gestionar_configuracion": puede_gestionar_negocios,
        }
    )
    return permisos
