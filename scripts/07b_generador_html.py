import sys
import json
import csv
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

CONFIG = cargar_json(ROOT_DIR / "config" / "settings.json") or {"multiplicadores": {"incremento_racha_por_fase": 0.5}}

def calcular_clasificacion_grupos(fase_grupos):
    posiciones = {}
    for grupo, partidos in fase_grupos.items():
        tabla = {}
        for p in partidos:
            loc, vis = p['local'], p['visitante']
            if loc not in tabla: tabla[loc] = {"pts": 0, "dif": 0}
            if vis not in tabla: tabla[vis] = {"pts": 0, "dif": 0}

            gl = int(p.get('goles_local', 0)) if str(p.get('goles_local', '')).isdigit() else 0
            gv = int(p.get('goles_visitante', 0)) if str(p.get('goles_visitante', '')).isdigit() else 0

            tabla[loc]["dif"] += (gl - gv)
            tabla[vis]["dif"] += (gv - gl)

            if p.get('estado', 'finished') == 'finished':
                if gl > gv: tabla[loc]["pts"] += 3
                elif gv > gl: tabla[vis]["pts"] += 3
                else:
                    tabla[loc]["pts"] += 1
                    tabla[vis]["pts"] += 1

        equipos_ordenados = sorted(tabla.items(), key=lambda x: (x[1]["pts"], x[1]["dif"]), reverse=True)
        for idx, (eq, stats) in enumerate(equipos_ordenados): posiciones[eq] = idx + 1
    return posiciones

def limpiar_nombre_archivo(nombre):
    reemplazos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', ' ': '_'}
    res = nombre.lower()
    for orig, rep in reemplazos.items(): res = res.replace(orig, rep)
    return "".join(c for c in res if c.isalnum() or c == '_') + "_sd.png"

