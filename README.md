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

## Variables de entorno y SMTP

El proyecto carga automaticamente un archivo `.env` al iniciar Django usando
`python-dotenv` con `override=True` para que, en desarrollo local, el archivo
`.env` pise variables previas del entorno. El archivo puede estar junto a
`manage.py` o en la raiz del repositorio. En esta estructura se busca primero
`sistema_turnos/.env` y luego `.env`.

El archivo real `.env` no debe commitearse; usar `.env.example` como guia.

La configuracion se lee con `os.getenv()` y se castea donde corresponde:
`DJANGO_DEBUG`, `EMAIL_USE_TLS` y `EMAIL_USE_SSL` como booleanos, y
`EMAIL_PORT` como entero.

Variables principales:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DATABASE_ENGINE`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`,
  `DATABASE_HOST`, `DATABASE_PORT`
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`
- `DEFAULT_FROM_EMAIL`

### Backend de consola

Para desarrollo local se puede usar el backend de consola. No envia emails
reales: imprime el mensaje MIME en la terminal.

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@sistema-turnos.local
```

### Backend SMTP

Para SMTP real, usar el backend SMTP de Django y las credenciales del proveedor.
Ejemplo con Gmail:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=tu-email@gmail.com
```

Evitar comillas raras, espacios invisibles o espacios al principio/final en
`EMAIL_HOST_PASSWORD`. Para Gmail, pegar la App Password tal como la entrega
Google.

`DEFAULT_FROM_EMAIL` tambien puede usar nombre visible:

```env
DEFAULT_FROM_EMAIL=Sistema de Turnos <tu-email@gmail.com>
```

Con Gmail no se debe usar la password normal de la cuenta. Hay que activar la
verificacion en dos pasos y crear una App Password desde la configuracion de la
cuenta de Google. Esa App Password es el valor de `EMAIL_HOST_PASSWORD`.

### Probar configuracion

Desde la carpeta del proyecto Django:

```bash
python manage.py diagnosticar_env
python manage.py probar_email correo@ejemplo.com
```

`diagnosticar_env` muestra `BASE_DIR`, las rutas buscadas, que `.env` fue
encontrado y los valores principales de email con tipos casteados. Nunca imprime
la password completa: solo informa si esta cargada y cuantos caracteres tiene.

`probar_email` muestra backend, host, puerto, usuario, TLS/SSL, remitente y
estado de password sin imprimirla. Con backend de consola se vera el MIME
completo en terminal; con SMTP debe intentar enviar un email real y mostrar
`SUCCESS` si Django reporta el envio. Si SMTP no tiene password cargada, el
comando corta con un error claro y sugiere revisar `.env` y `diagnosticar_env`.

No usar credenciales reales en `.env.example`.

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
proceso y, para desarrollo local, carga automaticamente el archivo `.env` si
existe.

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
servidos por WhiteNoise dentro de Django. Django solo sirve archivos `media/`
desde `urls.py` cuando `DEBUG=True`.

## Deploy en Render

Render Free no ofrece una shell interactiva persistente para preparar la app,
por eso el deploy inicial usa `build.sh` para instalar dependencias, recolectar
estaticos, migrar la base y crear datos iniciales de forma idempotente.

### Pasos

1. Crear una base PostgreSQL en Render.
2. Crear un Web Service desde GitHub apuntando a este repositorio.
3. Configurar el Build Command:

```bash
./build.sh
```

4. Configurar el Start Command:

```bash
gunicorn --chdir sistema_turnos sistema_turnos.wsgi:application
```

El `--chdir sistema_turnos` es necesario porque `manage.py` y el paquete Django
estan dentro de la carpeta `sistema_turnos/`.

### Variables de entorno

Configurar estas variables en Render, sin commitear `.env` ni secretos:

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-app.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com

DATABASE_ENGINE=postgres
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_HOST=
DATABASE_PORT=5432

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

CREATE_DEMO_USERS=True

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

`crear_superuser_render` usa `DJANGO_SUPERUSER_USERNAME`,
`DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`. Si falta alguna, muestra
un warning y no falla el deploy. Nunca imprime la password.

`crear_usuarios_demo --render-safe` solo crea usuarios y datos demo si
`CREATE_DEMO_USERS=True`. Para produccion real, usar `CREATE_DEMO_USERS=False` y
no usar credenciales demo. El comando puede ejecutarse muchas veces: reutiliza
negocio, sucursal, servicio, profesional, cliente, disponibilidad,
configuracion, usuarios y membresias existentes.

Si Render presenta problemas de redireccion por proxy con
`SECURE_SSL_REDIRECT=True`, desactivarlo temporalmente con
`SECURE_SSL_REDIRECT=False` mientras se revisa la configuracion HTTPS. La
preferencia para produccion es mantenerlo en `True`. El proyecto ya configura
`SECURE_PROXY_SSL_HEADER` para reconocer `X-Forwarded-Proto: https`, que es lo
esperado detras del proxy de Render.

### Static y media

WhiteNoise sirve los archivos estaticos generados por `collectstatic`; no se
debe commitear `staticfiles/`.

Render Free no ofrece filesystem persistente. `media/` puede funcionar de forma
temporal, pero para archivos importantes en produccion real se debe usar S3,
Cloudinary u otro storage externo. No se implementa storage externo todavia.

### URLs a probar

- `/accounts/login/`
- `/dashboard/`
- `/reservar/negocio-demo/`

## Comandos utiles

Desde la carpeta del proyecto Django:

```bash
cd sistema_turnos
python manage.py runserver
python manage.py check
python manage.py check --deploy
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py diagnosticar_env
python manage.py probar_email test@example.com
python manage.py collectstatic --noinput
python manage.py crear_superuser_render
python manage.py crear_usuarios_demo
python manage.py crear_usuarios_demo --render-safe
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
