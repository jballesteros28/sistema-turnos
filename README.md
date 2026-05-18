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
- `notificaciones`: registro y envio basico de emails de eventos de turnos.
- `reservas`: flujo publico online para que clientes finales reserven turnos.
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

## Reserva publica online

El flujo publico permite reservar sin entrar al panel interno:

- Ruta base: `/reservar/<negocio_slug>/`
- Ejemplo con datos demo: `/reservar/negocio-demo/`
- Seleccion de turno: sucursal, servicio, profesional opcional y fecha.
- Confirmacion: datos del cliente, email o telefono obligatorio y
  observaciones opcionales.
- El sistema calcula slots reales, recalcula disponibilidad al confirmar,
  crea o reutiliza el cliente del negocio, crea el turno con origen `online` y
  envia el email de turno creado cuando corresponde.

Para probarlo en desarrollo local:

```bash
cd sistema_turnos
python manage.py crear_usuarios_demo
python manage.py runserver
```

Luego abrir `/reservar/negocio-demo/`. Este flujo no requiere login y no muestra
la navegacion privada. El backoffice sigue siendo privado y mantiene login en
`/dashboard/`, `/turnos/` y `/agenda/turnos/`.

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
- `/reservar/<negocio_slug>/`
- `/reservar/<negocio_slug>/turno/`
- `/reservar/<negocio_slug>/confirmar/`
- `/reservar/<negocio_slug>/exito/`

## Configuracion de email

El sistema envia emails basicos para eventos principales de turnos usando el
email nativo de Django. Toda credencial debe configurarse por variables de
entorno; no se deben hardcodear datos reales en el repositorio.

### Variables necesarias

- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`
- `DEFAULT_FROM_EMAIL`

### Modo local con consola

En desarrollo el backend por defecto escribe los mensajes en consola:

```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@sistema-turnos.local"
```

Ejemplo en `.env` local:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@sistema-turnos.local
```

### Modo SMTP real

Para enviar por SMTP real, configurar estas variables en el entorno de
produccion o del proceso:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.tu-proveedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@dominio.com
EMAIL_HOST_PASSWORD=tu-password-o-app-password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=Sistema de Turnos <tu-email@dominio.com>
```

### Probar configuracion

Desde la carpeta del proyecto Django:

```bash
python manage.py probar_email correo@ejemplo.com
```

Con el backend de consola, el email se imprime en la terminal. Con SMTP, el
comando intenta enviarlo usando la configuracion actual.

No commitear `.env`. No usar credenciales reales en `.env.example`.

Eventos que disparan email en esta etapa:

- turno creado
- turno confirmado
- turno cancelado
- turno completado
- turno marcado como ausente

El envio es simple y sincronico. Si el cliente no tiene email, el flujo del
turno continua sin crear notificacion. Si el envio falla, se registra el intento
como fallido y el turno no se rompe. Celery, Redis, recordatorios programados y
colas asincronicas quedan para una etapa futura.

## Preparacion para produccion

El proyecto queda preparado para un deploy controlado mediante variables de
entorno. No se debe commitear un archivo `.env` real ni credenciales secretas;
usar `.env.example` como referencia. Django lee variables del entorno del
proceso; si se usa un archivo `.env`, debe cargarlo la shell, el servicio o la
plataforma de deploy.

### Variables de entorno necesarias

- `DJANGO_SECRET_KEY`: clave secreta de Django. Obligatoria en produccion.
- `DJANGO_DEBUG`: `True` en desarrollo, `False` en produccion.
- `DJANGO_ALLOWED_HOSTS`: hosts permitidos separados por coma.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: origenes confiables separados por coma, con
  esquema `https://` en produccion.
- `DATABASE_ENGINE`: `sqlite` para local o `postgres` para produccion.
- `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`,
  `DATABASE_PORT`: datos de conexion de base.
- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
  `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`,
  `DEFAULT_FROM_EMAIL`: configuracion de email.
- `STATIC_URL`, `MEDIA_URL`: URLs publicas de archivos estaticos y media.
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`,
  `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`,
  `SECURE_HSTS_PRELOAD`: controles de seguridad para HTTPS.

### Ejemplo de `.env` local

```env
DJANGO_SECRET_KEY=dev-insecure-local-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

DATABASE_ENGINE=sqlite
DATABASE_NAME=db.sqlite3

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=no-reply@sistema-turnos.local

STATIC_URL=/static/
MEDIA_URL=/media/

SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
```

### Ejemplo de `.env` produccion

```env
DJANGO_SECRET_KEY=change-me-with-a-real-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=turnos.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://turnos.example.com

DATABASE_ENGINE=postgres
DATABASE_NAME=sistema_turnos
DATABASE_USER=sistema_turnos_user
DATABASE_PASSWORD=change_me
DATABASE_HOST=localhost
DATABASE_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=sistema-turnos@example.com
EMAIL_HOST_PASSWORD=change_me
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=no-reply@example.com

STATIC_URL=/static/
MEDIA_URL=/media/

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Comandos de preparacion

Desde la raiz del repositorio:

```bash
pip install -r requirements.txt
```

Desde la carpeta del proyecto Django:

```bash
cd sistema_turnos
python manage.py migrate
python manage.py createsuperuser
python manage.py crear_usuarios_demo
python manage.py collectstatic --noinput
python manage.py check
python manage.py check --deploy
python manage.py test
```

`crear_usuarios_demo` es solo para desarrollo local. No usar credenciales demo
en produccion.

En produccion, los archivos estaticos recolectados en `staticfiles/` deben ser
servidos por el servidor web o la plataforma de deploy. Django solo sirve
archivos `media/` desde `urls.py` cuando `DEBUG=True`.

## Comandos utiles

Desde la carpeta del proyecto Django:

```bash
cd sistema_turnos
python manage.py runserver
python manage.py check
python manage.py check --deploy
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py probar_email test@example.com
python manage.py collectstatic --noinput
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
