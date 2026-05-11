# Sistema de Turnos

MVP en Django para administrar turnos de negocios con sucursales, servicios,
profesionales, clientes, disponibilidad horaria, excepciones de agenda y agenda
diaria/semanal.

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
- `agenda`: vista diaria y semanal filtrable de turnos.
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
11. Consultar la agenda diaria o semanal.

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

### Usuarios demo para desarrollo local

Para crear o actualizar usuarios de prueba y datos minimos de demo:

```bash
python manage.py crear_usuarios_demo
```

El comando es idempotente: crea lo faltante y reutiliza los registros demo si ya
existen. Asegura al menos un negocio, sucursal, servicio, profesional, cliente,
disponibilidad, configuracion de negocio, usuarios y membresias.

Credenciales solo para desarrollo local. No deben usarse en produccion.

| Rol | Username | Password | Que permite probar |
| --- | --- | --- | --- |
| superuser Django | `superuser` | `Admin12345!` | Acceso total, admin Django y datos globales. |
| superadmin | `superadmin` | `Admin12345!` | Gestion global desde la aplicacion. |
| admin_negocio | `admin_negocio` | `Admin12345!` | Gestion del negocio demo, configuracion y operacion. |
| recepcionista | `recepcionista` | `Admin12345!` | Operacion diaria: clientes, turnos, agenda, disponibilidad y excepciones. |
| profesional | `profesional` | `Admin12345!` | Solo sus turnos y agenda asignada. |
| usuario sin membresia | `sin_membresia` | `Admin12345!` | Login sin datos operativos ni navegacion interna sensible. |

## Roles y permisos

- `superuser` de Django: puede ver y gestionar todo el sistema, acceder al admin
  de Django y ver todos los negocios.
- `superadmin`: puede ver todo el sistema, gestionar todos los negocios y
  acceder a datos globales desde la aplicacion.
- `admin_negocio`: ve solo sus negocios asignados y gestiona negocio,
  sucursales, clientes, servicios, profesionales, configuracion,
  disponibilidad, excepciones y turnos de esos negocios.
- `recepcionista`: ve solo sus negocios asignados. Puede gestionar operacion
  diaria como clientes, turnos, agenda, disponibilidad y excepciones. Puede ver
  sucursales, servicios y profesionales, pero no edita configuracion ni datos
  sensibles del negocio.
- `profesional`: ve su agenda y sus turnos. No ve turnos de otros
  profesionales, no gestiona configuracion, negocio, servicios globales ni otros
  profesionales.
- Usuario sin membresia: puede iniciar sesion, pero no ve navegacion ni datos
  operativos. El sistema muestra el aviso "No tenés negocios asignados.
  Contactá a un administrador.".

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
- `/agenda/semanal/`
- `/configuracion/`

## Comandos utiles

Desde la carpeta del proyecto Django:

```bash
cd sistema_turnos
python manage.py runserver
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py crear_usuarios_demo
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
