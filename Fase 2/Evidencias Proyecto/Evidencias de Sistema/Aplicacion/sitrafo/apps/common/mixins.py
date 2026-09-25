"""Mixins compartidos por los viewsets de la API."""


class FiltradoPorClienteMixin:
    """
    Restringe el conjunto de datos a los documentos del propio cliente.

    Da cumplimiento a RN-16. El filtro se aplica en la capa de servicio y no
    en la plantilla, de modo que rija cualquiera sea la interfaz que consuma
    la API. El atributo campo_cliente indica la ruta al cliente desde el
    modelo de la vista.
    """

    campo_cliente = "cliente"

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario = self.request.user

        if usuario.is_superuser or usuario.es_interno:
            return queryset

        if usuario.cliente_id is None:
            return queryset.none()

        return queryset.filter(**{self.campo_cliente: usuario.cliente_id})
