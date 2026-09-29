# Alcance diferido

Requisitos de la ERS-01 que no se implementan en esta entrega, con su
justificacion. Se declaran de forma explicita como parte de la
repriorizacion del Product Backlog.

| Requisito | Motivo | Mitigacion actual |
|---|---|---|
| RF-SEG-06 (caducidad periodica de contrasenas) | Las guias actuales (NIST SP 800-63B) desaconsejan forzar cambios periodicos sin indicio de compromiso, porque inducen claves mas debiles. | Politica de complejidad, bloqueo temporal por intentos, recuperacion por enlace de un solo uso y restablecimiento por el Administrador. |

Todo el resto de los requisitos funcionales de la ERS-01 esta implementado y
cubierto por pruebas automatizadas.
