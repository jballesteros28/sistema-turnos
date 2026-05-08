from .models import RolMiembroNegocio
from .permissions import es_superadmin, get_membresias_usuario


def membresia_usuario(request):
    user = request.user
    if not user.is_authenticated:
        return {}

    if user.is_superuser:
        return {
            "rol_actual_usuario": "superuser",
            "usuario_sin_membresias": False,
        }

    membresias = list(get_membresias_usuario(user))
    if not membresias:
        return {
            "rol_actual_usuario": "",
            "usuario_sin_membresias": True,
        }

    if es_superadmin(user):
        rol = "superadmin"
    elif len(membresias) == 1:
        rol = membresias[0].get_rol_display()
    else:
        roles = {
            RolMiembroNegocio.ADMIN_NEGOCIO: "admin",
            RolMiembroNegocio.RECEPCIONISTA: "recepcion",
            RolMiembroNegocio.PROFESIONAL: "profesional",
        }
        rol = ", ".join(sorted({roles.get(m.rol, m.rol) for m in membresias}))

    return {
        "rol_actual_usuario": rol,
        "usuario_sin_membresias": False,
    }
