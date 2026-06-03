# Publicar en Streamlit Community Cloud

Recomendado para esta aplicacion porque Streamlit Community Cloud permite crear, desplegar y administrar apps Streamlit gratis desde GitHub.

## Requisitos

- Cuenta de GitHub.
- Cuenta de Streamlit Community Cloud: <https://share.streamlit.io/>
- Esta carpeta subida a un repositorio GitHub.

## Pasos

1. Crear un repositorio en GitHub, por ejemplo:

```text
ahil-calculadora-jubilacion-patronal
```

2. Subir estos archivos y carpetas:

```text
app.py
requirements.txt
runtime.txt
.streamlit/
assets/
data/
jubilacion/
tests/
README.md
INSTALACION.md
FUENTES.md
CONTROL_CODIGOS.md
```

No subir la carpeta `private/`; contiene codigos en texto claro y control local de uso.

3. Entrar a Streamlit Community Cloud:

```text
https://share.streamlit.io/
```

4. Iniciar sesion con GitHub.

5. Presionar **Create app** o **New app**.

6. Seleccionar:

```text
Repository: ahil-calculadora-jubilacion-patronal
Branch: main
Main file path: app.py
```

7. Presionar **Deploy**.

8. Cuando termine, Streamlit dara una URL publica similar a:

```text
https://ahil-calculadora-jubilacion-patronal.streamlit.app
```

Esa URL si se puede colocar en Gamma.

## Texto sugerido para Gamma

Nombre:

```text
Calculadora de Jubilacion Patronal | AHIL Legal Tech
```

Descripcion:

```text
Herramienta de apoyo juridico-laboral para estimar pension mensual, fondo global y generar informes Excel/PDF con desglose de calculos.
```

Boton:

```text
Abrir calculadora
```

URL:

```text
Pegar aqui la URL publica que entregue Streamlit Cloud.
```
