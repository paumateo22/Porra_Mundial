import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from curl_cffi import requests

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# ====================================================================
# IDs DEL MUNDIAL 2026 (SofaScore)
# ====================================================================
UNIQUE_TOURNAMENT_ID = 16
SEASON_ID = 58210  # ID actual de SofaScore para 2026. Revisar días antes del torneo.

# Zona horaria de España en verano (junio/julio 2026) = UTC+2
# Nuestros ISOs están en hora local española, SofaScore devuelve UTC puro.
# Al convertir nuestros ISOs a timestamp restamos este offset para comparar contra UTC.
OFFSET_LOCAL_UTC = timedelta(hours=2)

# Tolerancia para el matching por fecha: ±15 minutos
TOLERANCIA_FECHA_SEGUNDOS = 900

# Mapeo exacto de roundInfo_name de SofaScore → clave interna
# Usamos comparación EXACTA (== en minúsculas) para evitar falsos positivos
# como "semifinals" conteniendo "final".
RONDA_A_FASE = {
    "round of 32":      "dieciseisavos",   # por si 2026 usa este nombre
    "round of 16":      "octavos",
    "quarterfinals":    "cuartos",
    "semifinals":       "semifinales",
    "match for 3rd place": "tercer_puesto",
    "final":            "final",
}

# Diccionario traductor inglés → español para equipos en eliminatorias.
# Solo se usa en eliminatorias; en grupos solo actualizamos goles/estado.
# TODO: completar/ajustar cuando comiencen los partidos del Mundial 2026
# y veamos exactamente cómo escribe SofaScore cada nombre.
TRADUCCIONES = {
    # Confirmados en test 2022
    "Argentina":            "Argentina",
    "Australia":            "Australia",
    "Belgium":              "Bélgica",
    "Brazil":               "Brasil",
    "Canada":               "Canadá",
    "Croatia":              "Croacia",
    "Denmark":              "Dinamarca",
    "Ecuador":              "Ecuador",
    "England":              "Inglaterra",
    "France":               "Francia",
    "Germany":              "Alemania",
    "Ghana":                "Ghana",
    "Iran":                 "Irán",
    "Japan":                "Japón",
    "Mexico":               "México",
    "Morocco":              "Marruecos",
    "Netherlands":          "Países Bajos",
    "Poland":               "Polonia",
    "Portugal":             "Portugal",
    "Qatar":                "Qatar",
    "Saudi Arabia":         "Arabia Saudita",
    "Senegal":              "Senegal",
    "Serbia":               "Serbia",
    "South Korea":          "Corea del Sur",
    "Spain":                "España",
    "Switzerland":          "Suiza",
    "Tunisia":              "Túnez",
    "Uruguay":              "Uruguay",
    "USA":                  "Estados Unidos",
    "Wales":                "Gales",
    # Probables para 2026 — ajustar si SofaScore usa otro nombre
    "Algeria":              "Argelia",
    "Austria":              "Austria",
    "Bolivia":              "Bolivia",
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "Bosnia & Herzegovina": "Bosnia-Herzegovina",
    "Cape Verde":           "Cabo Verde",
    "Chile":                "Chile",
    "Colombia":             "Colombia",
    "Costa Rica":           "Costa Rica",
    "Cuba":                 "Cuba",
    "Curacao":              "Curazao",
    "Czech Republic":       "República Checa",
    "Czechia":              "República Checa",
    "DR Congo":             "RD Congo",
    "Democratic Republic of Congo": "RD Congo",
    "Egypt":                "Egipto",
    "Haiti":                "Haití",
    "Honduras":             "Honduras",
    "Indonesia":            "Indonesia",
    "Iraq":                 "Irak",
    "Ivory Coast":          "Costa de Marfil",
    "Cote d'Ivoire":        "Costa de Marfil",
    "Jamaica":              "Jamaica",
    "Jordan":               "Jordania",
    "New Zealand":          "Nueva Zelanda",
    "Nigeria":              "Nigeria",
    "Norway":               "Noruega",
    "Panama":               "Panamá",
    "Paraguay":             "Paraguay",
    "Peru":                 "Perú",
    "Scotland":             "Escocia",
    "South Africa":         "Sudáfrica",
    "Sweden":               "Suecia",
    "Turkey":               "Turquía",
    "Turkiye":              "Turquía",
    "Ukraine":              "Ucrania",
    "Uzbekistan":           "Uzbekistán",
    "Venezuela":            "Venezuela",
}


