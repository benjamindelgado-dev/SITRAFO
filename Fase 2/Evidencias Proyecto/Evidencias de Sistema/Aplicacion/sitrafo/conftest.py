"""
Configuracion comun de las pruebas.

Ninguna prueba debe llamar a un servicio externo real: el resultado
dependeria de la red y ensuciaria el registro de integraciones. Si una prueba
no simula explicitamente la llamada (patch de requests.get / requests.post),
la red queda bloqueada y el cliente recibe un error de conexion, que es
justamente el caso de degradacion controlada (RF-INT-03).
"""
from unittest.mock import patch

import pytest
from requests.exceptions import ConnectionError as ErrorConexion


@pytest.fixture(autouse=True)
def _sin_red_real():
    def bloquear(*args, **kwargs):
        raise ErrorConexion("Red bloqueada en las pruebas")

    with patch("requests.sessions.Session.request", side_effect=bloquear), \
         patch("time.sleep"):
        yield
