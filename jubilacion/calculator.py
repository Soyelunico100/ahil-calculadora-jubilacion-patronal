from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, getcontext

from .data_loader import CoefficientStore, GlobalCoefficient

getcontext().prec = 28

MONEY = Decimal("0.01")
PERCENT = Decimal("0.05")
TWEL = Decimal("12")


def D(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or "0"))


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass
class CalculationInput:
    trabajador: str
    identificacion: str
    empleador: str
    cargo: str
    fecha_nacimiento: date
    fecha_ingreso: date
    fecha_salida: date
    sexo: str
    remuneraciones_ultimos_5: list[Decimal]
    fondos_reserva_derecho: Decimal
    fondos_reserva_pagados: Decimal
    aportes_patronales_pagados: Decimal
    doble_jubilacion: bool = False
    despido_intempestivo: bool = False
    decimotercera_remuneracion: Decimal | None = None
    remuneracion_sectorial: Decimal = Decimal("0")
    decimocuarta_remuneracion: Decimal = Decimal("0")
    anio_coeficiente_global: int | None = None
    coeficiente_global_manual: Decimal | None = None
    edad_renta_manual: int | None = None
    tiempo_servicio_manual: Decimal | None = None
    notas: str = ""
    remuneraciones_ultimo_12: list[Decimal] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.fecha_salida < self.fecha_ingreso:
            raise ValueError("La fecha de salida no puede ser anterior a la fecha de ingreso.")
        if self.fecha_salida < self.fecha_nacimiento:
            raise ValueError("La fecha de salida no puede ser anterior a la fecha de nacimiento.")
        if not self.remuneraciones_ultimos_5:
            raise ValueError("Ingrese al menos una remuneracion para los ultimos 5 anos.")
        if len(self.remuneraciones_ultimo_12) not in {0, 12}:
            raise ValueError("El detalle del ultimo anio debe contener 12 valores.")

    @property
    def promedio_anual_ultimos_5(self) -> Decimal:
        return sum((D(value) for value in self.remuneraciones_ultimos_5), Decimal("0")) / Decimal("5")

    @property
    def total_ultimo_anio(self) -> Decimal:
        if self.remuneraciones_ultimo_12:
            return sum((D(value) for value in self.remuneraciones_ultimo_12), Decimal("0"))
        return sum((D(value) for value in self.remuneraciones_ultimos_5[-1:]), Decimal("0"))

    @property
    def promedio_mens_ultimo_anio(self) -> Decimal:
        return self.total_ultimo_anio / TWEL

    @property
    def edad_renta(self) -> int:
        if self.edad_renta_manual is not None:
            return int(self.edad_renta_manual)
        return completed_years(self.fecha_nacimiento, self.fecha_salida)

    @property
    def tiempo_servicio(self) -> Decimal:
        if self.tiempo_servicio_manual is not None:
            return D(self.tiempo_servicio_manual)
        days = (self.fecha_salida - self.fecha_ingreso).days
        return (Decimal(days) / Decimal("365.25")).quantize(Decimal("0.01"))

    @property
    def anio_c2(self) -> int:
        return self.anio_coeficiente_global or self.fecha_salida.year


@dataclass(frozen=True)
class ScenarioResult:
    nombre: str
    descripcion: str
    descuento_total: Decimal
    haber_individual: Decimal
    haber_ajustado: Decimal
    coeficiente_c1: Decimal
    pension_mens_calculada: Decimal
    pension_mensual: Decimal
    minimo_mens: Decimal
    maximo_mens: Decimal
    limite_aplicado: str
    coeficiente_global: GlobalCoefficient
    decimotercera: Decimal
    decimocuarta: Decimal
    fondo_global_calculado: Decimal
    minimo_fondo_global: Decimal
    fondo_global: Decimal


@dataclass(frozen=True)
class CalculationResult:
    entrada: CalculationInput
    edad_renta: int
    tiempo_servicio: Decimal
    elegible: bool
    elegibilidad: str
    promedio_anual_ultimos_5: Decimal
    promedio_mens_ultimo_anio: Decimal
    coeficiente_c1_fuente: str
    escenarios: list[ScenarioResult]
    advertencias: list[str]

    @property
    def recomendado(self) -> ScenarioResult:
        return self.escenarios[0]


