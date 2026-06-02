from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from textwrap import wrap

from fpdf import FPDF
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .calculator import CalculationResult, ScenarioResult, money


TITLE_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FILL = PatternFill("solid", fgColor="D9EAF7")


def build_excel_report(result: CalculationResult) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Informe"
    _setup_sheet(ws)

    ws["A1"] = "Informe de calculo de Jubilacion Patronal"
    ws["A1"].font = Font(bold=True, color="FFFFFF", size=14)
    ws["A1"].fill = TITLE_FILL
    ws.merge_cells("A1:F1")

    data_rows = [
        ("Trabajador", result.entrada.trabajador),
        ("Identificacion", result.entrada.identificacion),
        ("Empleador", result.entrada.empleador),
        ("Cargo", result.entrada.cargo),
        ("Fecha nacimiento", result.entrada.fecha_nacimiento.isoformat()),
        ("Fecha ingreso", result.entrada.fecha_ingreso.isoformat()),
        ("Fecha salida", result.entrada.fecha_salida.isoformat()),
        ("Edad al determinar renta", result.edad_renta),
        ("Tiempo de servicio", result.tiempo_servicio),
        ("Elegibilidad", result.elegibilidad),
        ("Promedio anual ultimos 5 anos", result.promedio_anual_ultimos_5),
        ("Promedio mensual ultimo anio", result.promedio_mens_ultimo_anio),
    ]
    row = 3
    for label, value in data_rows:
        ws.cell(row, 1, label)
        ws.cell(row, 2, value)
        row += 1

    row += 1
    ws.cell(row, 1, "Escenario recomendado").font = Font(bold=True)
    row += 1
    _write_scenario_summary(ws, row, result.recomendado)

    scenarios = wb.create_sheet("Escenarios")
    _setup_sheet(scenarios)
    _write_scenarios_sheet(scenarios, result)

    inputs = wb.create_sheet("Datos")
    _setup_sheet(inputs)
    _write_inputs_sheet(inputs, result)

    sources = wb.create_sheet("Fuentes")
    _setup_sheet(sources)
    _write_sources_sheet(sources, result)

    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def build_pdf_report(result: CalculationResult) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, _latin("Informe de calculo de Jubilacion Patronal"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(
        0,
        6,
        _latin(
            "Calculo referencial basado en el art. 216 del Codigo del Trabajo, "
            "MDT-2016-0099, Resolucion 07-2021 y tablas de coeficientes disponibles."
        ),
    )
    pdf.ln(2)

    _pdf_section(pdf, "Datos del trabajador")
    for label, value in [
        ("Trabajador", result.entrada.trabajador),
        ("Identificacion", result.entrada.identificacion),
        ("Empleador", result.entrada.empleador),
        ("Cargo", result.entrada.cargo),
        ("Periodo laboral", f"{result.entrada.fecha_ingreso} a {result.entrada.fecha_salida}"),
        ("Edad / servicio", f"{result.edad_renta} anos / {result.tiempo_servicio} anos"),
        ("Elegibilidad", result.elegibilidad),
    ]:
        _pdf_pair(pdf, label, str(value))

    _pdf_section(pdf, "Resumen recomendado")
    _pdf_scenario(pdf, result.recomendado)

    _pdf_section(pdf, "Escenario comparativo")
    _pdf_scenario(pdf, result.escenarios[1])

    if result.advertencias:
        _pdf_section(pdf, "Advertencias")
        for warning in result.advertencias:
            _pdf_multiline(pdf, f"- {warning}")

    _pdf_section(pdf, "Base de calculo")
    _pdf_multiline(
        pdf,
        "Haber individual = fondos de reserva + 5% del promedio anual de los "
        "ultimos 5 anos x tiempo de servicio. Pension mensual = haber ajustado / "
        "coeficiente C1 / 12. Fondo global = C2 x [(pension mensual x 12) + "
        "decimotercera + decimocuarta], validando el minimo legal del 50% de la "
        "remuneracion sectorial por anos de servicio.",
    )

    return pdf.output(dest="S").encode("latin-1")


def _write_scenario_summary(ws, start_row: int, scenario: ScenarioResult) -> None:
    rows = [
        ("Nombre", scenario.nombre),
        ("Pension mensual calculada", money(scenario.pension_mens_calculada)),
        ("Pension mensual aplicada", money(scenario.pension_mensual)),
        ("Limite aplicado", scenario.limite_aplicado),
        ("Fondo global calculado", money(scenario.fondo_global_calculado)),
        ("Minimo fondo global", money(scenario.minimo_fondo_global)),
        ("Fondo global aplicado", money(scenario.fondo_global)),
    ]
    for offset, (label, value) in enumerate(rows):
        ws.cell(start_row + offset, 1, label)
        ws.cell(start_row + offset, 2, value)


def _write_scenarios_sheet(ws, result: CalculationResult) -> None:
    headers = [
        "Escenario",
        "Descuento total",
        "Haber individual",
        "Haber ajustado",
        "C1",
        "Pension calculada",
        "Pension aplicada",
        "Limite",
        "C2",
        "Fondo global calculado",
        "Minimo fondo global",
        "Fondo global aplicado",
    ]
    ws.append(headers)
    _format_header(ws, 1, len(headers))
    for scenario in result.escenarios:
        ws.append(
            [
                scenario.nombre,
                float(scenario.descuento_total),
                float(scenario.haber_individual),
                float(scenario.haber_ajustado),
                float(scenario.coeficiente_c1),
                float(scenario.pension_mens_calculada),
                float(scenario.pension_mensual),
                scenario.limite_aplicado,
                float(scenario.coeficiente_global.coeficiente),
                float(scenario.fondo_global_calculado),
                float(scenario.minimo_fondo_global),
                float(scenario.fondo_global),
            ]
        )


def _write_inputs_sheet(ws, result: CalculationResult) -> None:
    ws.append(["Campo", "Valor"])
    _format_header(ws, 1, 2)
    rows = [
        ("Fondos reserva derecho", result.entrada.fondos_reserva_derecho),
        ("Fondos reserva pagados", result.entrada.fondos_reserva_pagados),
        ("Aportes patronales pagados", result.entrada.aportes_patronales_pagados),
        ("Decimocuarta", result.entrada.decimocuarta_remuneracion),
        ("Remuneracion sectorial", result.entrada.remuneracion_sectorial),
        ("Doble jubilacion", "Si" if result.entrada.doble_jubilacion else "No"),
        ("Despido intempestivo", "Si" if result.entrada.despido_intempestivo else "No"),
    ]
    for row in rows:
        ws.append(row)
    ws.append([])
    ws.append(["Remuneraciones ultimos 5 anos", "Valor"])
    _format_header(ws, ws.max_row, 2)
    for idx, value in enumerate(result.entrada.remuneraciones_ultimos_5, start=1):
        ws.append([f"Anio {idx}", float(value)])


def _write_sources_sheet(ws, result: CalculationResult) -> None:
    ws.append(["Fuente", "Detalle"])
    _format_header(ws, 1, 2)
    ws.append(["C1", result.coeficiente_c1_fuente])
    for scenario in result.escenarios:
        ws.append([f"C2 {scenario.nombre}", scenario.coeficiente_global.fuente])
    ws.append(["Resolucion 07-2021", "Limite maximo: promedio mensual del ultimo anio."])
    ws.append(["MDT-2016-0099", "Formula mensual y formula referencial de fondo global."])
    ws.append(["Resolucion 16-2025", "Escenario recomendado descuenta fondos de reserva."])
    ws.append(["Resolucion 04-2026", "Fondo global segun acuerdos ministeriales vigentes al cese."])


def _setup_sheet(ws) -> None:
    ws.freeze_panes = "A2"
    for idx in range(1, 12):
        ws.column_dimensions[get_column_letter(idx)].width = 22
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def _format_header(ws, row: int, columns: int) -> None:
    for col in range(1, columns + 1):
        cell = ws.cell(row, col)
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="top")


