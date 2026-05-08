# Sistema de Turnos

MVP en Django para administrar turnos de negocios con sucursales, servicios,
profesionales, clientes, disponibilidad horaria, excepciones de agenda y agenda
diaria.

## Apps principales

- `core`: dashboard operativo.
- `negocio`: datos base del negocio.
- `sucursal`: sedes del negocio y aceptacion de turnos.
- `servicio`: servicios, duracion, precio y estado.
- `profesional`: profesionales, sucursales asociadas y servicios prestados.
- `clientes`: clientes del negocio.
- `disponibilidad`: franjas horarias disponibles por sucursal y profesional.
- `excepcion`: bloqueos o cierres de agenda por negocio, sucursal o profesional.
- `turnos`: creacion, validacion y cambio de estado de turnos.
- `agenda`: vista diaria filtrable de turnos.
- `configuracion_negocio`: parametros operativos del negocio.
- `usuarios`: membresias entre usuarios Django, negocios y roles de acceso.

## Flujo operativo

1. Ingresar en `/accounts/login/`.
2. Crear un negocio con un superusuario o superadmin.
3. Crear sus sucursales.
4. Crear servicios.
5. Crear profesionales y asociarlos a sucursales y servicios.
6. Crear clientes.
7. Cargar disponibilidad.
8. Cargar excepciones cuando corresponda.
9. Ajustar la configuracion operativa del negocio.
10. Crear y operar turnos.
11. Consultar la agenda diaria.

## Autenticacion y multinegocio

El sistema usa autenticacion estandar de Django con sesiones:

- Login: `/accounts/login/`
- Logout: `/accounts/logout/`
- Redireccion post-login: `/dashboard/`
- Redireccion post-logout: `/accounts/login/`

Los usuarios anonimos no pueden ingresar a las vistas internas. Cada usuario
logueado ve datos de los negocios vinculados mediante `MiembroNegocio`. Un
usuario sin membresias no ve datos operativos y recibe el aviso correspondiente.

### Crear superusuario

Desde la carpeta del proyecto Django:

```bash
cd sistema_turnos
python manage.py createsuperuser
```

### Crear usuarios y membresias

Los usuarios se crean con el modelo estandar `auth.User`, desde el admin de
Django o shell. Luego se asignan a negocios con `MiembroNegocio`.

Ejemplo desde shell:

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from negocio.models import Negocio
from usuarios.models import MiembroNegocio, RolMiembroNegocio

user = User.objects.create_user("recepcion", password="cambiar-esta-clave")
negocio = Negocio.objects.get(nombre="Mi negocio")
MiembroNegocio.objects.create(
    user=user,
    negocio=negocio,
    rol=RolMiembroNegocio.RECEPCIONISTA,
)
```

Para usuarios con rol `profesional`, asociar tambien el campo `profesional`.

### Roles disponibles

- `superuser` de Django: ve todo.
- `superadmin`: ve todo dentro del sistema.
- `admin_negocio`: gestiona todo dentro de su negocio.
- `recepcionista`: gestiona clientes, turnos y agenda; ve catalogos del negocio.
- `profesional`: ve solo sus turnos y agenda si tiene un profesional asociado.

## Rutas principales

- `/dashboard/`
- `/negocios/`
- `/sucursales/`
- `/clientes/`
- `/servicios/`
- `/profesionales/`
- `/agenda/disponibilidades/`
- `/agenda/excepciones/`
- `/turnos/`
- `/agenda/turnos/`
- `/configuracion/`

## Comandos utiles

Desde la carpeta del proyecto Django:

```bash
cd sistema_turnos
python manage.py runserver
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

## Notas

- `db.sqlite3` contiene datos locales de prueba y no debe usarse como base de
  produccion.
- `db.sqlite3` no debe borrarse durante el desarrollo de este MVP.
- Los listados, dashboard, agenda, turnos y formularios filtran por negocios
  permitidos; los accesos directos a objetos fuera del alcance responden 404.
- En produccion configurar `SECRET_KEY` por variable de entorno.
- La generacion actual de slugs es simple; antes de produccion debe robustecerse
  para garantizar unicidad por negocio donde aplique.
- `ConfiguracionNegocio` gobierna anticipacion de reserva, confirmacion inicial,
  buffer entre turnos, permisos de turnos pasados y reglas de cancelacion.