# ====================================================================
# DESCARGA
# ====================================================================

def obtener_partidos_mundial():
    headers = {
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/",
        "Accept-Language": "es-ES,es;q=0.9",
        "Cache-Control": "max-age=0",
        "x-requested-with": "XMLHttpRequest"
    }

    print(f"🔍 Buscando partidos del Mundial 2026 (Torneo: {UNIQUE_TOURNAMENT_ID}, Temp: {SEASON_ID})...")

    # Bypass antibot avanzado
    session = requests.Session(impersonate="chrome120")
    print("  🕵️ Haciendo visita de 'calentamiento' a la portada para coger cookies...")
    try:
        session.get("https://www.sofascore.com/", timeout=15)
    except:
        pass

    todos_los_eventos = []
    eventos_ids = set() # Set para evitar duplicados entre last y next

    # Iteramos por los dos endpoints: pasados/en juego ("last") y futuros ("next")
    for tipo_endpoint in ["last", "next"]:
        pagina = 0
        print(f"  📡 Extrayendo lote: {tipo_endpoint.upper()}...")
        while True:
            # Usamos el dominio www principal en vez del subdominio api
            url = (
                f"https://www.sofascore.com/api/v1/unique-tournament/{UNIQUE_TOURNAMENT_ID}"
                f"/season/{SEASON_ID}/events/{tipo_endpoint}/{pagina}"
            )
            try:
                respuesta = session.get(url, headers=headers, timeout=15)
                
                if respuesta.status_code == 403:
                    print("     ❌ HTTP 403: Muro antibot detectado.")
                    break
                if respuesta.status_code != 200:
                    break

                datos = respuesta.json()
                eventos_pagina = datos.get('events', [])
                
                # Añadimos solo eventos que no hayamos guardado ya
                for ev in eventos_pagina:
                    ev_id = ev.get('id')
                    if ev_id not in eventos_ids:
                        eventos_ids.add(ev_id)
                        todos_los_eventos.append(ev)

                if not datos.get('hasNextPage', False) or not eventos_pagina:
                    break
                pagina += 1

            except Exception as e:
                print(f"❌ Error de conexión con SofaScore: {e}")
                break

    print(f"✅ Extraídos {len(todos_los_eventos)} partidos únicos en bruto del servidor.")
    return todos_los_eventos


# ====================================================================
# ESTRUCTURACIÓN
# ====================================================================

def calcular_goles_y_pasa(evento, local_es, visitante_es):
    """Extrae goles sin penaltis y determina qué equipo pasa."""
    estado = evento.get('status', {}).get('type')
    score_home = evento.get('homeScore', {})
    score_away = evento.get('awayScore', {})

    penaltis_loc = score_home.get('penalties') or 0
    penaltis_vis = score_away.get('penalties') or 0

    if estado == 'notstarted':
        return "", "", "TBD"

    goles_loc = str((score_home.get('current') or 0) - penaltis_loc)
    goles_vis = str((score_away.get('current') or 0) - penaltis_vis)

    pasa = "TBD"
    if estado == 'finished':
        gl, gv = int(goles_loc), int(goles_vis)
        if gl > gv:
            pasa = local_es
        elif gv > gl:
            pasa = visitante_es
        else:
            # Empate en tiempo reglamentario → penaltis
            if penaltis_loc > penaltis_vis:
                pasa = local_es
            elif penaltis_vis > penaltis_loc:
                pasa = visitante_es

    return goles_loc, goles_vis, pasa


