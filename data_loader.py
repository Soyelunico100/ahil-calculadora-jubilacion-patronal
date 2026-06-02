from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class C1Coefficient:
    edad: int
    coeficiente: Decimal
    fuente: str


@dataclass(frozen=True)
class GlobalCoefficient:
    anio: int
    tasa_descuento: Decimal
    edad: int
    sexo: str
    coeficiente: Decimal
    fuente: str


class CoefficientStore:
    """CSV-backed coefficient lookup."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or DATA_DIR
        self._c1 = self._load_c1()
        self._global = self._load_global()

    @property
    def available_global_years(self) -> list[int]:
        return sorted({key[0] for key in self._global})

    @property
    def c1_age_range(self) -> tuple[int | None, int | None]:
        if not self._c1:
            return None, None
        edades = self._c1.keys()
        return min(edades), max(edades)

    def _load_c1(self) -> dict[int, C1Coefficient]:
        path = self.data_dir / "coeficientes_c1.csv"
        rows: dict[int, C1Coefficient] = {}
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                edad = int(row["edad"])
                rows[edad] = C1Coefficient(
                    edad=edad,
                    coeficiente=Decimal(row["coeficiente"]),
                    fuente=row["fuente"],
                )
        return rows

    def _load_global(self) -> dict[tuple[int, int, str], GlobalCoefficient]:
        path = self.data_dir / "coeficientes_globales.csv"
        rows: dict[tuple[int, int, str], GlobalCoefficient] = {}
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                anio = int(row["anio"])
                edad = int(row["edad"])
                sexo = normalize_sex(row["sexo"])
                rows[(anio, edad, sexo)] = GlobalCoefficient(
                    anio=anio,
                    tasa_descuento=Decimal(row["tasa_descuento"]),
                    edad=edad,
                    sexo=sexo,
                    coeficiente=Decimal(row["coeficiente"]),
                    fuente=row["fuente"],
                )
        return rows

    def get_c1(self, edad: int) -> C1Coefficient:
        try:
            return self._c1[edad]
        except KeyError as exc:
            minimo, maximo = self.c1_age_range
            raise ValueError(
                f"No existe coeficiente C1 para edad {edad}. "
                f"Rango disponible: {minimo}-{maximo}."
            ) from exc

    def get_global(
        self,
        *,
        anio: int,
        edad: int,
        sexo: str,
        manual: Decimal | None = None,
        fuente_manual: str = "Coeficiente ingresado manualmente",
    ) -> GlobalCoefficient:
        sexo_norm = normalize_sex(sexo)
        if manual is not None:
            return GlobalCoefficient(
                anio=anio,
                tasa_descuento=Decimal("0"),
                edad=edad,
                sexo=sexo_norm,
                coeficiente=manual,
                fuente=fuente_manual,
            )
        try:
            return self._global[(anio, edad, sexo_norm)]
        except KeyError as exc:
            disponibles = ", ".join(str(year) for year in self.available_global_years)
            raise ValueError(
                f"No existe coeficiente global C2 para anio {anio}, edad {edad}, sexo {sexo_norm}. "
                f"Anios disponibles: {disponibles}. Puede ingresar C2 manual."
            ) from exc


def normalize_sex(value: str) -> str:
    text = value.strip().lower()
    if text in {"h", "hombre", "masculino", "m"}:
        # In this app "M" can be ambiguous. Streamlit passes full labels.
        if text == "m":
            return "Mujer"
        return "Hombre"
    if text in {"mujer", "f", "femenino"}:
        return "Mujer"
    raise ValueError("Sexo debe ser Hombre o Mujer.")
