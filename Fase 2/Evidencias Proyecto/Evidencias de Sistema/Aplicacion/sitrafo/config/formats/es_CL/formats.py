"""
Formato numerico chileno.

Django no trae un formato propio para es-CL y usa el del espanol generico,
que separa los miles con un espacio ("$1 667 042"). En Chile se usa el punto
("$1.667.042") y la coma para los decimales ("40,55 UF"). Los demas formatos
(fechas, horas) se siguen tomando del espanol generico de Django.
"""
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "."
NUMBER_GROUPING = 3