def _pdf_section(pdf: FPDF, title: str) -> None:
    pdf.ln(4)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, _latin(title), ln=True)
    pdf.set_font("Arial", "", 10)


def _pdf_pair(pdf: FPDF, label: str, value: str) -> None:
    pdf.set_font("Arial", "B", 9)
    pdf.cell(45, 6, _latin(label + ":"), border=0)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 6, _latin(value))


def _pdf_scenario(pdf: FPDF, scenario: ScenarioResult) -> None:
    for label, value in [
        ("Escenario", scenario.nombre),
        ("Pension calculada", _usd(scenario.pension_mens_calculada)),
        ("Pension aplicada", _usd(scenario.pension_mensual)),
        ("Fondo global calculado", _usd(scenario.fondo_global_calculado)),
        ("Minimo fondo global", _usd(scenario.minimo_fondo_global)),
        ("Fondo global aplicado", _usd(scenario.fondo_global)),
    ]:
        _pdf_pair(pdf, label, value)


def _pdf_multiline(pdf: FPDF, text: str) -> None:
    for line in wrap(text, 105):
        pdf.multi_cell(0, 5, _latin(line))


def _usd(value: Decimal) -> str:
    return f"USD {money(value):,.2f}"


def _latin(text: str) -> str:
    return (
        str(text)
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )
