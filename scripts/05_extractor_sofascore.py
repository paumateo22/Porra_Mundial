import sys
import json
from pathlib import Path
from curl_cffi import requests

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# ====================================================================
# IDs DEL MUNDIAL 2026 (SofaScore)
# ====================================================================
UNIQUE_TOURNAMENT_ID = 16
SEASON_ID = 58210  # ID actual de SofaScore para 2026. Revisar días antes del torneo.

# Diccionario traductor base (Se ampliará cuando se clasifiquen los 48 equipos)
TRADUCCIONES = {
    "Netherlands": "Países Bajos", "USA": "Estados Unidos", "Argentina": "Argentina",
    "Australia": "Australia", "France": "Francia", "Poland": "Polonia",
    "England": "Inglaterra", "Senegal": "Senegal", "Japan": "Japón",
    "Croatia": "Croacia", "Brazil": "Brasil", "South Korea": "Corea del Sur",
    "Morocco": "Marruecos", "Spain": "España", "Portugal": "Portugal",
    "Switzerland": "Suiza", "Germany": "Alemania", "Belgium": "Bélgica",
    "Cameroon": "Camerún", "Canada": "Canadá", "Costa Rica": "Costa Rica",
    "Denmark": "Dinamarca", "Ecuador": "Ecuador", "Ghana": "Ghana",
    "Iran": "Irán", "Mexico": "México", "Qatar": "Qatar",
    "Saudi Arabia": "Arabia Saudita", "Serbia": "Serbia", "Tunisia": "Túnez",
    "Uruguay": "Uruguay", "Wales": "Gales",
    # Nuevos para 2026
    "Czech Republic": "República Checa", "Czechia": "República Checa",
    "South Africa": "Sudáfrica", "Norway": "Noruega", "Sweden": "Suecia",
    "Colombia": "Colombia", "Chile": "Chile", "Paraguay": "Paraguay",
    "Panama": "Panamá", "Bolivia": "Bolivia", "Peru": "Perú",
    "Ivory Coast": "Costa de Marfil", "Cote d'Ivoire": "Costa de Marfil",
    "Netherlands": "Países Bajos", "Austria": "Austria", "Algeria": "Argelia",
    "Jordan": "Jordania", "RD Congo": "RD Congo",
    "DR Congo": "RD Congo", "Democratic Republic of Congo": "RD Congo",
    "Uzbekistan": "Uzbekistán", "New Zealand": "Nueva Zelanda",
    "Scotland": "Escocia", "Haiti": "Haití", "Iraq": "Irak",
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "Cape Verde": "Cabo Verde", "Curacao": "Curazao",
    "Turkey": "Turquía", "Turkiye": "Turquía",
    "Tunisia": "Túnez",
}

# Tolerancia en segundos para el matching por fecha (15 minutos)
TOLERANCIA_FECHA_SEGUNDOS = 900


def obtener_partidos_mundial():
    headers = {
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/",
        "Accept-Language": "es-ES,es;q=0.9"
    }

    print(f"🔍 Buscando partidos del Mundial 2026 (Torneo: {UNIQUE_TOURNAMENT_ID}, Temp: {SEASON_ID})...")

    todos_los_eventos = []
    pagina = 0

    while True:
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{UNIQUE_TOURNAMENT_ID}/season/{SEASON_ID}/events/last/{pagina}"
        try:
            respuesta = requests.get(url, headers=headers, impersonate="chrome110")
            if respuesta.status_code != 200:
                break

            datos = respuesta.json()
            eventos_pagina = datos.get('events', [])
            todos_los_eventos.extend(eventos_pagina)

            if not datos.get('hasNextPage', False) or not eventos_pagina:
                break
            pagina += 1

        except Exception as e:
            print(f"❌ Error de conexión con SofaScore: {e}")
            break

    print(f"✅ Extraídos {len(todos_los_eventos)} partidos en bruto del servidor.")
    return todos_los_eventos


