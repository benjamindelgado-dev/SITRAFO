"""Paginacion de la API."""
from rest_framework.pagination import PageNumberPagination


class Paginacion(PageNumberPagination):
    """
    25 resultados por pagina por defecto. El cliente puede pedir mas con
    ?page_size=N (hasta 500), como hace la aplicacion de escritorio en sus
    listados, para no perder filas cuando hay mas de una pagina.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 500
