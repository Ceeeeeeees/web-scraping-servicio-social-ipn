"""Pruebas del parser del portal del IPN.

Usan un fragmento de HTML con la estructura real de
InfoServSocListaProgsActivi.do (dos actividades de un prestatario).
"""

from src import config
from src.exporter import consolidar_convocatorias
from src.parser import parsear_ipn

# Fragmento mínimo con la estructura real del portal: el menú lateral
# también usa la clase "tabla" (no debe parsearse) y el contenido tiene
# dos actividades, una con beca y monto y otra sin apoyos.
HTML_EJEMPLO = """
<html><body>
<div class="menu">
  <div class="tabla">
    <div class="filaMenu"><a href="/infoServSoc/RequisitosServSocial.do">Requisitos</a></div>
  </div>
</div>
<div class="contenido">
<div class="tabla">
    <div class="subtitulo">
        Actividad: SERVICIO SOCIAL YMCA-SISTEMAS
    </div>
    <div class="fila"> <b>Vacantes:</b> 4</div>
    <div class="subtitulo2">
        Prestatario : YMCA (401019432)
    </div>
    <div class="fila"><b>Nombre largo:</b> A.C.J. DE LA CIUDAD DE MEXICO YMCA A.C.</div>
    <div class="fila"><b>Nombre del programa:</b> SERVICIO SOCIAL EN SISTEMAS (B000000074)</div>
    <div class="fila">
        <b>Fecha inicio:</b> 16/5/2025 &nbsp;
        <b>Fecha t&eacute;rmino:</b> 24/7/2026
    </div>
    <div class="fila"><b>Objetivo:</b> Contribuir a la formación académica.</div>
    <div class="fila"><b>Domicilio:</b>
        Calle: AV. GRANJAS, Núm. exterior: 618,
        Núm. interior: , Colonia: ANAHUAC,
        Delegación o Municipio: MIGUEL HIDALGO</div>
    <div class="fila"><b>Apoyos:</b>
        BECA ECONÓMICA,&nbsp;
        Monto del Apoyo $ 1,500.00,&nbsp;
        CAPACITACIÓN,&nbsp;
    </div>
    <div class="fila">&nbsp;</div>

    <div class="subtitulo">
        Actividad: SOPORTE TECNICO
    </div>
    <div class="fila"> <b>Vacantes:</b> 2</div>
    <div class="subtitulo2">
        Prestatario : YMCA (401019432)
    </div>
    <div class="fila"><b>Nombre largo:</b> A.C.J. DE LA CIUDAD DE MEXICO YMCA A.C.</div>
    <div class="fila">
        <b>Fecha inicio:</b> 1/1/2030 &nbsp;
        <b>Fecha t&eacute;rmino:</b> 31/12/2030
    </div>
    <div class="fila"><b>Objetivo:</b> Mantenimiento de equipos.</div>
    <div class="fila"><b>Apoyos:</b>
        ASESORÍA,&nbsp;
    </div>
    <div class="fila">
        <b><a href="/infoServSoc/InfoServSocListaPrsttrPerf.do?cvePerfil=36">Regresar</a></b>
    </div>
</div>
</div>
</body></html>
"""


def test_parsear_ipn_extrae_dos_actividades() -> None:
    """El fragmento de ejemplo debe producir dos convocatorias válidas."""
    config.PERFILES_IPN[36] = "ESCOM INGENIERÍA EN SISTEMAS COMPUTACIONALES"
    convocatorias = parsear_ipn(HTML_EJEMPLO)
    assert len(convocatorias) == 2

    primera, segunda = convocatorias

    assert primera["id"] == "ipn-401019432-b000000074-servicio-social-ymca-sistemas"
    assert primera["titulo"] == "SERVICIO SOCIAL YMCA-SISTEMAS"
    assert primera["institucion"] == "A.C.J. DE LA CIUDAD DE MEXICO YMCA A.C."
    assert primera["apoyoEconomico"] is True
    assert primera["monto"] == 1500.0
    assert primera["fechaPublicacion"] == "2025-05-16"
    assert primera["fechaLimite"] == "2026-07-24"
    assert primera["carreras"] == ["ESCOM INGENIERÍA EN SISTEMAS COMPUTACIONALES"]
    assert primera["ubicacion"] == "MIGUEL HIDALGO"
    assert primera["direccion"].startswith("Calle: AV. GRANJAS")
    assert "cvePerfil=36" in primera["url"]
    assert "cvePrsttr=401019432" in primera["url"]

    assert segunda["apoyoEconomico"] is False
    assert segunda["monto"] is None
    # La segunda actividad no trae domicilio
    assert segunda["ubicacion"] is None
    assert segunda["direccion"] is None
    # La segunda actividad inicia en el futuro
    assert segunda["estado"] == "proxima"


def test_consolidar_une_carreras_de_duplicados() -> None:
    """La misma actividad vista desde dos perfiles debe fusionarse."""
    base = {"id": "ipn-1-actividad", "titulo": "ACTIVIDAD"}
    desde_perfil_a = {**base, "carreras": ["Carrera A"]}
    desde_perfil_b = {**base, "carreras": ["Carrera B", "Carrera A"]}

    consolidadas = consolidar_convocatorias([desde_perfil_a, desde_perfil_b])

    assert len(consolidadas) == 1
    assert consolidadas[0]["carreras"] == ["Carrera A", "Carrera B"]
