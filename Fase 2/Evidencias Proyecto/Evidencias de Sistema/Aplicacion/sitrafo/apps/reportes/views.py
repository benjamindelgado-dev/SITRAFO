"""API de reportes (RF-REP-01 a RF-REP-06)."""
import datetime

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import CuentaOperativa, PermisoPorRol

from . import exportar
from .servicios import REPORTES


class ReporteView(APIView):
    """
    GET /api/v1/reportes/<tipo>/?desde=AAAA-MM-DD&hasta=AAAA-MM-DD&formato=json|xlsx|pdf

    Por defecto el periodo son los ultimos 90 dias.
    """

    permission_classes = [CuentaOperativa, PermisoPorRol]
    permisos_alternativos = {None: ["reporte.leer"]}
    action = None

    def get(self, request, tipo):
        generador = REPORTES.get(tipo)
        if generador is None:
            return Response({"detalle": f"Reporte desconocido. Opciones: {', '.join(REPORTES)}."},
                            status=status.HTTP_404_NOT_FOUND)
        hoy = timezone.localdate()
        try:
            desde = datetime.date.fromisoformat(request.query_params.get(
                "desde", (hoy - datetime.timedelta(days=90)).isoformat()))
            hasta = datetime.date.fromisoformat(request.query_params.get("hasta", hoy.isoformat()))
        except ValueError:
            return Response({"detalle": "Las fechas deben tener formato AAAA-MM-DD."},
                            status=status.HTTP_400_BAD_REQUEST)
        if desde > hasta:
            return Response({"detalle": "La fecha inicial es posterior a la final."},
                            status=status.HTTP_400_BAD_REQUEST)

        reporte = generador(desde, hasta)
        periodo = f"{desde:%d-%m-%Y} al {hasta:%d-%m-%Y}"
        formato = request.query_params.get("formato", "json")
        nombre = f"SITRAFO-{tipo}-{desde:%Y%m%d}-{hasta:%Y%m%d}"
        if formato == "xlsx":
            respuesta = HttpResponse(
                exportar.a_excel(reporte, periodo),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            respuesta["Content-Disposition"] = f'attachment; filename="{nombre}.xlsx"'
            return respuesta
        if formato == "pdf":
            respuesta = HttpResponse(exportar.a_pdf(reporte, periodo),
                                     content_type="application/pdf")
            respuesta["Content-Disposition"] = f'attachment; filename="{nombre}.pdf"'
            return respuesta
        return Response({**reporte, "periodo": periodo,
                         "filas": [[str(v) if v is not None else "" for v in f]
                                   for f in reporte["filas"]],
                         "totales": [str(v) for v in reporte.get("totales") or []]})
