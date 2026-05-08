from django.db.models import Q

from negocio.models import Negocio

from .models import MiembroNegocio, RolMiembroNegocio


ROLES_GESTION_NEGOCIO = (
    RolMiembroNegocio.ADMIN_NEGOCIO,
)
ROLES_GESTION_OPERATIVA = (
    RolMiembroNegocio.ADMIN_NEGOCIO,
    RolMiembroNegocio.RECEPCIONISTA,
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


def usuario_puede_ver_negocio(user, negocio):
    if not negocio or not getattr(user, "is_authenticated", False):
        return False

    if es_superadmin(user):
        return True

    return get_membresias_usuario(user).filter(negocio=negocio).exists()


def usuario_puede_gestionar_negocio(user, negocio):
    if not negocio or not getattr(user, "is_authenticated", False):
        return False

    if es_superadmin(user):
        return True

    return get_membresias_usuario(user).filter(
        negocio=negocio,
        rol__in=ROLES_GESTION_NEGOCIO,
    ).exists()


def usuario_puede_gestionar_operacion(user, negocio):
    if not negocio or not getattr(user, "is_authenticated", False):
        return False

    if es_superadmin(user):
        return True

    return get_membresias_usuario(user).filter(
        negocio=negocio,
        rol__in=ROLES_GESTION_OPERATIVA,
    ).exists()


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


def usuario_tiene_membresias(user):
    if not getattr(user, "is_authenticated", False):
        return False
    return es_superadmin(user) or get_membresias_usuario(user).exists()