def estructurar_resultados_oficiales(eventos_crudos):
    """
    Convierte los eventos crudos de SofaScore a un diccionario estructurado.
    Incluye el timestamp Unix del partido para poder usarlo en el matching por fecha.
    """
    resultados = {
        "fase_grupos": {},
        "clasificados_a_dieciseisavos": [],
        "eliminatorias": {
            "dieciseisavos": [], "octavos": [], "cuartos": [],
            "semifinales": [], "tercer_puesto": [], "final": []
        }
    }

    partidos_procesados = 0

    for evento in eventos_crudos:
        estado = evento.get('status', {}).get('type')

        local_eng = evento.get('homeTeam', {}).get('name', 'TBD')
        visitante_eng = evento.get('awayTeam', {}).get('name', 'TBD')
        local = TRADUCCIONES.get(local_eng, local_eng)
        visitante = TRADUCCIONES.get(visitante_eng, visitante_eng)

        score_home = evento.get('homeScore', {})
        score_away = evento.get('awayScore', {})

        penaltis_loc = score_home.get('penalties', 0)
        penaltis_vis = score_away.get('penalties', 0)

        goles_loc_str = str(score_home.get('current', 0) - penaltis_loc) if estado != 'notstarted' else ""
        goles_vis_str = str(score_away.get('current', 0) - penaltis_vis) if estado != 'notstarted' else ""

        pasa = "TBD"
        if estado == 'finished':
            if goles_loc_str and goles_vis_str:
                if int(goles_loc_str) > int(goles_vis_str):
                    pasa = local
                elif int(goles_vis_str) > int(goles_loc_str):
                    pasa = visitante
                else:
                    if penaltis_loc > penaltis_vis:
                        pasa = local
                    elif penaltis_vis > penaltis_loc:
                        pasa = visitante
                    else:
                        pasa = "Empate"

        nombre_ronda = evento.get('roundInfo', {}).get('name', '').lower()

        # Timestamp Unix del partido (para matching por fecha en eliminatorias)
        timestamp_unix = evento.get('startTimestamp', 0)

        es_eliminatoria = any(kw in nombre_ronda for kw in [
            "16", "quarter", "semi", "final", "3rd", "1/8", "1/4", "32", "1/16", "round of"
        ])

        if not es_eliminatoria:
            # FASE DE GRUPOS
            grupo_crudo = evento.get('tournament', {}).get('groupName', 'Group Desconocido')
            grupo = grupo_crudo.replace("Group", "Grupo").strip()

            if grupo not in resultados["fase_grupos"]:
                resultados["fase_grupos"][grupo] = []

            resultados["fase_grupos"][grupo].append({
                "local": local,
                "visitante": visitante,
                "goles_local": goles_loc_str,
                "goles_visitante": goles_vis_str,
                "estado": estado,
                "_timestamp": timestamp_unix  # Auxiliar, se elimina tras el merge
            })

        else:
            # ELIMINATORIAS
            partido_elim = {
                "local": local,
                "visitante": visitante,
                "pasa": pasa,
                "estado": estado,
                "goles_local": goles_loc_str,
                "goles_visitante": goles_vis_str,
                "_timestamp": timestamp_unix  # Auxiliar, se elimina tras el merge
            }

            if "32" in nombre_ronda or "1/16" in nombre_ronda or "round of 32" in nombre_ronda:
                resultados["eliminatorias"]["dieciseisavos"].append(partido_elim)
            elif "16" in nombre_ronda or "1/8" in nombre_ronda or "round of 16" in nombre_ronda:
                resultados["eliminatorias"]["octavos"].append(partido_elim)
            elif "quarter" in nombre_ronda or "1/4" in nombre_ronda:
                resultados["eliminatorias"]["cuartos"].append(partido_elim)
            elif "semi" in nombre_ronda or "1/2" in nombre_ronda:
                resultados["eliminatorias"]["semifinales"].append(partido_elim)
            elif "3rd" in nombre_ronda or "third" in nombre_ronda or "tercer" in nombre_ronda:
                partido_elim["ganador"] = pasa
                resultados["eliminatorias"]["tercer_puesto"].append(partido_elim)
            elif "final" in nombre_ronda:
                partido_elim["ganador"] = pasa
                resultados["eliminatorias"]["final"].append(partido_elim)

        partidos_procesados += 1

    resultados["fase_grupos"] = dict(sorted(resultados["fase_grupos"].items()))

    # Deducir clasificados desde los equipos reales en dieciseisavos
    ronda_corte = "dieciseisavos" if resultados["eliminatorias"]["dieciseisavos"] else "octavos"
    equipos_clasificados = set()
    for p in resultados["eliminatorias"][ronda_corte]:
        if p["local"] != "TBD":
            equipos_clasificados.add(p["local"])
        if p["visitante"] != "TBD":
            equipos_clasificados.add(p["visitante"])

    resultados["clasificados_a_dieciseisavos"] = sorted(list(equipos_clasificados))

    print(f"📊 Se han estructurado {partidos_procesados} partidos en el formato oficial temporal.")
    return resultados


