# Configuración de Render para linguistic_app

## Paso 1: Crear la base de datos PostgreSQL en Render

1. Ve a https://dashboard.render.com/
2. Haz click en **"New +"** en la esquina superior derecha
3. Selecciona **"PostgreSQL"**
4. Completa los campos:
   - **Name**: `linguistic-app-db`
   - **Database**: `linguistic_mvp`
   - **User**: `linguistic_user`
   - **Region**: la más cercana a ti
   - **PostgreSQL Version**: 15
5. Haz click en **"Create Database"**
6. Espera a que se cree (toma unos 2-3 minutos)
7. Una vez creada, copia la **Internal Database URL** (verás algo como `postgresql://user:pass@host/dbname`)

## Paso 2: Crear el servicio web en Render

1. De nuevo, haz click en **"New +"**
2. Selecciona **"Web Service"**
3. Conecta tu repositorio GitHub:
   - Haz click en **"Connect a repository"**
   - Selecciona `yuranimar/linguistic_app`
4. Completa los campos:
   - **Name**: `linguistic-app`
   - **Environment**: `Python 3`
   - **Region**: la misma de la BD
   - **Branch**: `main`
   - **Build Command**: 
     ```
     pip install -r requirements.txt && python init_db.py
     ```
   - **Start Command**: 
     ```
     gunicorn --bind 0.0.0.0:$PORT app:app
     ```
   - **Plan**: Free (o Paid si quieres)

## Paso 3: Configurar las variables de entorno

1. En la página del servicio web que acabas de crear, ve a la sección **"Environment"**
2. Haz click en **"Add Environment Variable"** y añade estas 3:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | La URL que copiaste de PostgreSQL en el Paso 1 |
| `SECRET_KEY` | Cualquier string largo, ej: `mi-clave-secreta-super-larga-123456` |
| `FLASK_ENV` | `production` |

3. Haz click en **"Save"**

## Paso 4: Desplegar

1. La app debería empezar a desplegarse automáticamente
2. Espera a que termine (verás un ✅ en verde cuando esté listo)
3. Render te dará una URL pública, algo como `https://linguistic-app-xxxxx.onrender.com`
4. Abre esa URL en el navegador

## Paso 5: Probar login

1. La URL que ves en Render es tu app pública
2. Ve a `https://linguistic-app-xxxxx.onrender.com/login`
3. Usa estas credenciales:
   - Email: `admin@gestor.co`
   - Contraseña: `admin123`

## Notas importantes

- **NO uses GitHub Pages** para esta app. Es una aplicación Flask, no un sitio HTML estático.
- La URL pública correcta es la de Render, no la de GitHub.
- La base de datos PostgreSQL en Render es persistente, a diferencia de SQLite que se pierde.
- Si el login aún falla, ve a **"Logs"** en el dashboard de Render y busca el error exacto.

## Cambiar la contraseña del admin (importante en producción)

1. Una vez que hayas iniciado sesión como admin
2. Contacta al administrador o modifica manualmente la contraseña en la BD
3. Por ahora, úsala como está pero cámbiala después

---

¿Necesitas ayuda en alguno de estos pasos? Pregunta.