def obtener_racha_fases(jugador_dir, equipo, fase_objetivo):
    fases_cronologicas = ["grupos", "dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]
    fase_busqueda_ocr = "finales" if fase_objetivo in ["final", "tercer_puesto", "finales"] else fase_objetivo
    fase_busqueda_infobae = "finales" if fase_objetivo in ["final", "tercer_puesto"] else fase_objetivo

    idx_limite = fases_cronologicas.index(fase_busqueda_ocr) if fase_busqueda_ocr in fases_cronologicas else 0
    rastros = []

    for i in range(idx_limite):
        fase_origen = fases_cronologicas[i]
        if fase_origen == "grupos":
            ruta_base = jugador_dir / "pronosticos" / "grupos" / f"{jugador_dir.name}_base.json"
            if ruta_base.exists():
                base = cargar_json(ruta_base)
                for p in base.get("eliminatorias", {}).get(fase_busqueda_infobae, []):
                    if p.get("local") == equipo or p.get("visitante") == equipo:
                        rastros.append(("Grupos", f"participantes/{jugador_dir.name}/pronosticos/grupos/{jugador_dir.name}_base.json"))
                        break
        else:
            ruta_ocr = jugador_dir / "pronosticos" / "eliminatorias" / fase_origen / f"{fase_origen}.json"
            if ruta_ocr.exists():
                ocr_data = cargar_json(ruta_ocr)
                for p in ocr_data.get("predicciones", {}).get(fase_busqueda_ocr, []):
                    if p.get("local") == equipo or p.get("visitante") == equipo:
                        nombres_cortos = {"dieciseisavos": "1/16", "octavos": "1/8", "cuartos": "1/4", "semifinales": "Semis"}
                        nombre_link = nombres_cortos.get(fase_origen, fase_origen)
                        rastros.append((nombre_link, f"participantes/{jugador_dir.name}/pronosticos/eliminatorias/{fase_origen}/{fase_origen}.json"))
                        break
    return rastros

def get_sidebar_html(depth=""):
    return f"""
    <div id="mySidenav" class="sidenav">
        <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>
        <a href="{depth}instrucciones.html" style="color:var(--gold);">📖 Instrucciones & Registro</a>
        <a href="{depth}index.html">🏠 Clasificación Global</a>
        <a href="{depth}calendario.html">📅 Calendario Oficial</a>
        <a href="{depth}participantes.html">👥 Participantes</a>
        <a href="https://www.infobae.com/mundial-2026/simulador/" target="_blank">🔗 Infobae</a>
        <a href="https://www.livefutbol.com/competition/co139/fifa-copa-mundial/standings-calculator/" target="_blank">🔗 LiveFutbol</a>
        <a href="https://www.sofascore.com/es-la/football/tournament/world/world-championship/16#id:58210" target="_blank">🔗 SofaScore</a>
    </div>
    <div class="menu-btn" onclick="openNav()">&#9776;</div>
    <script>
        function openNav() {{ document.getElementById("mySidenav").style.width = "250px"; }}
        function closeNav() {{ document.getElementById("mySidenav").style.width = "0"; }}
    </script>
    """

def get_header_html(title, subtitle, depth="", show_participa=False):
    participa_btn = f'<br><a href="{depth}instrucciones.html" class="btn-participa">¡PARTICIPA AHORA!</a>' if show_participa else ""
    return f"""
    <header>
        <h1>{title}</h1>
        <p>{subtitle}</p>
        <div class="top-nav">
            <a href="{depth}index.html" class="home-btn">🏠 Inicio</a>
            <a href="https://www.infobae.com/mundial-2026/simulador/" target="_blank">Infobae</a>
            <a href="https://www.livefutbol.com/competition/co139/fifa-copa-mundial/standings-calculator/" target="_blank">LiveFutbol</a>
            <a href="https://www.sofascore.com/es-la/football/tournament/world/world-championship/16#id:58210" target="_blank">SofaScore</a>
        </div>
        {participa_btn}
    </header>
    """

# =====================================================================
# INSTRUCCIONES HTML
# =====================================================================
def generar_instrucciones_html():
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instrucciones y Registro - Porra Mundial</title>
    <link rel="stylesheet" href="theme.css">
</head>
<body>
    {get_sidebar_html("")}
    {get_header_html("📖 Instrucciones & Registro", "Todo lo que necesitas saber para participar en la Porra Mundial 2026", "")}
    <div class="container">
        <h2>Registro en 3 Pasos</h2>
        
        <div class="instrucciones-box">
            <h3>Paso 1: Fase de Grupos (Infobae)</h3>
            <p>Primero, debes pronosticar todos los resultados de la fase de grupos usando el simulador de Infobae.</p>
            <p>🔗 <a href="https://www.infobae.com/mundial-2026/simulador/" target="_blank">Abrir Simulador Infobae</a></p>
            <p><i>Nota: Copia el enlace de tus resultados para el siguiente paso.</i></p>
        </div>

        <div class="instrucciones-box">
            <h3>Paso 2: Registro Oficial y Premios (Google Forms)</h3>
            <p>Rellena el formulario oficial. Aquí deberás pegar el enlace de Infobae con tu pronóstico y votar por los premios extra (MVP, Bota de Oro, Jugador Joven).</p>
            <p>🔗 <a href="https://docs.google.com/forms/d/e/1FAIpQLSdd_VDG4fUwA3l9eLJa0EmKJ64NeoMYGZv6YvPE_VnrhBTYMg/viewform?usp=dialog" target="_blank">Rellenar Formulario Oficial</a></p>
        </div>

        <div class="instrucciones-box">
            <h3>Paso 3: Eliminatorias (LiveFutbol)</h3>
            <p>Finalmente, usa LiveFutbol para pronosticar todas las fases de eliminatoria (desde Dieciseisavos hasta la Final. En cada fase tendrás que volver a pronosticar desde la fase actual hasta la final).</p>
            <p>🔗 <a href="https://www.livefutbol.com/competition/co139/fifa-copa-mundial/standings-calculator/" target="_blank">Abrir Calculadora LiveFutbol</a></p>
            <p><i>Nota: El motor leerá las capturas de este bracket automáticamente.</i></p>
        </div>

        <details>
            <summary><h2>📜 Reglamento y Funcionamiento</h2></summary>
            <div style="padding: 10px;">
                <p>El sistema se actualiza en tiempo real de forma automática extrayendo datos de la API oficial.</p>
                <ul>
                    <li><strong>Acierto de Signo (1X2):</strong> Otorga 1 punto base.</li>
                    <li><strong>Acierto Exacto:</strong> Otorga {CONFIG.get("puntuacion", {}).get("acierto_exacto", 3)} puntos si clavas el resultado numérico.</li>
                    <li><strong>Multiplicadores:</strong> En eliminatorias, si un equipo que pusiste que pasaba llega lejos en la vida real, tus puntos se multiplicarán dependiendo de la racha desde donde lo pronosticaste.</li>
                    <li><strong>Bonos de Jornada:</strong> El jugador con más aciertos exactos de cada ronda se lleva el bono "Ganador", y el peor pierde puntos.</li>
                </ul>
                <p>El proyecto es Open Source y está automatizado mediante GitHub Actions.</p>
                <p>🔗 <a href="https://github.com/paumateo22/Porra_Mundial" target="_blank" style="color:var(--gold);">Ver Repositorio en GitHub</a></p>
            </div>
        </details>
    </div>
</body>
</html>
"""
    with open(ROOT_DIR / "instrucciones.html", 'w', encoding='utf-8') as f:
        f.write(html)

# =====================================================================
# INDEX (RANKING Y ÚLTIMOS PARTIDOS)
# =====================================================================
def generar_index_html():
    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    if not ruta_csv.exists(): return False

    jornadas_dict = cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    jornadas_keys = list(jornadas_dict.keys())
    
    realidad_dict = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    pos_real = calcular_clasificacion_grupos(realidad_dict.get("fase_grupos", {}))
    pasan_real = realidad_dict.get("clasificados_a_dieciseisavos", [])

    # Obtener dinámicamente los puntos base definidos en settings.json
    pts_1x2_val = CONFIG.get("puntuacion", {}).get("acierto_1x2", 1)
    pts_ex_val = CONFIG.get("puntuacion", {}).get("acierto_exacto", 3)

    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏆 Porra Mundial 2026</title>
    <link rel="stylesheet" href="theme.css">
</head>
<body>
    {get_sidebar_html("")}
    {get_header_html("🏆 Porra Mundial 2026", f"Panel de Estadísticas Oficiales | Actualizado: {fecha_act}", "", show_participa=True)}
    <div class="container">
"""
    
    jugadores_datos = []
    with open(ruta_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jug_id = row['Jugador'].replace(' ', '_').lower()
            ruta_libro = ROOT_DIR / "participantes" / jug_id / "estadisticas" / "historial_puntos.json"
            ruta_base = ROOT_DIR / "participantes" / jug_id / "pronosticos" / "grupos" / f"{jug_id}_base.json"
            
            libro = cargar_json(ruta_libro) or {}
            base_pred = cargar_json(ruta_base) or {}
            premios = libro.get("premios_finales", {}).get("formularios", {}).get("detalles", {})
            pts_extra_totales = float(row.get('Puntos_Podio', 0)) + float(row.get('Puntos_Forms', 0))
            
            total_1x2 = total_exactos = 0
            for p_data in libro.get("desglose_partidos", {}).values():
                if p_data.get("acierto_1x2"): total_1x2 += 1
                if p_data.get("acierto_exacto"): total_exactos += 1
                
            victorias_j = derrotas_j = 0
            for j_data in libro.get("desglose_jornadas", {}).values():
                res = j_data.get("resultado")
                if res == "Ganador": victorias_j += 1
                elif res == "Perdedor": derrotas_j += 1
                
            pos_pred = calcular_clasificacion_grupos(base_pred.get("fase_grupos", {}))
            pasan_pred = base_pred.get("clasificados_a_dieciseisavos", [])
            aciertos_pase = sum(1 for eq in pasan_real if eq in pasan_pred)
            aciertos_pos = sum(1 for eq in pasan_real if eq in pasan_pred and pos_pred.get(eq) == pos_real.get(eq))

            jugadores_datos.append({
                "pos_csv": row['Posicion'],
                "nombre": row['Jugador'],
                "id": jug_id,
                "total": row['TOTAL'],
                "sd_str": f"+{premios.get('sorpresa', 0)} | +{premios.get('decepcion', 0)}",
                "extras": f"{pts_extra_totales:.2f}",
                "aciertos_str": f"{total_exactos} / {total_1x2}",
                "record_str": f"{victorias_j}W - {derrotas_j}L",
                "pase_str": f"{aciertos_pos} / {aciertos_pase}",
                "libro": libro
            })

    # SECCIÓN 1: RESUMEN GENERAL
    html += """
        <details open>
            <summary><h2>📊 Resumen General</h2></summary>
            <div class="table-wrapper">
                <table>
                    <tr>
                        <th>Pos</th><th>Jugador</th><th>Aciertos<br><span style="font-size:0.8em">(Exactos / 1x2)</span></th>
                        <th>Pase a Elim.<br><span style="font-size:0.8em">(Posición / Pasan)</span></th>
                        <th>Sorpresa | Decepción</th><th>Extras<br>(Premios)</th><th>Récord<br>(Ganador/Perdedor)</th><th>Total</th>
                    </tr>
"""
    for j in jugadores_datos:
        pos_display = j['pos_csv'] + "º"
        if j['pos_csv'] == "1": pos_display = "🥇 1º"
        elif j['pos_csv'] == "2": pos_display = "🥈 2º"
        elif j['pos_csv'] == "3": pos_display = "🥉 3º"
        html += f"""
                    <tr>
                        <td>{pos_display}</td>
                        <td><a href="participantes/{j['id']}/vistas/dashboard.html" style="color:var(--gold); font-weight:bold; text-decoration:none;">{j['nombre']}</a></td>
                        <td>{j['aciertos_str']}</td>
                        <td>{j['pase_str']}</td>
                        <td>{j['sd_str']}</td>
                        <td>{j['extras']}</td>
                        <td>{j['record_str']}</td>
                        <td class="pts-totales">{j['total']}</td>
                    </tr>"""
    html += """
                </table>
            </div>
        </details>
"""

    # SECCIÓN 2: ÚLTIMOS PARTIDOS (Plegados por defecto, sin emojis, con desglose)
    ultimos_terminados = []
    for g, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos:
            if p.get("estado") == "finished": ultimos_terminados.append({"fase": g, "data": p, "limpia": "grupos"})
    
    fases_elim = [("dieciseisavos", "1/16"), ("octavos", "1/8"), ("cuartos", "1/4"), ("semifinales", "Semis"), ("tercer_puesto", "3º Puesto"), ("final", "Final")]
    for clave, nombre in fases_elim:
        for p in realidad_dict.get("eliminatorias", {}).get(clave, []):
            if p.get("estado") == "finished": ultimos_terminados.append({"fase": nombre, "data": p, "limpia": clave})
            
    ultimos_4 = ultimos_terminados[-4:]
    ultimos_4.reverse()

    html += """
        <h2 style="margin-top:40px;">🔥 Últimos Partidos 
            <a href="calendario.html" style="font-size:0.5em; float:right; color:var(--table-header); text-decoration:none; margin-top:10px;">Ver Calendario ➡️</a>
        </h2>
        <div class="latest-grid" style="margin-bottom:40px;">
    """
    
    if not ultimos_4:
        html += "<p style='color:gray;'>Aún no hay partidos finalizados.</p>"
    else:
        jugadores_dirs = [p for p in (ROOT_DIR / "participantes").iterdir() if p.is_dir()]
        for u_match in ultimos_4:
            fase_txt = u_match["fase"]
            p_real = u_match["data"]
            loc_r = p_real.get("local", "")
            vis_r = p_real.get("visitante", "")
            clave = f"ID_{p_real['id_partido']}" if "id_partido" in p_real else f"{loc_r}_vs_{vis_r}"
            
            stats_match = []
            for j_dir in jugadores_dirs:
                libro_j = cargar_json(j_dir / "estadisticas" / "historial_puntos.json") or {}
                info_p = libro_j.get("desglose_partidos", {}).get(clave)
                if not info_p: continue
                
                pred_txt = "-"
                ruta_base = j_dir / "pronosticos" / "grupos" / f"{j_dir.name}_base.json"
                base_pred = cargar_json(ruta_base) or {}
                dict_preds = {}
                for g_k, p_list in base_pred.get("fase_grupos", {}).items():
                    for pp in p_list: dict_preds[f"{pp['local']}_vs_{pp['visitante']}"] = pp
                for f_k in ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]:
                    f_data = cargar_json(j_dir / "pronosticos" / "eliminatorias" / f_k / f"{f_k}.json") or {}
                    for f_dest, p_list in f_data.get("predicciones", {}).items():
                        r_fase = realidad_dict.get("eliminatorias", {}).get("tercer_puesto", []) + realidad_dict.get("eliminatorias", {}).get("final", []) if f_dest in ["finales", "final", "tercer_puesto"] else realidad_dict.get("eliminatorias", {}).get(f_dest, [])
                        for i, p_rl in enumerate(r_fase):
                            if i < len(p_list): dict_preds[f"ID_{p_rl['id_partido']}"] = p_list[i]

                p_pred = dict_preds.get(clave, {})
                if p_pred:
                    loc_p, vis_p = p_pred.get("local", ""), p_pred.get("visitante", "")
                    if loc_p != loc_r or vis_p != vis_r:
                        pred_txt = f"{loc_p} {p_pred.get('goles_local','-')}-{p_pred.get('goles_visitante','-')} {vis_p}"
                    else:
                        pred_txt = f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}"

                # Diseño Semántico y LÓGICA DINÁMICA DE DESGLOSE DE PUNTOS
                acierto_ex = info_p.get("acierto_exacto", False)
                acierto_1x2 = info_p.get("acierto_1x2", False)
                mult = info_p.get("multiplicador_aplicado", 1.0)
                pts_finales = info_p.get("puntos_conseguidos", 0)
                
                if acierto_ex: 
                    pred_styled = f"<span class='pred-exact'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[ {pts_1x2_val} <span class='pred-1x2'>Acierto</span> + {pts_ex_val} <span class='pred-exact'>Exacto</span> ] &times; {mult}</span>"
                elif acierto_1x2: 
                    pred_styled = f"<span class='pred-1x2'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[ {pts_1x2_val} <span class='pred-1x2'>Acierto</span> ] &times; {mult}</span>"
                else: 
                    pred_styled = f"<span class='pred-miss'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:gray; font-size:0.85em;'>0 pts</span>"

                # Multiplicador Desplegable
                mult_html = f"x{mult}"
                if mult > 1.0:
                    r_loc = obtener_racha_fases(j_dir, p_real.get("local"), u_match["limpia"])
                    r_vis = obtener_racha_fases(j_dir, p_real.get("visitante"), u_match["limpia"])
                    content_html = ""
                    if r_loc:
                        content_html += f"<strong>{p_real.get('local')}:</strong><br>"
                        for r in r_loc: content_html += f"<a href='{r[1]}' target='_blank' class='mult-link'>+{CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a><br>"
                    if r_vis:
                        content_html += f"<strong>{p_real.get('visitante')}:</strong><br>"
                        for r in r_vis: content_html += f"<a href='{r[1]}' target='_blank' class='mult-link'>+{CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a><br>"
                    
                    if content_html:
                        mult_html = f"<details class='mult-details'><summary>x{mult} ▼</summary><div class='mult-content'>{content_html}</div></details>"

                stats_match.append({
                    "nombre": j_dir.name.replace('_', ' ').title(),
                    "id": j_dir.name,
                    "pts": pts_finales,
                    "mult": mult_html,
                    "pred": pred_styled,
                    "desglose": desglose_html
                })

            stats_match = sorted(stats_match, key=lambda x: x['pts'], reverse=True)

            html += f"""
            <details class="match-card">
                <summary>
                    <div class="match-header">{fase_txt}</div>
                    <div class="match-score">{loc_r} <span>{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}</span> {vis_r}</div>
                </summary>
                <div class="match-breakdown">
                    <table style="font-size:0.9em; background:transparent;">
                        <tr>
                            <th style="background:#111;">Jugador</th>
                            <th style="background:#111;">Pronóstico</th>
                            <th style="background:#111; width:70px;">Mult.</th>
                            <th style="background:#111;">Cálculo</th>
                            <th style="background:#111;">Pts</th>
                        </tr>"""
            for st in stats_match:
                html += f"<tr><td><a href='participantes/{st['id']}/vistas/dashboard.html' style='color:#b0c4de; text-decoration:none;'>{st['nombre']}</a></td><td>{st['pred']}</td><td>{st['mult']}</td><td>{st['desglose']}</td><td style='color:var(--gold); font-weight:bold; font-size:1.1em;'>{st['pts']}</td></tr>"
            html += """</table></div></details>"""
            
    html += "</div>"

    # SECCIÓN 3: RENDIMIENTO POR JORNADAS
    html += """
        <details open>
            <summary><h2>📅 Rendimiento por Jornadas</h2></summary>
            <div class="table-wrapper">
                <table>
                    <tr>
                        <th>Pos</th><th>Jugador</th>
"""
    for j_key in jornadas_keys: html += f"<th>{j_key.upper()}</th>"
    html += "</tr>\n"

    for j in jugadores_datos:
        html += f"<tr><td>{j['pos_csv']}º</td><td>{j['nombre']}</td>"
        desglose_j = j['libro'].get("desglose_jornadas", {})
        desglose_p = j['libro'].get("desglose_partidos", {})
        
        for j_key in jornadas_keys:
            info_j = desglose_j.get(j_key)
            if not info_j:
                html += "<td>-</td>"
                continue
                
            exactos_j = pts_partidos_j = 0
            for p in jornadas_dict.get(j_key, []):
                clave_p = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                info_partido = desglose_p.get(clave_p, {})
                if info_partido.get("acierto_exacto", False): exactos_j += 1
                pts_partidos_j += info_partido.get("puntos_conseguidos", 0)
                
            aciertos_1x2_j = info_j.get("aciertos_1x2", 0)
            pts_totales_j = pts_partidos_j + info_j.get("puntos_bono", 0)
            
            pts_str = f"+{pts_totales_j}" if pts_totales_j > 0 else f"{pts_totales_j}"
            texto_celda = f"<strong>{exactos_j} / {aciertos_1x2_j}</strong><br><span style='font-size:0.85em; font-weight:normal; opacity:0.85;'>{pts_str} pts</span>"
            
            res = info_j.get("resultado", "")
            clase_css = ' class="ganador-jornada"' if res == "Ganador" else (' class="perdedor-jornada"' if res == "Perdedor" else "")
            
            html += f"<td{clase_css}>{texto_celda}</td>"
            
        html += "</tr>\n"
        
    html += """
                </table>
            </div>
        </details>
    </div>
</body>
</html>
"""
    with open(ROOT_DIR / "index.html", 'w', encoding='utf-8') as f:
        f.write(html)
    return True

