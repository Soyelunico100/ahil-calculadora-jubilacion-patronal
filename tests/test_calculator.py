from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from jubilacion import CalculationInput, CoefficientStore, calculate_jubilacion
from jubilacion.reports import build_excel_report, build_pdf_report


def excel_case() -> CalculationInput:
    return CalculationInput(
        trabajador="Caso Excel",
        identificacion="0000000000",
        empleador="Empresa",
        cargo="Cargo",
        fecha_nacimiento=date(1970, 1, 1),
        fecha_ingreso=date(1990, 1, 1),
        fecha_salida=date(2022, 1, 1),
        sexo="Hombre",
        remuneraciones_ultimos_5=[
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("92434.89"),
        ],
        remuneraciones_ultimo_12=[Decimal("10000")] * 12,
        fondos_reserva_derecho=Decimal("17290.13"),
        fondos_reserva_pagados=Decimal("17290.13"),
        aportes_patronales_pagados=Decimal("28838.89"),
        remuneracion_sectorial=Decimal("400"),
        decimocuarta_remuneracion=Decimal("400"),
        edad_renta_manual=52,
        tiempo_servicio_manual=Decimal("34.22"),
        coeficiente_global_manual=Decimal("13.5778394834333"),
    )


class CalculatorTests(unittest.TestCase):
    def test_regression_against_excel_values(self) -> None:
        result = calculate_jubilacion(excel_case())
        solo_fondos = result.escenarios[0]
        fondos_aportes = result.escenarios[1]

        self.assertAlmostEqual(float(solo_fondos.pension_mens_calculada), 304.5774342, places=6)
        self.assertAlmostEqual(float(fondos_aportes.pension_mens_calculada), 26.88737673, places=6)
        self.assertEqual(fondos_aportes.pension_mensual, Decimal("30"))
        self.assertAlmostEqual(float(solo_fondos.fondo_global_calculado), 59192.68145, places=4)

    def test_coefficient_store_has_2026_official_table(self) -> None:
        store = CoefficientStore()
        coefficient = store.get_global(anio=2026, edad=40, sexo="Mujer")
        self.assertEqual(coefficient.coeficiente, Decimal("14.3056897074653"))

    def test_coefficient_store_has_pdf_tables_2016_to_2026(self) -> None:
        store = CoefficientStore()
        self.assertEqual(store.available_global_years, list(range(2016, 2027)))
        coefficient_2016 = store.get_global(anio=2016, edad=39, sexo="Hombre")
        coefficient_2021 = store.get_global(anio=2021, edad=79, sexo="Mujer")
        self.assertEqual(coefficient_2016.coeficiente, Decimal("15.1257705934602"))
        self.assertEqual(coefficient_2021.coeficiente, Decimal("5.3930926574543"))

    def test_reports_are_generated(self) -> None:
        result = calculate_jubilacion(excel_case())
        xlsx = build_excel_report(result)
        pdf = build_pdf_report(result)
        self.assertTrue(xlsx.startswith(b"PK"))
        self.assertTrue(pdf.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
