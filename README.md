# Sistema de Turnos

MVP en Django para administrar turnos de negocios con sucursales, servicios,
profesionales, clientes, disponibilidad horaria, excepciones de agenda y agenda
diaria/semanal.

## Estructura

```text
repo/
  manage.py
  requirements.txt
  .env.example
  README.md
  build.sh

  agenda/
  clientes/
  configuracion_negocio/
  core/
  disponibilidad/
  excepcion/
  negocio/
  notificaciones/
  profesional/
  reservas/
  servicio/
  sucursal/
  turnos/
  usuarios/

  sistema_turnos/
    settings.py
    urls.py
    wsgi.py
    asgi.py
    view_utils.py

  static/
  templates/
  media/
```

El modulo de configuracion de Django es `sistema_turnos.settings`, el
`ROOT_URLCONF` es `sistema_turnos.urls` y la aplicacion WSGI es
`sistema_turnos.wsgi.application`.

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

## Puesta en marcha local

Crear un archivo `.env` en la raiz del proyecto, junto a `manage.py`. Usar
`.env.example` como guia.

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py crear_usuarios_demo
python manage.py runserver
```

Luego abrir:

- `/accounts/login/`
- `/dashboard/`
- `/reservar/negocio-demo/`
- `/turnos/`
- `/agenda/semanal/`

Credenciales demo para desarrollo local:

| Rol | Username | Password |
| --- | --- | --- |
| superuser Django | `superuser` | `Admin12345!` |
| superadmin | `superadmin` | `Admin12345!` |
| admin_negocio | `admin_negocio` | `Admin12345!` |
| recepcionista | `recepcionista` | `Admin12345!` |
| profesional | `profesional` | `Admin12345!` |
| usuario sin membresia | `sin_membresia` | `Admin12345!` |

## Variables de entorno

Django carga automaticamente `repo/.env` con `python-dotenv` y `override=True`.
No se buscan otros archivos `.env`.

Variables principales:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
  `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`,
  `DEFAULT_FROM_EMAIL`
- `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`,
  `DJANGO_SUPERUSER_PASSWORD`
- `CREATE_DEMO_USERS`
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`,
  `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`,
  `SECURE_HSTS_PRELOAD`

### Base de datos

La base se configura con `DATABASE_URL` usando `dj-database-url`.

Local:

```env
DATABASE_URL=sqlite:///db.sqlite3
```

Render/PostgreSQL:

```env
DATABASE_URL=postgres://usuario:password@host:5432/dbname
```

Si `DATABASE_URL` no esta definida, Django usa `db.sqlite3` en la raiz del repo.
Render suele entregar `DATABASE_URL` automaticamente al vincular una base
PostgreSQL.

### Email

Para desarrollo local se puede usar el backend de consola:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=no-reply@sistema-turnos.local
```

Para SMTP real, configurar el backend SMTP de Django y las credenciales del
proveedor:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=sistema-turnos@example.com
EMAIL_HOST_PASSWORD=change_me
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=no-reply@example.com
```

No commitear `.env` ni credenciales reales.

## Comandos utiles

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
python manage.py diagnosticar_env
python manage.py probar_email test@example.com
python manage.py crear_superuser_render
python manage.py crear_usuarios_demo
python manage.py crear_usuarios_demo --render-safe
```

`diagnosticar_env` muestra `BASE_DIR`, la ruta oficial de `.env`, los valores
principales de email con tipos casteados y la configuracion de base activa sin
imprimir passwords.

## Deploy en Render

Build Command:

```bash
./build.sh
```

Start Command:

```bash
gunicorn sistema_turnos.wsgi:application
```

Variables minimas en Render:

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-app.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com

DATABASE_URL=postgres://usuario:password@host:5432/dbname

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=

DJANGO_SUPERUSER_USERNAME=
DJANGO_SUPERUSER_EMAIL=
DJANGO_SUPERUSER_PASSWORD=
CREATE_DEMO_USERS=False

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

`crear_superuser_render` usa `DJANGO_SUPERUSER_USERNAME`,
`DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`. Si falta alguna, muestra
un warning y no falla el deploy.

`crear_usuarios_demo --render-safe` solo crea usuarios y datos demo si
`CREATE_DEMO_USERS=True`.

## Static y media

WhiteNoise sirve los archivos estaticos recolectados por `collectstatic` desde
`staticfiles/`. Esa carpeta no debe commitearse.

`media/` esta ignorada por git. En Render Free el filesystem no es persistente;
para archivos importantes en produccion real conviene usar S3, Cloudinary u
otro storage externo.

## Rutas principales

- `/dashboard/`
- `/accounts/login/`
- `/reservar/negocio-demo/`
- `/turnos/`
- `/agenda/semanal/`
- `/negocios/`
- `/sucursales/`
- `/clientes/`
- `/servicios/`
- `/profesionales/`
- `/agenda/disponibilidades/`
- `/agenda/excepciones/`
- `/agenda/turnos/`
- `/configuracion/`

## Notas

- `db.sqlite3`, `*.sqlite3`, `.env`, `media/`, `staticfiles/`, `__pycache__/`,
  `*.pyc`, `.venv/` y `venv/` deben permanecer ignorados.
- `db.sqlite3` contiene datos locales de prueba y no debe usarse como base de
  produccion.
- Los listados, dashboard, agenda, turnos y formularios filtran por negocios
  permitidos; los accesos directos a objetos fuera del alcance responden 404.
