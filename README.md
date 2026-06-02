# Calculadora de Jubilacion Patronal Ecuador

Aplicacion web local en Python para calcular pension mensual, fondo global y generar informe Excel/PDF.

Nombre recomendado para publicar en AHIL Legal Tech:

```text
Calculadora de Jubilacion Patronal | AHIL Legal Tech
```

Descripcion corta:

```text
Herramienta de apoyo juridico-laboral para estimar pension mensual, fondo global y generar informes Excel/PDF con desglose de calculos.
```

Nota: `http://localhost:8501` solo funciona en la computadora donde esta encendida la aplicacion. Para colocarla en una pagina publica de Gamma se debe publicar la app en un hosting o servidor y usar la URL publica resultante.

## Ejecutar rapido

En Windows, puede hacer doble clic en `instalar.bat` y luego en `ejecutar_app.bat`.

O manualmente:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Para instalar en otra maquina, ver [INSTALACION.md](INSTALACION.md).

## Verificar

```powershell
python -m unittest discover -s tests -v
```

## Fuentes principales

- Excel original: `Calculo de Jubilacion Patronal y Jubilacion por Vejez.xlsx`.
- MDT-2016-0099: formula de calculo mensual y fondo global.
- Resolucion 07-2021: limite maximo de pension mensual.
- Resolucion 16-2025: tratamiento de fondos de reserva.
- Resolucion 04-2026: criterio actual para aplicar acuerdos ministeriales vigentes al fondo global.
- Tablas de coeficientes globales 2022-2026 del Ministerio del Trabajo.
