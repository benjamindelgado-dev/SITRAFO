"""Validadores reutilizables."""
import re

from django.core.exceptions import ValidationError


def limpiar_rut(rut: str) -> str:
    """Deja el RUT como 12345678-9, sin puntos ni espacios."""
    return re.sub(r"[.\s]", "", str(rut)).upper()


def calcular_dv(numero: int) -> str:
    """Calcula el digito verificador de un RUT chileno."""
    suma = 0
    multiplicador = 2
    for digito in reversed(str(numero)):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def validar_rut(valor: str) -> None:
    """
    Valida formato y digito verificador de un RUT chileno.

    Da cumplimiento a RF-CLI-02.
    """
    rut = limpiar_rut(valor)
    if not re.fullmatch(r"\d{7,8}-[\dK]", rut):
        raise ValidationError(
            "El RUT debe tener el formato 12345678-9.", code="rut_formato"
        )
    numero, dv = rut.split("-")
    if calcular_dv(int(numero)) != dv:
        raise ValidationError(
            "El digito verificador del RUT no es correcto.", code="rut_dv"
        )
