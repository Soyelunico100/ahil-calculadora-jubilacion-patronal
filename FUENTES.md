# Fuentes usadas

## Documentos locales revisados

- `Calculo de Jubilacion Patronal y Jubilacion por Vejez.xlsx`
- `MDT-2016-0099 CALCULO DE LA JUBILACION PATRONAL.pdf`
- `2021-07-Triple-reiteracion-calculo-de-la-pension-jubilar.pdf`
- `RESOLUCION No. 16-2025 Descontar fondos de reserva del valor de la Jubilacion Patronal.pdf`
- `RESOLUCION No. 04-2026.pdf`
- Codigo del Trabajo cargado/revisado para articulos 216, 217 y 218 sobre jubilacion patronal.
- `TABLA-DE-COEFICIENTE-ANO-2016-.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2017-.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2018-.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2019-.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2020-.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2021-.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2022.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2023-.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2024-.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2025-.pdf`
- `TABLA-DE-COEFICIENTE-ANO-2026-.pdf`

## Fuentes oficiales en linea

- Ministerio del Trabajo, Jubilacion Patronal: <https://www.trabajo.gob.ec/jubilacion-patronal/>
- Tabla de coeficientes 2026: <https://www.trabajo.gob.ec/wp-content/uploads/2026/02/Tabla-de-coeficientes-para-el-calculo-global-de-Jubilacion-Patronal-2026.pdf>
- Corte Nacional de Justicia, Resolucion No. 16-2025 sobre fondos de reserva para el calculo de jubilacion patronal: <https://www.cortenacional.gob.ec/cnj/images/pdf/resoluciones/2025/16-2025-Jurisprudencia-obligatoria---valores-de-fondo-de-reserva-para-el-calculo-de-la-jubilacion.pdf>
- Pregunta oficial sobre limite maximo de pension, Resolucion 07-2021: <https://www.trabajo.gob.ec/14-de-acuerdo-a-la-jurisprudencia-dictada-por-la-corte-nacional-de-justicia-contenida-en-la-resolucion-no-07-2021-cual-es-la-formula-de-calculo-para-obtener-el-monto-maximo-de-la-pension-de/>
- Pregunta oficial sobre reglas de pago y MDT-2016-0099: <https://www.trabajo.gob.ec/32-cuales-son-las-reglas-para-efectuar-el-pago-de-la-jubilacion-a-cargo-de-los-empleadores/>

## Nota sobre Resolucion 16-2025

La Resolucion No. 16-2025 de la Corte Nacional de Justicia declara precedente jurisprudencial obligatorio sobre los valores de fondos de reserva en el calculo de jubilacion patronal. La aplicacion toma este criterio como escenario recomendado: el fondo de reserva integra el haber individual y, por favorabilidad, se rebajan solo los fondos de reserva pagados, entregados o depositados; los aportes patronales se conservan solo como escenario comparativo.

## Nota sobre Resolucion 04-2026

La Resolucion No. 04-2026 de la Corte Nacional de Justicia confirma que el fondo global de jubilacion patronal, cuando existe acuerdo de las partes, debe calcularse aplicando los acuerdos ministeriales vigentes a la fecha de terminacion de la relacion laboral. La aplicacion usa ese criterio al seleccionar el coeficiente C2 por anio de cese o permitir C2 manual si el anio no esta cargado.

## Nota sobre tablas C2

El archivo `data/coeficientes_globales.csv` fue reconstruido desde los PDF locales de tablas 2016-2026. Las tablas 2016, 2017, 2018, 2019, 2020, 2022, 2023, 2024, 2025 y 2026 contienen edades 39-99. El PDF 2021 disponible contiene edades 39-79; para un caso 2021 con edad superior se debe ingresar el coeficiente C2 manualmente desde la fuente oficial que corresponda.

## Nota sobre Codigo del Trabajo

La calculadora aplica el articulo 216 para derecho, formula, limites de pension mensual y minimo de fondo global; el articulo 217 para explicar el derecho de herederos por un anio; y el articulo 218 como base del coeficiente de edad C1. Estos puntos constan en la app y en el informe PDF/Excel.