def iso_a_timestamp(fecha_iso: str) -> int:
    """Convierte una fecha ISO 8601 sin zona horaria a timestamp Unix (UTC)."""
    from datetime import datetime, timezone
    if not fecha_iso:
        return 0
    try:
        # Asumimos hora local de España (UTC+2 en verano, donde se juega el torneo)
        # Pero los JSONs están en hora local ya, así que comparamos directamente
        dt = datetime.fromisoformat(fecha_iso)
        # Devolvemos segundos desde epoch sin ajuste TZ (comparación relativa)
        return int(dt.timestamp())
    except Exception:
        return 0


def hacer_update_selectivo(realidad_actual, resultados_nuevos):
    """
    Actualiza la realidad oficial con los datos de SofaScore.

    FASE DE GRUPOS: Matching por nombre de equipo (local + visitante).
    ELIMINATORIAS: Matching por fecha/hora del partido (tolerancia ±15 min).
                   Esto resuelve el problema de los placeholders (1E, 3A/3B...).
                   Cuando SofaScore ya sabe quiénes juegan, inyectamos los nombres
                   reales en el JSON, preservando id_partido y fecha originales.
    """

    # ---- 1. FASE DE GRUPOS (matching por nombre) ----
    for grupo, partidos_actuales in realidad_actual.get("fase_grupos", {}).items():
        partidos_nuevos = resultados_nuevos.get("fase_grupos", {}).get(grupo, [])

        for p_act in partidos_actuales:
            for p_nuevo in partidos_nuevos:
                mismos_equipos_directos = (
                    p_act.get("local") == p_nuevo["local"] and
                    p_act.get("visitante") == p_nuevo["visitante"]
                )
                mismos_equipos_invertidos = (
                    p_act.get("local") == p_nuevo["visitante"] and
                    p_act.get("visitante") == p_nuevo["local"]
                )

                if mismos_equipos_directos:
                    p_act["goles_local"] = p_nuevo["goles_local"]
                    p_act["goles_visitante"] = p_nuevo["goles_visitante"]
                    p_act["estado"] = p_nuevo["estado"]
                    break
                elif mismos_equipos_invertidos:
                    # SofaScore invirtió el orden local/visitante (raro pero posible)
                    p_act["goles_local"] = p_nuevo["goles_visitante"]
                    p_act["goles_visitante"] = p_nuevo["goles_local"]
                    p_act["estado"] = p_nuevo["estado"]
                    break

    # ---- 2. ELIMINATORIAS (matching por fecha) ----
    for fase, partidos_actuales in realidad_actual.get("eliminatorias", {}).items():
        partidos_nuevos = resultados_nuevos.get("eliminatorias", {}).get(fase, [])

        if not partidos_nuevos:
            continue

        # Construimos un índice de los partidos de SofaScore por timestamp
        # para hacer el lookup en O(1)
        index_sofascore = {}  # timestamp_unix -> partido_sofascore
        for p_nuevo in partidos_nuevos:
            ts = p_nuevo.get("_timestamp", 0)
            if ts:
                index_sofascore[ts] = p_nuevo

        for p_act in partidos_actuales:
            # Convertimos la fecha ISO del partido actual a timestamp
            ts_act = iso_a_timestamp(p_act.get("fecha", ""))
            if not ts_act:
                continue

            # Buscamos el partido de SofaScore más cercano en tiempo
            mejor_match = None
            menor_diff = float('inf')

            for ts_nuevo, p_nuevo in index_sofascore.items():
                diff = abs(ts_act - ts_nuevo)
                if diff < menor_diff:
                    menor_diff = diff
                    mejor_match = p_nuevo

            # Solo hacemos el merge si la diferencia es menor a la tolerancia
            if mejor_match and menor_diff <= TOLERANCIA_FECHA_SEGUNDOS:
                p_nuevo = mejor_match

                # SIEMPRE actualizamos goles y estado
                p_act["goles_local"] = p_nuevo["goles_local"]
                p_act["goles_visitante"] = p_nuevo["goles_visitante"]
                p_act["estado"] = p_nuevo["estado"]

                if p_nuevo.get("pasa") and p_nuevo["pasa"] != "TBD":
                    p_act["pasa"] = p_nuevo["pasa"]

                if p_nuevo.get("ganador"):
                    p_act["ganador"] = p_nuevo["ganador"]

                # INYECCIÓN DE EQUIPOS REALES cuando los placeholders ya se conocen
                # Un placeholder es cualquier valor que no sea un nombre de país real.
                # Lo detectamos comprobando si contiene "/" o es mayúscula corta (1E, 2A, etc.)
                local_actual = p_act.get("local", "")
                visitante_actual = p_act.get("visitante", "")

                local_es_placeholder = _es_placeholder(local_actual)
                visitante_es_placeholder = _es_placeholder(visitante_actual)

                local_sofascore = p_nuevo.get("local", "")
                visitante_sofascore = p_nuevo.get("visitante", "")

                if local_es_placeholder and local_sofascore and local_sofascore != "TBD":
                    p_act["local"] = local_sofascore
                    print(f"  ✏️  [{fase}] ID {p_act.get('id_partido', '?')}: "
                          f"'{local_actual}' → '{local_sofascore}'")

                if visitante_es_placeholder and visitante_sofascore and visitante_sofascore != "TBD":
                    p_act["visitante"] = visitante_sofascore
                    print(f"  ✏️  [{fase}] ID {p_act.get('id_partido', '?')}: "
                          f"'{visitante_actual}' → '{visitante_sofascore}'")

    # ---- 3. Actualizar clasificados si SofaScore ya los tiene ----
    if resultados_nuevos.get("clasificados_a_dieciseisavos"):
        realidad_actual["clasificados_a_dieciseisavos"] = resultados_nuevos["clasificados_a_dieciseisavos"]

    return realidad_actual


