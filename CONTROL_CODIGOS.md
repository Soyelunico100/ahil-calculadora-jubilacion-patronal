# Control de codigos de acceso

## Archivos importantes

Codigos para entregar a clientes:

```text
private/codigos_acceso_100.csv
```

Este archivo queda solo en tu maquina. No debe subirse a GitHub publico.

Hashes que usa la aplicacion:

```text
data/access_code_hashes.csv
```

Este archivo si puede subirse a GitHub porque no contiene los codigos en texto claro.

Registro de uso:

```text
private/access_usage.json
```

La aplicacion lo crea automaticamente cuando se usa un codigo.

## Regla de uso

- Cada codigo tiene 8 caracteres alfanumericos.
- Cada codigo se asigna al primer trabajador calculado.
- Para otro trabajador se necesita otro codigo.
- Cada codigo permite descargar maximo 10 informes para ese mismo trabajador.
- Las descargas de Excel y PDF cuentan como informes.
- La clave master del administrador permite calcular y descargar informes sin limite.
- La clave master esta guardada en la aplicacion como hash, no como texto claro.

## Como entregar codigos

1. Abra `private/codigos_acceso_100.csv`.
2. Copie un codigo con estado `disponible`.
3. Entregue ese codigo al cliente/trabajador.
4. Puede anotar manualmente el trabajador asignado en ese CSV para su control interno.

## Como generar otros 100 codigos

Ejecute:

```powershell
python generar_codigos.py
```

Esto reemplaza:

```text
private/codigos_acceso_100.csv
data/access_code_hashes.csv
```

Si ya publico la app en Streamlit Cloud, despues de generar nuevos codigos debe subir a GitHub el nuevo:

```text
data/access_code_hashes.csv
```

## Nota para Streamlit Cloud

En una app publica de Streamlit Cloud, el registro `private/access_usage.json` puede reiniciarse si el servidor se reinicia o se redepliega. Para control juridico/comercial estricto en internet conviene conectar una base externa, por ejemplo Google Sheets, Supabase o Firebase. Para uso local en tu maquina, el control queda guardado en `private/access_usage.json`.
