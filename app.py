from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from jubilacion import CalculationInput, CoefficientStore, calculate_jubilacion
from jubilacion.calculator import money
from jubilacion.reports import build_excel_report, build_pdf_report


st.set_page_config(
    page_title="AHIL Legal Tech - Jubilacion Patronal",
    layout="wide",
)
st.title("AHIL Legal Tech | Calculadora de Jubilacion Patronal")
st.caption(
    "Herramienta local de consultoria juridica, tributaria y laboral para estimar "
    "pension mensual, fondo global y generar informes Excel/PDF."
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


def usd(value: Decimal) -> str:
    return f"USD {money(value):,.2f}"


with st.form("calculo"):
    left, right = st.columns(2)
    with left:
        trabajador = st.text_input("Nombre del trabajador")
        identificacion = st.text_input("Cedula / identificacion")
        cargo = st.text_input("Cargo")
        sexo = st.selectbox("Sexo para coeficiente global", ["Hombre", "Mujer"])
        fecha_nacimiento = st.date_input("Fecha de nacimiento", value=date(1970, 1, 1))
        fecha_ingreso = st.date_input("Fecha de ingreso", value=date(1990, 1, 1))
        fecha_salida = st.date_input("Fecha de salida", value=date.today())
    with right:
        empleador = st.text_input("Empleador")
        doble_jubilacion = st.checkbox("Tiene doble jubilacion")
        despido_intempestivo = st.checkbox("Despido intempestivo")
        fondos_reserva_derecho = st.number_input(
            "Fondos de reserva causados (A / FRR)", min_value=0.0, step=100.0
        )
        fondos_reserva_pagados = st.number_input(
            "Fondos de reserva pagados/depositados", min_value=0.0, step=100.0
        )
        aportes_patronales = st.number_input(
            "Aportes patronales pagados/depositados", min_value=0.0, step=100.0
        )
        decimocuarta = st.number_input(
            "Decimocuarta remuneracion para fondo global",
            min_value=0.0,
            value=470.0,
            step=10.0,
        )
        remuneracion_sectorial = st.number_input(
            "Remuneracion sectorial vigente al cese",
            min_value=0.0,
            value=470.0,
            step=10.0,
        )

    st.subheader("Remuneraciones")
    modo = st.radio("Modo de ingreso", ["Resumen anual", "Detalle mensual"], horizontal=True)
    remuneraciones_5: list[Decimal]
    remuneraciones_12: list[Decimal] = []
    if modo == "Resumen anual":
        cols = st.columns(5)
        years = list(range(fecha_salida.year - 4, fecha_salida.year + 1))
        remuneraciones_50 = []
        for idx, col in enumerate(cols):
            with col:
                value = st.number_input(
                    f"Total anual {years[idx]}",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    key=f"annual_{idx}",
                )
                remuneraciones_50.append(as_decimal(value))
        total_ultimo = st.number_input(
            "Total remuneracion ultimo anio",
            min_value=0.0,
            value=float(remuneraciones_50[-1]) if remuneraciones_50 else 0.0,
            step=100.0,
        )
        remuneraciones_12 = [as_decimal(total_ultimo) / Decimal("12")] * 12
    else:
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
        edad_manual = (
            st.number_input("Edad de renta", min_value=1, max_value=120, value=52)
            if use_manual_age
            else None
        )
        use_manual_service = st.checkbox("Ingresar tiempo de servicio manual")
        service_manual = (
            st.number_input("Tiempo de servicio", min_value=0.0, value=25.0, step=0.01)
            if use_manual_service
            else None
        )
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
        manual_c2_enabled = st.checkbox("Ingresar C2 manual")
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
        notas = st.text_area("Notas para el informe")

    submitted = st.form_submit_button("Calcular")


if submitted:
    try:
        entrada = CalculationInput(
            trabajador=trabajador,
            identificacion=identificacion,
            empleador=empleador,
            cargo=cargo,
            fecha_nacimiento=fecha_nacimiento,
            fecha_ingreso=fecha_ingreso,
            fecha_salida=fecha_salida,
            sexo=sexo,
            remuneraciones_ultimos_5=remuneraciones_50,
            remuneraciones_ultimo_12=remuneraciones_12,
            fondos_reserva_derecho=as_decimal(fondos_reserva_derecho),
            fondos_reserva_pagados=as_decimal(fondos_reserva_pagados),
            aportes_patronales_pagados=as_decimal(aportes_patronales),
            doble_jubilacion=doble_jubilacion,
            despido_intempestivo=despido_intempestivo,
            remuneracion_sectorial=as_decimal(remuneracion_sectorial),
            decimocuarta_remuneracion=as_decimal(decimocuarta),
            anio_coeficiente_global=int(anio_c2),
            coeficiente_global_manual=as_decimal(manual_c2) if manual_c2_enabled else None,
            edad_renta_manual=int(edad_manual) if use_manual_age else None,
            tiempo_servicio_manual=as_decimal(service_manual) if use_manual_service else None,
            notas=notas,
        )
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
                    "Pension calculada": usd(scenario.pension_mens_calculada),
                    "Pension aplicada": usd(scenario.pension_mensual),
                    "Limite": scenario.limite_aplicado,
                    "Fondo global calculado": usd(scenario.fondo_global_calculado),
                    "Minimo fondo global": usd(scenario.minimo_fondo_global),
                    "Fondo global aplicado": usd(scenario.fondo_global),
                    "C1": str(scenario.coeficiente_c1),
                    "C2": str(scenario.coeficiente_global.coeficiente),
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.download_button(
            "Descargar Excel",
            data=build_excel_report(result),
            file_name="informe_jubilacion_patronal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.download_button(
            "Descargar PDF",
            data=build_pdf_report(result),
            file_name="informe_jubilacion_patronal.pdf",
            mime="application/pdf",
        )