# =====================================================================
# RESTO DE VISTAS (Participantes, Calendario)
# =====================================================================
def generar_participantes_html():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Participantes - Porra Mundial</title><link rel="stylesheet" href="theme.css"></head><body>{get_sidebar_html("")}{get_header_html("👥 Participantes", "Dashboards Individuales y Gráficos de Rendimiento", "")}<div class="container"><div class="jugadores-grid">"""
    for jugador_dir in jugadores: html += f"""<a href="participantes/{jugador_dir.name}/vistas/dashboard.html" class="card"><h3>{jugador_dir.name.replace('_', ' ').title()}</h3><p>Ver Gráficas y Detalle 📊</p></a>"""
    html += "</div></div></body></html>"
    with open(ROOT_DIR / "participantes.html", 'w', encoding='utf-8') as f: f.write(html)

def render_partido_bracket(p):
    loc, vis = p.get('local', 'TBD'), p.get('visitante', 'TBD')
    gl, gv = p.get('goles_local', '-'), p.get('goles_visitante', '-')
    ganador = p.get('ganador') if 'ganador' in p else p.get('pasa', 'TBD')
    c_loc = "winner" if ganador == loc and ganador != "TBD" else ""
    c_vis = "winner" if ganador == vis and ganador != "TBD" else ""
    return f"""<div class='bracket-match'><div class='bracket-team {c_loc}'><span class='team-name' title='{loc}'>{loc}</span> <span class='team-score'>{gl}</span></div><div class='bracket-team {c_vis}'><span class='team-name' title='{vis}'>{vis}</span> <span class='team-score'>{gv}</span></div></div>"""

def generar_calendario_html():
    realidad_dict = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Calendario - Porra Mundial</title><link rel="stylesheet" href="theme.css"></head><body>{get_sidebar_html("")}{get_header_html("📅 Calendario Oficial", "Resultados y Cuadro de Eliminatorias en Tiempo Real", "")}<div class="container">"""
    fase_grupos = realidad_dict.get("fase_grupos", {})
    if fase_grupos:
        html += "<details open><summary><h2>🌍 Fase de Grupos</h2></summary><div class='groups-grid'>"
        for grupo, partidos in sorted(fase_grupos.items()):
            html += f"""<div class="card" style="padding:15px; cursor:default;"><h3 style="color:var(--gold); border-bottom:1px solid #333; padding-bottom:5px;">{grupo}</h3><table style="width:100%; font-size:0.9em; margin-top:10px;">"""
            for p in partidos: html += f"<tr><td style='text-align:right; border:none; padding:5px;'>{p['local']}</td><td style='border:none; font-weight:bold; padding:5px;'>{p.get('goles_local', '-')} - {p.get('goles_visitante', '-')}</td><td style='text-align:left; border:none; padding:5px;'>{p['visitante']}</td><td style='border:none;'>{'⏳' if p.get('estado') == 'notstarted' else '✅'}</td></tr>"
            html += "</table></div>"
        html += "</div></details>"

    eliminatorias = realidad_dict.get("eliminatorias", {})
    if eliminatorias:
        html += "<details open><summary><h2>⚔️ Cuadro de Eliminatorias</h2></summary><div class='bracket-wrapper'><div class='bracket'>"
        html += "<div class='bracket-side left-side'>"
        for clave, nombre in [("dieciseisavos", "1/16"), ("octavos", "1/8"), ("cuartos", "1/4"), ("semifinales", "Semis")]:
            partidos = eliminatorias.get(clave, [])
            if not partidos and clave == "dieciseisavos": continue
            mitad = (len(partidos) + 1) // 2
            if partidos[:mitad]:
                html += f"<div class='bracket-round'><div class='round-title'>{nombre}</div>"
                for p in partidos[:mitad]: html += render_partido_bracket(p)
                html += "</div>"
        html += "</div><div class='bracket-center'>"
        final = eliminatorias.get("final", [])
        html += "<div class='center-round'><div class='round-title' style='color:var(--gold);'>🏆 FINAL</div>"
        for p in final: html += render_partido_bracket(p)
        html += "</div>"
        tercer = eliminatorias.get("tercer_puesto", [])
        if tercer:
            html += "<div class='center-round' style='margin-top:auto;'><div class='round-title' style='color:#a9b7c6;'>🥉 3º Puesto</div>"
            for p in tercer: html += render_partido_bracket(p)
            html += "</div>"
        html += "</div><div class='bracket-side right-side'>"
        for clave, nombre in [("semifinales", "Semis"), ("cuartos", "1/4"), ("octavos", "1/8"), ("dieciseisavos", "1/16")]:
            partidos = eliminatorias.get(clave, [])
            if not partidos and clave == "dieciseisavos": continue
            mitad = (len(partidos) + 1) // 2
            if partidos[mitad:]:
                html += f"<div class='bracket-round'><div class='round-title'>{nombre}</div>"
                for p in partidos[mitad:]: html += render_partido_bracket(p)
                html += "</div>"
        html += "</div></div></div></details>"
    html += "</div></body></html>"
    with open(ROOT_DIR / "calendario.html", 'w', encoding='utf-8') as f: f.write(html)

def ejecutar_07b():
    print("=======================================================")
    print(" 🌐 [07B] INICIANDO RENDERIZADO HTML FRONTEND (GLOBAL) 🌐")
    print("=======================================================")
    generar_instrucciones_html()
    generar_participantes_html()
    generar_calendario_html()
    if generar_index_html(): 
        print("✅ index.html global generado con éxito.")
    else: 
        print("❌ Error: No se encontró el ranking_oficial.csv")
    print("✅ Web base completada (Dashboards individuales en 07c).")

if __name__ == "__main__":
    ejecutar_07b()