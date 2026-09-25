"""Pruebas de las utilidades compartidas."""
import pytest
from django.core.exceptions import ValidationError

from apps.common.validators import calcular_dv, limpiar_rut, validar_rut


def test_limpiar_rut_quita_puntos_y_espacios():
    assert limpiar_rut("12.345.678-5") == "12345678-5"


@pytest.mark.parametrize(
    "numero,dv",
    [(12345678, "5"), (11111111, "1"), (20221980, "2")],
)
def test_calcular_dv(numero, dv):
    assert calcular_dv(numero) == dv


def test_validar_rut_acepta_rut_valido():
    validar_rut("12.345.678-5")


def test_validar_rut_rechaza_dv_incorrecto():
    with pytest.raises(ValidationError):
        validar_rut("12345678-9")


def test_validar_rut_rechaza_formato_invalido():
    with pytest.raises(ValidationError):
        validar_rut("abc")
