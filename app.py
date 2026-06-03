from __future__ import annotations

from dataclasses import fields
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

from jubilacion import CalculationInput, CoefficientStore, calculate_jubilacion
from jubilacion.access_control import assign_code_to_worker, register_report_download, validate_access
from jubilacion.calculator import money
from jubilacion.legal_basis import LEGAL_BASIS
from jubilacion.reports import build_excel_report, build_pdf_report


LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo-ronquillo.png"
LOGO_IMAGE = Image.open(LOGO_PATH) if LOGO_PATH.exists() else None
FORMULA_PENSION_PATH = Path(__file__).resolve().parent / "assets" / "formula_pension_mensual.png"
FORMULA_GLOBAL_PATH = Path(__file__).resolve().parent / "assets" / "formula_fondo_global.png"

st.set_page_config(
    page_title="AHIL Legal Tech - Jubilacion Patronal",
    page_icon=LOGO_IMAGE,
    layout="wide",
)

st.markdown(
    """
    <style>
      :root {
        --ahil-blue: #0f4c81;
        --ahil-celeste: #dff4ff;
        --ahil-ink: #10233f;
      }
      html, body, [data-testid="stAppViewContainer"] {
        background:
          radial-gradient(circle at 12% 8%, rgba(77, 171, 247, 0.24), transparent 32%),
          radial-gradient(circle at 92% 18%, rgba(15, 76, 129, 0.14), transparent 30%),
          linear-gradient(135deg, #f8fcff 0%, #eef8ff 42%, #ffffff 78%);
      }
      [data-testid="stHeader"] {
        background: rgba(248, 252, 255, 0.78);
        backdrop-filter: blur(8px);
      }
      .main .block-container {
        padding-top: 2.1rem;
        padding-bottom: 4.8rem;
      }
      div[data-testid="stForm"] {
        border: 1px solid rgba(15, 76, 129, 0.16);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.92);
        box-shadow: 0 18px 44px rgba(16, 35, 63, 0.08);
      }
      div[data-testid="stMetric"] {
        border: 1px solid rgba(15, 76, 129, 0.12);
        border-radius: 12px;
        padding: 12px 14px;
        background: linear-gradient(180deg, #ffffff 0%, #eff9ff 100%);
      }
      h1, h2, h3 {
        color: var(--ahil-ink);
      }
      .stButton button, .stDownloadButton button {
        border-radius: 10px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

header_logo, header_text = st.columns([1, 6])
with header_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=110)
with header_text:
    st.title("AHIL Legal Tech | Calculadora de Jubilacion Patronal")
    st.caption(
        "Herramienta local de consultoria juridica, tributaria y laboral para estimar "
        "pension mensual, fondo global y generar informes Excel/PDF."
    )
st.info(
    "Criterio aplicado: la Resolucion No. 16-2025 de la Corte Nacional de Justicia "
    "declara precedente obligatorio sobre fondos de reserva en jubilacion patronal. "
    "Por favorabilidad, el escenario recomendado descuenta solo fondos de reserva "
    "pagados, entregados o depositados; los aportes patronales se muestran solo en "
    "un escenario comparativo."
)
with st.expander("Base legal aplicada en la calculadora"):
    for title, detail in LEGAL_BASIS:
        st.markdown(f"**{title}.** {detail}")

with st.expander("Formulas oficiales MDT-2016-0099"):
    formula_left, formula_right = st.columns(2)
    with formula_left:
        st.markdown("**Pension mensual**")
        if FORMULA_PENSION_PATH.exists():
            st.image(str(FORMULA_PENSION_PATH), width=330)
        st.caption("A = fondos de reserva; B = promedio anual ultimos 5 anos; C = tiempo de servicio; D = descuento; E = coeficiente C1.")
    with formula_right:
        st.markdown("**Fondo global**")
        if FORMULA_GLOBAL_PATH.exists():
            st.image(str(FORMULA_GLOBAL_PATH), width=300)
        st.caption("A = coeficiente global C2; B = pension mensual; C = decimotercera; D = decimocuarta.")

st.warning(
    "Acceso restringido. Para solicitar un codigo de uso, comuniquese con Pablo "
    "Ronquillo - AHIL Legal Tech. Pagina: "
    "https://ahil-legal-tech-6yuizq3.gamma.site/#card-atqpfiqapdfgy80"
)

store = CoefficientStore()


def as_decimal(value) -> Decimal:
    return Decimal(str(value or "0"))


def month_labels(end: date, count: int) -> list[str]:
    labels = []
    for offset in range(count - 1, -1, -1):
        raw_month = end.month - offset
        year = end.year + (raw_month - 1) // 12
        month = (raw_month - 1) % 12 + 1
        labels.append(f"{year}-{month:02d}")
    return labels


def split_annual_totals(month_values: list[Decimal]) -> list[Decimal]:
    return [
        sum(month_values[start : start + 12], Decimal("0"))
        for start in range(0, 60, 12)
    ]


def annual_period_labels(end: date, periods: int = 5) -> list[str]:
    labels = month_labels(end, periods * 12)
    return [
        f"{labels[start]} a {labels[start + 11]}"
        for start in range(0, periods * 12, 12)
    ]


def usd(value: Decimal) -> str:
    return f"USD {money(value):,.2f}"


def note(text: str) -> None:
    st.caption(f"Observacion: {text}")


st.subheader("Fecha base del calculo")
fecha_salida = st.date_input(
    "Fecha de salida / terminacion de la relacion laboral",
    value=date.today(),
    min_value=date(1900, 1, 1),
    max_value=date(2100, 12, 31),
    key="fecha_salida_global",
)
note(
    "Cambie primero esta fecha. Con ella se actualizan los cinco periodos de "
    "remuneracion, el anio sugerido de coeficiente global C2 y el tiempo de servicio."
)


with st.form("calculo"):
    st.subheader("Codigo de acceso")
    access_code = st.text_input("Codigo alfanumerico de 8 caracteres o clave master", max_chars=32, type="password")
    note(
        "Ingrese el codigo entregado por AHIL Legal Tech. Cada codigo se asigna al "
        "primer trabajador calculado y permite descargar maximo 10 informes para ese trabajador. "
        "La clave master del administrador permite acceso ilimitado."
    )

    left, right = st.columns(2)
    with left:
        trabajador = st.text_input("Nombre del trabajador")
        note("Ingrese nombres y apellidos completos del trabajador que constaran en el informe.")
        identificacion = st.text_input("Cedula / identificacion")
        note("Ingrese cedula, RUC o identificacion usada en la relacion laboral.")
        cargo = st.text_input("Cargo")
        note("Ingrese el cargo o puesto que ocupaba al momento del cese.")
        sexo = st.selectbox("Sexo para coeficiente global", ["Hombre", "Mujer"])
        note("Seleccione el sexo que corresponda para buscar el coeficiente global C2.")
        fecha_nacimiento = st.date_input(
            "Fecha de nacimiento",
            value=date(1970, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        note("Ingrese la fecha de nacimiento para calcular la edad al determinar la renta.")
        fecha_ingreso = st.date_input(
            "Fecha de ingreso",
            value=date(1990, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        note("Ingrese la fecha real de inicio de la relacion laboral.")
        st.markdown(f"**Fecha de salida seleccionada:** {fecha_salida:%d/%m/%Y}")
        note("Esta fecha se selecciona arriba para que los periodos se actualicen antes de calcular.")
    with right:
        empleador = st.text_input("Empleador")
        note("Ingrese razon social o nombre del empleador que constara en el informe.")
        doble_jubilacion = st.checkbox("Tiene doble jubilacion")
        note("Marque si el trabajador tambien recibe jubilacion del IESS; cambia el minimo mensual a USD 20.")
        despido_intempestivo = st.checkbox("Despido intempestivo")
        note("Marque solo si aplica jubilacion proporcional por despido intempestivo entre mas de 20 y menos de 25 anos.")
        fondos_reserva_derecho = st.number_input(
            "Fondos de reserva causados (A / FRR)", min_value=0.0, step=100.0
        )
        note("Coloque el total de fondos de reserva a que tuvo derecho el trabajador durante la relacion laboral.")
        fondos_reserva_pagados = st.number_input(
            "Fondos de reserva pagados/depositados", min_value=0.0, step=100.0
        )
        note("Coloque los fondos de reserva ya entregados al trabajador o depositados en el IESS.")
        aportes_patronales = st.number_input(
            "Aportes patronales pagados/depositados", min_value=0.0, step=100.0
        )
        note("Coloque la suma de aportes patronales si desea ver el escenario comparativo del MDT/Excel.")
        decimotercera = st.number_input(
            "Decimotercera remuneracion para fondo global",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )
        note("Si deja este valor en 0, la app usa automaticamente una pension mensual aplicada como decimotercera.")
        decimocuarta = st.number_input(
            "Decimocuarta remuneracion para fondo global",
            min_value=0.0,
            value=470.0,
            step=10.0,
        )
        note("Coloque el valor de la decimocuarta remuneracion vigente que se suma al fondo global.")
        remuneracion_sectorial = st.number_input(
            "Remuneracion sectorial vigente al cese",
            min_value=0.0,
            value=470.0,
            step=10.0,
        )
        note("Coloque la remuneracion basica sectorial del cargo al cese; valida el minimo del fondo global.")

    st.subheader("Remuneraciones")
    modo = st.radio("Modo de ingreso", ["Resumen anual", "Detalle mensual"], horizontal=True)
    note("Use resumen anual si ya tiene totales por anio; use detalle mensual si desea que la app los sume.")
    remuneraciones_5: list[Decimal]
    remuneraciones_12: list[Decimal] = []
    if modo == "Resumen anual":
        cols = st.columns(5)
        periodos = annual_period_labels(fecha_salida)
        period_key = f"{fecha_salida.year}_{fecha_salida.month:02d}"
        remuneraciones_50 = []
        for idx, col in enumerate(cols):
            with col:
                value = st.number_input(
                    f"Periodo {idx + 1}: {periodos[idx]}",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    key=f"annual_{period_key}_{idx}",
                )
                note("Ingrese el total ganado en este periodo de 12 meses segun roles de pago o certificado laboral.")
                remuneraciones_50.append(as_decimal(value))
        total_ultimo = st.number_input(
            f"Total remuneracion ultimo anio ({periodos[-1]})",
            min_value=0.0,
            value=float(remuneraciones_50[-1]) if remuneraciones_50 else 0.0,
            step=100.0,
            key=f"last_year_{period_key}",
        )
        note("Ingrese la suma de remuneraciones de los ultimos 12 meses; sirve para el limite maximo mensual.")
        remuneraciones_12 = [as_decimal(total_ultimo) / Decimal("12")] * 12
    else:
        note("Ingrese cada remuneracion mensual de los ultimos 60 meses, en orden cronologico.")
        labels = month_labels(fecha_salida, 60)
        df = pd.DataFrame({"Periodo": labels, "Remuneracion": [0.0] * 60})
        edited = st.data_editor(
            df,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Remuneracion": st.column_config.NumberColumn(min_value=0.0, step=10.0)
            },
            use_container_width=True,
        )
        month_values = [as_decimal(value) for value in edited["Remuneracion"].tolist()]
        remuneraciones_50 = split_annual_totals(month_values)
        remuneraciones_12 = month_values[-12:]

    advanced = st.expander("Parametros avanzados")
    with advanced:
        use_manual_age = st.checkbox("Ingresar edad de renta manual")
        note("Active solo si necesita corregir manualmente la edad usada para C1/C2.")
        edad_manual = (
            st.number_input("Edad de renta", min_value=1, max_value=120, value=52)
            if use_manual_age
            else None
        )
        if use_manual_age:
            note("Coloque la edad exacta que se debe usar para consultar los coeficientes.")
        use_manual_service = st.checkbox("Ingresar tiempo de servicio manual")
        note("Active si desea reemplazar el calculo automatico entre fecha de ingreso y salida.")
        service_manual = (
            st.number_input("Tiempo de servicio", min_value=0.0, value=25.0, step=0.01)
            if use_manual_service
            else None
        )
        if use_manual_service:
            note("Coloque los anos de servicio con decimales, por ejemplo 34.22.")
        min_year = min(store.available_global_years)
        max_year = max(store.available_global_years)
        default_c2_year = min(max(fecha_salida.year, min_year), max_year)
        anio_c2 = st.number_input(
            "Anio de coeficiente global C2",
            min_value=min_year,
            max_value=max_year,
            value=default_c2_year,
            step=1,
        )
        note("Seleccione el anio de la tabla C2; normalmente coincide con el anio de salida.")
        note("Tablas cargadas: 2016 a 2026. La tabla PDF 2021 disponible llega hasta edad 79; para edad mayor use C2 manual.")
        manual_c2_enabled = st.checkbox("Ingresar C2 manual")
        note("Active si el anio de salida no esta cargado o si tiene una tabla oficial mas reciente.")
        manual_c2 = (
            st.number_input(
                "Coeficiente C2 manual",
                min_value=0.0,
                value=0.0,
                step=0.000001,
                format="%.12f",
            )
            if manual_c2_enabled
            else None
        )
        if manual_c2_enabled:
            note("Copie el coeficiente global de la tabla oficial segun edad, sexo y anio.")
        notas = st.text_area("Notas para el informe")
        note("Agregue observaciones del caso, documentos revisados o criterio aplicado.")

    submitted = st.form_submit_button("Calcular")


if submitted:
    try:
        access_status = validate_access(access_code, identificacion, trabajador)
        if not access_status.allowed:
            raise ValueError(access_status.message)

        input_data = {
            "trabajador": trabajador,
            "identificacion": identificacion,
            "empleador": empleador,
            "cargo": cargo,
            "fecha_nacimiento": fecha_nacimiento,
            "fecha_ingreso": fecha_ingreso,
            "fecha_salida": fecha_salida,
            "sexo": sexo,
            "remuneraciones_ultimos_5": remuneraciones_50,
            "remuneraciones_ultimo_12": remuneraciones_12,
            "fondos_reserva_derecho": as_decimal(fondos_reserva_derecho),
            "fondos_reserva_pagados": as_decimal(fondos_reserva_pagados),
            "aportes_patronales_pagados": as_decimal(aportes_patronales),
            "doble_jubilacion": doble_jubilacion,
            "despido_intempestivo": despido_intempestivo,
            "remuneracion_sectorial": as_decimal(remuneracion_sectorial),
            "decimocuarta_remuneracion": as_decimal(decimocuarta),
            "anio_coeficiente_global": int(anio_c2),
            "coeficiente_global_manual": as_decimal(manual_c2) if manual_c2_enabled else None,
            "edad_renta_manual": int(edad_manual) if use_manual_age else None,
            "tiempo_servicio_manual": as_decimal(service_manual) if use_manual_service else None,
            "notas": notas,
        }
        available_fields = {field.name for field in fields(CalculationInput)}
        if "decimotercera_remuneracion" in available_fields:
            input_data["decimotercera_remuneracion"] = (
                as_decimal(decimotercera) if as_decimal(decimotercera) > 0 else None
            )
        entrada = CalculationInput(**input_data)
        access_status = assign_code_to_worker(access_code, identificacion, trabajador)
        if not access_status.allowed:
            raise ValueError(access_status.message)
        result = calculate_jubilacion(entrada, store)
    except Exception as exc:
        st.error(str(exc))
    else:
        if result.advertencias:
            for warning in result.advertencias:
                st.warning(warning)

        recommended = result.recomendado
        c1, c2, c3 = st.columns(3)
        c1.metric("Pension mensual recomendada", usd(recommended.pension_mensual))
        c2.metric("Fondo global recomendado", usd(recommended.fondo_global))
        c3.metric("Tiempo de servicio", f"{result.tiempo_servicio} anos")

        rows = []
        for scenario in result.escenarios:
            rows.append(
                {
                    "Escenario": scenario.nombre,
                    "Criterio aplicado": scenario.descripcion,
                    "Pension calculada": usd(scenario.pension_mens_calculada),
                    "Pension aplicada": usd(scenario.pension_mensual),
                    "Limite": scenario.limite_aplicado,
                    "Decimotercera": usd(scenario.decimotercera),
                    "Decimocuarta": usd(scenario.decimocuarta),
                    "Fondo global calculado": usd(scenario.fondo_global_calculado),
                    "Minimo fondo global": usd(scenario.minimo_fondo_global),
                    "Fondo global aplicado": usd(scenario.fondo_global),
                    "C1": str(scenario.coeficiente_c1),
                    "C2": str(scenario.coeficiente_global.coeficiente),
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if access_status.is_master:
            st.success(f"{access_status.message} Puede generar informes sin limite.")
        else:
            st.success(
                f"{access_status.message} Informes usados: {access_status.reports_used}. "
                f"Informes restantes para {access_status.worker_label}: {access_status.reports_remaining}."
            )
        st.info(
            "Base jurisprudencial: Resolucion CNJ No. 16-2025. El fondo de reserva "
            "integra el haber individual y la rebaja admisible en el escenario "
            "recomendado corresponde a fondos de reserva ya pagados/depositados. "
            "El escenario con aportes patronales se conserva solo como referencia "
            "comparativa frente al Excel/criterios anteriores."
        )

        downloads_disabled = (not access_status.is_master) and access_status.reports_remaining <= 0
        st.download_button(
            "Descargar Excel",
            data=build_excel_report(result),
            file_name="informe_jubilacion_patronal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=downloads_disabled,
            on_click=register_report_download,
            args=(access_code, identificacion, trabajador, "excel"),
        )
        st.download_button(
            "Descargar calculo en PDF",
            data=build_pdf_report(result),
            file_name="informe_jubilacion_patronal.pdf",
            mime="application/pdf",
            disabled=downloads_disabled,
            on_click=register_report_download,
            args=(access_code, identificacion, trabajador, "pdf"),
        )


st.markdown(
    """
    <style>
      .ahil-whatsapp-widget {
        position: fixed;
        right: 22px;
        bottom: 28px;
        z-index: 999999;
        display: flex;
        align-items: flex-end;
        gap: 10px;
        font-family: Arial, sans-serif;
      }
      .ahil-whatsapp-card {
        width: 238px;
        padding: 12px 14px 11px;
        border: 1px solid rgba(15, 76, 129, 0.18);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.96);
        color: #12233d;
        box-shadow: 0 14px 34px rgba(15, 76, 129, 0.18);
        font-size: 13px;
        line-height: 1.28;
      }
      .ahil-whatsapp-card strong {
        display: block;
        color: #0f2748;
        font-size: 13px;
        margin-bottom: 4px;
      }
      .ahil-whatsapp-card span {
        display: block;
      }
      .ahil-contact-name {
        color: #0f2748;
        font-size: 12.5px;
        font-weight: 700;
        margin-top: 8px;
      }
      .ahil-contact-title {
        color: #4e6c8b;
        font-size: 12px;
        margin-top: 1px;
      }
      .ahil-whatsapp-button {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: linear-gradient(145deg, #36e275 0%, #0ebd52 100%);
        color: #ffffff !important;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none !important;
        box-shadow: 0 14px 30px rgba(37, 211, 102, 0.38);
        border: 3px solid #ffffff;
        transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
      }
      .ahil-whatsapp-button:hover {
        background: linear-gradient(145deg, #42ec82 0%, #0fac4b 100%);
        transform: translateY(-1px);
        box-shadow: 0 16px 34px rgba(37, 211, 102, 0.44);
      }
      .ahil-whatsapp-icon {
        width: 36px;
        height: 36px;
        display: block;
      }
      @media (max-width: 760px) {
        .ahil-whatsapp-widget {
          right: 16px;
          bottom: 18px;
        }
        .ahil-whatsapp-card {
          display: none;
        }
      }
    </style>
    <div class="ahil-whatsapp-widget">
      <div class="ahil-whatsapp-card">
        <strong>Atencion directa AHIL Legal Tech</strong>
        Si tiene dudas sobre el calculo, puede escribirme por WhatsApp.
        <span class="ahil-contact-name">Ing. Pablo Ronquillo</span>
        <span class="ahil-contact-title">Abg. Msc.</span>
      </div>
      <a
        class="ahil-whatsapp-button"
        href="https://wa.me/593986658162?text=Hola%20Ing.%20Pablo%20Ronquillo%2C%20tengo%20una%20consulta%20sobre%20la%20calculadora%20de%20Jubilacion%20Patronal."
        target="_blank"
        rel="noopener noreferrer"
        title="Chatear por WhatsApp"
        aria-label="Chatear por WhatsApp con Pablo Ronquillo"
      >
        <svg class="ahil-whatsapp-icon" viewBox="0 0 32 32" aria-hidden="true">
          <path fill="#ffffff" d="M16.04 3.2C9.07 3.2 3.4 8.83 3.4 15.75c0 2.25.6 4.44 1.73 6.35L3.2 29l7.07-1.86a12.7 12.7 0 0 0 6.03 1.53h.01c6.97 0 12.64-5.63 12.64-12.55 0-3.35-1.31-6.5-3.7-8.87A12.6 12.6 0 0 0 16.04 3.2Zm.01 23.34h-.01a10.5 10.5 0 0 1-5.34-1.46l-.38-.23-4.19 1.1 1.12-4.06-.25-.41a10.3 10.3 0 0 1-1.58-5.48c0-5.75 4.72-10.42 10.53-10.42 2.81 0 5.45 1.09 7.44 3.05a10.33 10.33 0 0 1 3.09 7.37c0 5.74-4.72 10.42-10.53 10.42Zm5.78-7.8c-.31-.16-1.85-.91-2.14-1.01-.29-.11-.5-.16-.71.16-.21.31-.82 1.01-1 .1-.18.21-.37.23-.68.08-.31-.16-1.31-.48-2.5-1.53a9.3 9.3 0 0 1-1.73-2.15c-.18-.31-.02-.48.14-.64.14-.14.31-.37.47-.55.16-.18.21-.31.31-.52.1-.21.05-.39-.03-.55-.08-.16-.71-1.7-.97-2.33-.26-.62-.52-.53-.71-.54h-.6c-.21 0-.55.08-.84.39-.29.31-1.1 1.07-1.1 2.61 0 1.54 1.13 3.03 1.29 3.24.16.21 2.23 3.38 5.41 4.74.76.32 1.35.51 1.81.66.76.24 1.45.21 1.99.13.61-.09 1.85-.75 2.11-1.48.26-.73.26-1.36.18-1.48-.08-.13-.29-.21-.61-.37Z"/>
        </svg>
      </a>
    </div>
    <div style="margin-top:32px;border-top:1px solid #d0d7de;padding-top:12px;
    color:#536471;font-size:13px;text-align:center;">
      <strong>Ing. Pablo Ronquillo</strong><br>
      Abg. Msc. | AHIL Legal Tech | Celular: 0986658162 | Quito - Ecuador
    </div>
    """,
    unsafe_allow_html=True,
)