def estructurar_resultados_oficiales(eventos_crudos):
    """
    Clasifica los eventos en fase_grupos y eliminatorias.

    - Fase de grupos: NO traduce nombres (solo goles/estado se usarán en el merge).
    - Eliminatorias:  SÍ traduce nombres (se inyectarán cuando los placeholders se resuelvan).
    - Guarda _timestamp UTC para el matching por fecha.
    """
    resultados = {
        "fase_grupos": {},
        "clasificados_a_dieciseisavos": [],
        "eliminatorias": {
            "dieciseisavos": [], "octavos": [], "cuartos": [],
            "semifinales": [], "tercer_puesto": [], "final": []
        }
    }

    for evento in eventos_crudos:
        estado         = evento.get('status', {}).get('type')
        nombre_ronda   = evento.get('roundInfo', {}).get('name', '')
        nombre_ronda_n = nombre_ronda.strip().lower()  # normalizado para comparación
        timestamp_unix = evento.get('startTimestamp', 0)

        # ---- Determinar si es fase de grupos o eliminatoria ----
        fase_interna = RONDA_A_FASE.get(nombre_ronda_n)  # None si es grupos

        if fase_interna is None:
            # FASE DE GRUPOS
            # No necesitamos traducir los nombres porque el merge de grupos
            # solo actualizará goles/estado (matching por nombre ya en español).
            local_raw     = evento.get('homeTeam', {}).get('name', 'TBD')
            visitante_raw = evento.get('awayTeam', {}).get('name', 'TBD')

            score_home = evento.get('homeScore', {})
            score_away = evento.get('awayScore', {})
            penaltis_loc = score_home.get('penalties') or 0
            penaltis_vis = score_away.get('penalties') or 0

            if estado == 'notstarted':
                goles_loc_str = ""
                goles_vis_str = ""
            else:
                goles_loc_str = str((score_home.get('current') or 0) - penaltis_loc)
                goles_vis_str = str((score_away.get('current') or 0) - penaltis_vis)

            grupo_crudo = evento.get('tournament', {}).get('groupName', 'Group Desconocido')
            grupo = grupo_crudo.replace("Group", "Grupo").strip()

            if grupo not in resultados["fase_grupos"]:
                resultados["fase_grupos"][grupo] = []

            resultados["fase_grupos"][grupo].append({
                "local":           local_raw,      # en inglés, solo para el matching interno
                "visitante":       visitante_raw,
                "goles_local":     goles_loc_str,
                "goles_visitante": goles_vis_str,
                "estado":          estado,
                "_timestamp":      timestamp_unix
            })

        else:
            # ELIMINATORIAS — aquí sí traducimos porque inyectaremos los nombres
            local_eng     = evento.get('homeTeam', {}).get('name', 'TBD')
            visitante_eng = evento.get('awayTeam', {}).get('name', 'TBD')
            local_es      = TRADUCCIONES.get(local_eng, local_eng)
            visitante_es  = TRADUCCIONES.get(visitante_eng, visitante_eng)

            goles_loc, goles_vis, pasa = calcular_goles_y_pasa(evento, local_es, visitante_es)

            partido_elim = {
                "local":           local_es,
                "visitante":       visitante_es,
                "pasa":            pasa,
                "estado":          estado,
                "goles_local":     goles_loc,
                "goles_visitante": goles_vis,
                "_timestamp":      timestamp_unix
            }

            if fase_interna in ("tercer_puesto", "final"):
                partido_elim["ganador"] = pasa

            resultados["eliminatorias"][fase_interna].append(partido_elim)

    resultados["fase_grupos"] = dict(sorted(resultados["fase_grupos"].items()))

    # Deducir clasificados desde los equipos conocidos en dieciseisavos (o octavos)
    ronda_corte = "dieciseisavos" if resultados["eliminatorias"]["dieciseisavos"] else "octavos"
    clasificados = set()
    for p in resultados["eliminatorias"][ronda_corte]:
        if p["local"] not in ("TBD", ""):
            clasificados.add(p["local"])
        if p["visitante"] not in ("TBD", ""):
            clasificados.add(p["visitante"])
    resultados["clasificados_a_dieciseisavos"] = sorted(list(clasificados))

    return resultados


# ====================================================================
# CONVERSIÓN DE FECHAS
# ====================================================================

def iso_local_a_timestamp_utc(fecha_iso: str) -> int:
    """
    Convierte una fecha ISO en hora local española (UTC+2 en verano)
    a timestamp Unix UTC, para poder comparar contra los timestamps de SofaScore.
    """
    if not fecha_iso:
        return 0
    try:
        dt_local = datetime.fromisoformat(fecha_iso)
        # Restamos el offset para obtener UTC
        dt_utc = dt_local - OFFSET_LOCAL_UTC
        return int(dt_utc.replace(tzinfo=timezone.utc).timestamp())
    except Exception:
        return 0


