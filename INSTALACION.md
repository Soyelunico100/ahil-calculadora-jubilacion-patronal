# Instructivo de instalacion en otras maquinas

Este proyecto es una aplicacion local en Python para calcular Jubilacion Patronal en Ecuador y generar informes en Excel y PDF.

## 1. Requisitos

- Windows 10/11.
- Python 3.11 o superior. Recomendado: Python 3.12.
- Acceso a internet solo para la primera instalacion de dependencias.

Para comprobar Python:

```powershell
python --version
```

Si Windows no reconoce `python`, instalarlo desde <https://www.python.org/downloads/windows/> y marcar la opcion **Add python.exe to PATH**.

## 2. Copiar el proyecto

Copiar completa esta carpeta a la nueva maquina, por ejemplo:

```text
C:\Jubilacion patronal
```

La carpeta debe conservar estos archivos y subcarpetas:

```text
app.py
requirements.txt
INSTALACION.md
FUENTES.md
instalar.bat
ejecutar_app.bat
data\
jubilacion\
tests\
```

## 3. Crear entorno virtual

Abrir PowerShell dentro de la carpeta del proyecto:

```powershell
cd "C:\Jubilacion patronal"
python -m venv .venv
```

Activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activacion, usar solo para esa ventana:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Alternativa rapida: hacer doble clic en `instalar.bat`. Este archivo crea el entorno e instala las dependencias.

## 4. Instalar dependencias

Con internet:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Sin internet en la maquina destino:

1. En una maquina con internet, dentro de la carpeta del proyecto, ejecutar:

```powershell
python -m pip download -r requirements.txt -d wheelhouse
```

2. Copiar tambien la carpeta `wheelhouse` a la maquina destino.

3. En la maquina destino, instalar asi:

```powershell
python -m pip install --no-index --find-links wheelhouse -r requirements.txt
```

## 5. Verificar instalacion

Ejecutar las pruebas:

```powershell
python -m unittest discover -s tests -v
```

Resultado esperado:

```text
Ran 3 tests
OK
```

## 6. Ejecutar la aplicacion

Con el entorno virtual activo:

```powershell
streamlit run app.py
```

Alternativa rapida: hacer doble clic en `ejecutar_app.bat` despues de instalar.

Streamlit abrira una direccion local parecida a:

```text
http://localhost:8501
```

Abrir esa direccion en el navegador si no se abre automaticamente.

## 7. Uso basico

1. Ingresar datos del trabajador, empleador, fechas, sexo y causal.
2. Ingresar fondos de reserva causados, fondos pagados/depositados y aportes patronales.
3. Elegir ingreso resumido anual o detalle mensual.
4. Revisar parametros avanzados si se necesita ingresar edad, tiempo de servicio o C2 manual.
5. Presionar **Calcular**.
6. Descargar el informe en Excel o PDF.

La aplicacion muestra dos escenarios:

- **Solo fondos de reserva**: criterio recomendado, alineado con la Resolucion 16-2025.
- **Fondos de reserva + aportes**: escenario comparativo que replica el criterio del Excel/MDT.

## 8. Notas importantes

- El calculo es referencial y debe revisarse contra la normativa vigente y documentacion laboral del caso.
- Los coeficientes C2 incluidos cubren 2020, 2022, 2023, 2024, 2025 y 2026.
- Si el ano de salida no tiene tabla cargada, usar el campo avanzado **Ingresar C2 manual**.
- Para actualizar tablas futuras, reemplazar o ampliar `data\coeficientes_globales.csv` respetando las columnas existentes.