def calculate_jubilacion(
    entrada: CalculationInput,
    store: CoefficientStore | None = None,
) -> CalculationResult:
    store = store or CoefficientStore()
    warnings: list[str] = []
    service = entrada.tiempo_servicio
    eligible, eligibility = eligibility_message(service, entrada.despido_intempestivo)
    if not eligible:
        warnings.append(eligibility)

    c1 = store.get_c1(entrada.edad_renta)
    c2 = store.get_global(
        anio=entrada.anio_c2,
        edad=entrada.edad_renta,
        sexo=entrada.sexo,
        manual=entrada.coeficiente_global_manual,
    )

    haber_individual = D(entrada.fondos_reserva_derecho) + (
        entrada.promedio_anual_ultimos_5 * PERCENT * service
    )
    minimum_month = Decimal("20") if entrada.doble_jubilacion else Decimal("30")
    maximum_month = entrada.promedio_mens_ultimo_anio
    if maximum_month < minimum_month:
        warnings.append(
            "El promedio mensual del ultimo anio es menor al minimo legal; revise los datos."
        )

    scenarios = [
        (
            "Solo fondos de reserva",
            "Criterio recomendado por Resolucion CNJ 16-2025: el empleador rebaja "
            "solo fondos de reserva pagados, entregados o depositados; no rebaja "
            "aportes patronales en aplicacion del principio de favorabilidad.",
            D(entrada.fondos_reserva_pagados),
        ),
        (
            "Fondos de reserva + aportes",
            "Escenario comparativo historico/Excel: descuenta fondos de reserva y "
            "aportes patronales. Se muestra solo para contraste frente al criterio "
            "jurisprudencial obligatorio actual.",
            D(entrada.fondos_reserva_pagados) + D(entrada.aportes_patronales_pagados),
        ),
    ]
    results = [
        _build_scenario(
            nombre=nombre,
            descripcion=descripcion,
            descuento_total=descuento,
            haber_individual=haber_individual,
            coeficiente_c1=c1.coeficiente,
            coeficiente_global=c2,
            minimum_month=minimum_month,
            maximum_month=maximum_month,
            decimocuarta=D(entrada.decimocuarta_remuneracion),
            decimotercera_manual=entrada.decimotercera_remuneracion,
            remuneracion_sectorial=D(entrada.remuneracion_sectorial),
            service=service,
        )
        for nombre, descripcion, descuento in scenarios
    ]
    return CalculationResult(
        entrada=entrada,
        edad_renta=entrada.edad_renta,
        tiempo_servicio=service,
        elegible=eligible,
        elegibilidad=eligibility,
        promedio_anual_ultimos_5=entrada.promedio_anual_ultimos_5,
        promedio_mens_ultimo_anio=maximum_month,
        coeficiente_c1_fuente=c1.fuente,
        escenarios=results,
        advertencias=warnings,
    )


def _build_scenario(
    *,
    nombre: str,
    descripcion: str,
    descuento_total: Decimal,
    haber_individual: Decimal,
    coeficiente_c1: Decimal,
    coeficiente_global: GlobalCoefficient,
    minimum_month: Decimal,
    maximum_month: Decimal,
    decimotercera_manual: Decimal | None,
    decimocuarta: Decimal,
    remuneracion_sectorial: Decimal,
    service: Decimal,
) -> ScenarioResult:
    haber_ajustado = haber_individual - descuento_total
    pension_calc = haber_ajustado / coeficiente_c1 / TWEL
    pension_limited, limit_name = apply_month_limits(pension_calc, minimum_month, maximum_month)
    decimo13 = D(decimotercera_manual) if decimotercera_manual is not None else pension_limited
    fondo_global_calculado = coeficiente_global.coeficiente * (
        (pension_limited * TWEL) + decimo13 + decimocuarta
    )
    minimum_global = remuneracion_sectorial * Decimal("0.50") * service
    fondo_global = max(fondo_global_calculado, minimum_global)
    return ScenarioResult(
        nombre=nombre,
        descripcion=descripcion,
        descuento_total=descuento_total,
        haber_individual=haber_individual,
        haber_ajustado=haber_ajustado,
        coeficiente_c1=coeficiente_c1,
        pension_mens_calculada=pension_calc,
        pension_mensual=pension_limited,
        minimo_mens=minimum_month,
        maximo_mens=maximum_month,
        limite_aplicado=limit_name,
        coeficiente_global=coeficiente_global,
        decimotercera=decimo13,
        decimocuarta=decimocuarta,
        fondo_global_calculado=fondo_global_calculado,
        minimo_fondo_global=minimum_global,
        fondo_global=fondo_global,
    )


def apply_month_limits(value: Decimal, minimum: Decimal, maximum: Decimal) -> tuple[Decimal, str]:
    if maximum > Decimal("0") and value > maximum:
        return maximum, "maximo mensual ultimo anio"
    if value < minimum:
        return minimum, "minimo legal"
    return value, "sin ajuste"


def completed_years(birth: date, end: date) -> int:
    age = end.year - birth.year - ((end.month, end.day) < (birth.month, birth.day))
    return age


def eligibility_message(service: Decimal, despido_intempestivo: bool) -> tuple[bool, str]:
    if service >= Decimal("25"):
        return True, "Cumple 25 o mas anos de servicio."
    if service > Decimal("20") and despido_intempestivo:
        return True, "Cumple jubilacion proporcional por despido intempestivo."
    return (
        False,
        "No cumple 25 o mas o proporcional por despido intempestivo segun los datos ingresados.",
    )
