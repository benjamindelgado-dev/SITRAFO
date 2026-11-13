"""
Politica de seguridad de contenido (Content-Security-Policy, RNF-03).

Corrige la alerta de OWASP ZAP «Cabecera Content Security Policy (CSP) no
configurada» (H-01 del PPR-01, tarea S3-13). La politica solo admite recursos
del propio sitio: el portal no usa CDN ni fuentes externas y no tiene
JavaScript ni estilos escritos dentro de las plantillas, por lo que no
necesita 'unsafe-inline' ni 'unsafe-eval'.

La unica salida a otro dominio es el envio del formulario de pago, que
redirige a PayPal (form-action).
"""
POLITICA_SITIO = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
    "form-action 'self' https://www.sandbox.paypal.com https://www.paypal.com",
])

# El panel de administracion de Django trae atributos style en algunas de sus
# plantillas; solo ahi se permiten estilos en linea. No es parte del portal
# del cliente ni de la API publica.
POLITICA_ADMIN = POLITICA_SITIO.replace("style-src 'self'", "style-src 'self' 'unsafe-inline'")


class PoliticaSeguridadContenidoMiddleware:
    """Agrega la cabecera Content-Security-Policy a cada respuesta."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        if "Content-Security-Policy" not in respuesta:
            if request.path.startswith("/admin/"):
                respuesta["Content-Security-Policy"] = POLITICA_ADMIN
            else:
                respuesta["Content-Security-Policy"] = POLITICA_SITIO
        return respuesta
