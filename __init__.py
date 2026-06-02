"""Calculadora local de jubilacion patronal Ecuador."""

from .calculator import CalculationInput, CalculationResult, ScenarioResult, calculate_jubilacion
from .data_loader import CoefficientStore

__all__ = [
    "CalculationInput",
    "CalculationResult",
    "ScenarioResult",
    "calculate_jubilacion",
    "CoefficientStore",
]