# ====================================================================
# HELPERS
# ====================================================================

def _es_placeholder(nombre: str) -> bool:
    """
    Devuelve True si el nombre es un placeholder (1E, 3A/3B/3C, Ganador 73...)
    en lugar de un nombre de país real.
    """
    if not nombre:
        return False
    if re.match(r'^\d[A-Z]', nombre):   # "1E", "2A", "3F"
        return True
    if "/" in nombre:                    # "3A/3B/3C/3D/3F"
        return True
    if re.match(r'^(Ganador|Perdedor)\s+\d+$', nombre, re.IGNORECASE):
        return True
    if re.match(r'^Eq\.\s+\d+', nombre):
        return True
    return False


# ====================================================================
# MERGE SELECTIVO
# ====================================================================

def hacer_update_selectivo(realidad_actual, resultados_nuevos):
    """
    Actualiza realidad_oficial.json con los datos de SofaScore.

    FASE DE GRUPOS:
        Matching por nombre de equipo (local + visitante, ya en español en nuestro JSON).
        Solo sobreescribe goles_local, goles_visitante y estado.
        NO toca local/visitante (ya están bien desde el principio).

    ELIMINATORIAS:
        Matching por fecha/hora UTC con tolerancia ±15 min.
        Sobreescribe goles, estado y pasa.
        Si el local/visitante actual es un placeholder, lo sustituye por el nombre
        real que devuelve SofaScore (ya traducido al español).
    """

    # ---- 1. FASE DE GRUPOS: matching por nombre ----
    for grupo, partidos_actuales in realidad_actual.get("fase_grupos", {}).items():
        # Construimos un índice rápido por (local_en_inglés, visitante_en_inglés)
        # de los partidos nuevos
        index_grupos = {}
        for p_nuevo in resultados_nuevos.get("fase_grupos", {}).get(grupo, []):
            key_directo  = (p_nuevo["local"],     p_nuevo["visitante"])
            key_invertido = (p_nuevo["visitante"], p_nuevo["local"])
            index_grupos[key_directo]  = ("directo",   p_nuevo)
            index_grupos[key_invertido] = ("invertido", p_nuevo)

        for p_act in partidos_actuales:
            # Nuestro JSON tiene los nombres en español → los traducimos al inglés
            # para buscar en el índice de SofaScore.
            # Estrategia más robusta: buscar directamente comparando los valores
            # en inglés que SofaScore devuelve contra los valores traducidos que tenemos.
            local_act = p_act.get("local", "")
            vis_act   = p_act.get("visitante", "")

            match_found = None
            invertido   = False

            for p_nuevo in resultados_nuevos.get("fase_grupos", {}).get(grupo, []):
                loc_n = TRADUCCIONES.get(p_nuevo["local"], p_nuevo["local"])
                vis_n = TRADUCCIONES.get(p_nuevo["visitante"], p_nuevo["visitante"])

                if loc_n == local_act and vis_n == vis_act:
                    match_found = p_nuevo
                    invertido   = False
                    break
                elif loc_n == vis_act and vis_n == local_act:
                    match_found = p_nuevo
                    invertido   = True
                    break

            if match_found:
                if not invertido:
                    p_act["goles_local"]     = match_found["goles_local"]
                    p_act["goles_visitante"] = match_found["goles_visitante"]
                else:
                    # SofaScore tiene los equipos al revés
                    p_act["goles_local"]     = match_found["goles_visitante"]
                    p_act["goles_visitante"] = match_found["goles_local"]
                p_act["estado"] = match_found["estado"]

    # ---- 2. ELIMINATORIAS: matching por fecha UTC ----
    for fase, partidos_actuales in realidad_actual.get("eliminatorias", {}).items():
        partidos_nuevos = resultados_nuevos.get("eliminatorias", {}).get(fase, [])
        if not partidos_nuevos:
            continue

        # Índice timestamp_utc → partido nuevo
        index_elim = {
            p["_timestamp"]: p
            for p in partidos_nuevos
            if p.get("_timestamp")
        }

        for p_act in partidos_actuales:
            ts_act = iso_local_a_timestamp_utc(p_act.get("fecha", ""))
            if not ts_act:
                continue

            # Buscar el partido más cercano en tiempo
            mejor_match  = None
            menor_diff   = float('inf')
            for ts_nuevo, p_nuevo in index_elim.items():
                diff = abs(ts_act - ts_nuevo)
                if diff < menor_diff:
                    menor_diff  = diff
                    mejor_match = p_nuevo

            if not mejor_match or menor_diff > TOLERANCIA_FECHA_SEGUNDOS:
                continue

            p_nuevo = mejor_match

            # Actualizar goles, estado y quién pasa
            p_act["goles_local"]     = p_nuevo["goles_local"]
            p_act["goles_visitante"] = p_nuevo["goles_visitante"]
            p_act["estado"]          = p_nuevo["estado"]

            if p_nuevo.get("pasa") and p_nuevo["pasa"] != "TBD":
                p_act["pasa"] = p_nuevo["pasa"]

            if p_nuevo.get("ganador"):
                p_act["ganador"] = p_nuevo["ganador"]

            # Inyectar nombres reales si los actuales son placeholders
            local_act = p_act.get("local", "")
            vis_act   = p_act.get("visitante", "")

            if _es_placeholder(local_act) and p_nuevo["local"] not in ("TBD", ""):
                print(f"  ✏️  [{fase}] ID {p_act.get('id_partido', '?')}: "
                      f"'{local_act}' → '{p_nuevo['local']}'")
                p_act["local"] = p_nuevo["local"]

            if _es_placeholder(vis_act) and p_nuevo["visitante"] not in ("TBD", ""):
                print(f"  ✏️  [{fase}] ID {p_act.get('id_partido', '?')}: "
                      f"'{vis_act}' → '{p_nuevo['visitante']}'")
                p_act["visitante"] = p_nuevo["visitante"]

    # ---- 3. Clasificados ----
    if resultados_nuevos.get("clasificados_a_dieciseisavos"):
        realidad_actual["clasificados_a_dieciseisavos"] = \
            resultados_nuevos["clasificados_a_dieciseisavos"]

    return realidad_actual