def _es_placeholder(nombre: str) -> bool:
    """
    Detecta si un nombre de equipo es un placeholder (1E, 2A, 3A/3B/3C..., Ganador 73, etc.)
    en lugar de un nombre de país real.
    """
    if not nombre:
        return False

    # Formatos de placeholder conocidos:
    # - "1E", "2A", "3A/3B/3C/3D/3F"  → posiciones de grupo
    # - "Ganador 73", "Perdedor 101"    → resultados de partidos anteriores
    import re

    # Placeholder tipo posición: empieza por dígito + letra(s) o tiene "/"
    if re.match(r'^\d[A-Z]', nombre):
        return True
    if "/" in nombre:
        return True

    # Placeholder tipo "Ganador N" o "Perdedor N"
    if re.match(r'^(Ganador|Perdedor)\s+\d+$', nombre, re.IGNORECASE):
        return True

    # Placeholder tipo "Eq. 73A"
    if re.match(r'^Eq\.\s+\d+', nombre):
        return True

    return False


def ejecutar_05_scraper():
    print("=======================================================")
    print(" 📥 [05] ACTUALIZANDO REALIDAD DESDE SOFASCORE 📥")
    print("=======================================================")

    eventos_crudos = obtener_partidos_mundial()
    if not eventos_crudos:
        print("⚠️ No hay datos en SofaScore para este torneo todavía. Manteniendo realidad anterior.")
        return

    resultados_nuevos = estructurar_resultados_oficiales(eventos_crudos)

    carpeta_resultados = ROOT_DIR / "data" / "resultados"
    carpeta_resultados.mkdir(parents=True, exist_ok=True)
    ruta_guardado = carpeta_resultados / "realidad_oficial.json"

    realidad_actual = {"fase_grupos": {}, "clasificados_a_dieciseisavos": [], "eliminatorias": {}}
    if ruta_guardado.exists():
        with open(ruta_guardado, 'r', encoding='utf-8') as f:
            try:
                realidad_actual = json.load(f)
            except json.JSONDecodeError:
                pass

    print("\n🔄 Iniciando merge selectivo...")
    realidad_actualizada = hacer_update_selectivo(realidad_actual, resultados_nuevos)

    # Limpiar campos auxiliares "_timestamp" que no deben persistir en el JSON
    for grupo, partidos in realidad_actualizada.get("fase_grupos", {}).items():
        for p in partidos:
            p.pop("_timestamp", None)
    for fase, partidos in realidad_actualizada.get("eliminatorias", {}).items():
        for p in partidos:
            p.pop("_timestamp", None)

    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(realidad_actualizada, f, ensure_ascii=False, indent=4)

    print(f"\n💾 ¡Realidad oficial actualizada con éxito en: {ruta_guardado.relative_to(ROOT_DIR)}")
    print("   (Update selectivo: grupos por nombre, eliminatorias por fecha)")


if __name__ == "__main__":
    ejecutar_05_scraper()