# ====================================================================
# PUNTO DE ENTRADA
# ====================================================================

def ejecutar_05_scraper():
    print("=======================================================")
    print(" 📥 [05] ACTUALIZANDO REALIDAD DESDE SOFASCORE 📥")
    print("=======================================================")

    eventos_crudos = obtener_partidos_mundial()
    if not eventos_crudos:
        print("⚠️ No hay datos en SofaScore todavía. Manteniendo realidad anterior.")
        return

    resultados_nuevos = estructurar_resultados_oficiales(eventos_crudos)

    carpeta_resultados = ROOT_DIR / "data" / "resultados"
    carpeta_resultados.mkdir(parents=True, exist_ok=True)
    ruta_guardado = carpeta_resultados / "realidad_oficial.json"

    realidad_actual = {
        "fase_grupos": {},
        "clasificados_a_dieciseisavos": [],
        "eliminatorias": {}
    }
    if ruta_guardado.exists():
        with open(ruta_guardado, 'r', encoding='utf-8') as f:
            try:
                realidad_actual = json.load(f)
            except json.JSONDecodeError:
                pass

    print("\n🔄 Iniciando merge selectivo...")
    realidad_actualizada = hacer_update_selectivo(realidad_actual, resultados_nuevos)

    # Limpiar campos auxiliares antes de escribir
    for partidos in realidad_actualizada.get("fase_grupos", {}).values():
        for p in partidos:
            p.pop("_timestamp", None)
    for partidos in realidad_actualizada.get("eliminatorias", {}).values():
        for p in partidos:
            p.pop("_timestamp", None)

    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(realidad_actualizada, f, ensure_ascii=False, indent=4)

    print(f"\n💾 Realidad oficial actualizada en: {ruta_guardado.relative_to(ROOT_DIR)}")
    print("   Grupos → matching por nombre | Eliminatorias → matching por fecha UTC")


if __name__ == "__main__":
    ejecutar_05_scraper()
