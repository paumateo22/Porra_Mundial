import sys
import json
import csv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

CONFIG = cargar_json(ROOT_DIR / "config" / "settings.json") or {"multiplicadores": {"incremento_racha_por_fase": 0.5}}
PTS_1X2 = CONFIG.get("puntuacion", {}).get("acierto_1x2", 1)
PTS_EX = CONFIG.get("puntuacion", {}).get("acierto_exacto", 3)
PTS_PASE = CONFIG.get("puntuacion", {}).get("acierto_pase_grupo", 1)
PTS_POS = CONFIG.get("puntuacion", {}).get("acierto_posicion_grupo", 2)

def safe_num(val, is_float=False):
    try: return float(val) if is_float else int(val)
    except: return 0.0 if is_float else 0

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

def get_header_html(title, subtitle, depth=""):
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
    </header>
    """

def calcular_clasificacion_grupos(fase_grupos):
    posiciones = {}
    for grupo, partidos in fase_grupos.items():
        tabla = {}
        for p in partidos:
            loc, vis = p['local'], p['visitante']
            if loc not in tabla: tabla[loc] = {"pts": 0, "dif": 0}
            if vis not in tabla: tabla[vis] = {"pts": 0, "dif": 0}
            gl = safe_num(p.get('goles_local', 0))
            gv = safe_num(p.get('goles_visitante', 0))
            tabla[loc]["dif"] += (gl - gv)
            tabla[vis]["dif"] += (gv - gl)
            if p.get('estado', 'finished') == 'finished':
                if gl > gv: tabla[loc]["pts"] += 3
                elif gv > gl: tabla[vis]["pts"] += 3
                else: tabla[loc]["pts"] += 1; tabla[vis]["pts"] += 1
        equipos_ordenados = sorted(tabla.items(), key=lambda x: (x[1]["pts"], x[1]["dif"]), reverse=True)
        for idx, (eq, stats) in enumerate(equipos_ordenados): posiciones[eq] = idx + 1
    return posiciones

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
                        rastros.append(("Grupos", f"../../../participantes/{jugador_dir.name}/pronosticos/grupos/{jugador_dir.name}_base.json"))
                        break
        else:
            ruta_ocr = jugador_dir / "pronosticos" / "eliminatorias" / fase_origen / f"{fase_origen}.json"
            if ruta_ocr.exists():
                ocr_data = cargar_json(ruta_ocr)
                for p in ocr_data.get("predicciones", {}).get(fase_busqueda_ocr, []):
                    if p.get("local") == equipo or p.get("visitante") == equipo:
                        nombres_cortos = {"dieciseisavos": "1/16", "octavos": "1/8", "cuartos": "1/4", "semifinales": "Semis"}
                        rastros.append((nombres_cortos.get(fase_origen, fase_origen), f"../../../participantes/{jugador_dir.name}/pronosticos/eliminatorias/{fase_origen}/{fase_origen}.json"))
                        break
    return rastros

def limpiar_nombre_id(nombre):
    reemplazos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', ' ': '_'}
    res = nombre.lower()
    for orig, rep in reemplazos.items(): res = res.replace(orig, rep)
    return "".join(c for c in res if c.isalnum() or c == '_')

def generar_dashboards_html():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    total_jugadores = len(jugadores)
    
    jornadas_dict = cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    jornadas_keys = list(jornadas_dict.keys())
    realidad_dict = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    
    pos_real = calcular_clasificacion_grupos(realidad_dict.get("fase_grupos", {}))
    pasan_real = realidad_dict.get("clasificados_a_dieciseisavos", [])
    
    dict_reales = {}
    for g, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos: dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    for f, partidos in realidad_dict.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p: dict_reales[f"ID_{p['id_partido']}"] = p

    nombres_columnas_sd = ["GRUPOS", "1/16", "1/8", "1/4", "SEMIS", "FINAL", "GANADOR"]

    # Mapeo universal de fases para SD
    fases_map_sd = {
        "grupos": 0, "fase_grupos": 0, "Grupos": 0,
        "dieciseisavos": 1, "1/16": 1, "16vos": 1,
        "octavos": 2, "1/8": 2, "8vos": 2,
        "cuartos": 3, "1/4": 3,
        "semifinales": 4, "Semis": 4,
        "finales": 5, "final": 5, "Final": 5, "tercer_puesto": 5
    }

    global_sd = {}
    for j_dir in jugadores:
        libro = cargar_json(j_dir / "estadisticas" / "historial_puntos.json")
        if not libro: continue
        for eq, datos in libro.get("matriz_sorpresas_decepciones", {}).items():
            if eq not in global_sd:
                global_sd[eq] = {
                    "media": safe_num(datos["media_grupo"], is_float=True),
                    "real": safe_num(fases_map_sd.get(datos["realidad"], 0)),
                    "predicciones": []
                }
            global_sd[eq]["predicciones"].append({
                "jugador": j_dir.name.replace('_', ' ').title(),
                "fase_id": safe_num(fases_map_sd.get(datos["pronostico"], 0)),
                "pts": safe_num(datos["puntos"], is_float=True)
            })

    rankings_jornada = {}
    for j_key in jornadas_keys:
        hits = []
        for j_dir in jugadores:
            lib = cargar_json(j_dir / "estadisticas" / "historial_puntos.json") or {}
            dj = lib.get("desglose_jornadas", {}).get(j_key, {})
            hits.append((j_dir.name, dj.get("aciertos_1x2", 0)))
        hits.sort(key=lambda x: x[1], reverse=True)
        rankings_jornada[j_key] = {}
        rank = 1
        for idx, (pid, h) in enumerate(hits):
            if idx > 0 and h < hits[idx-1][1]: rank = idx + 1
            rankings_jornada[j_key][pid] = rank

    csv_data = {}
    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    if ruta_csv.exists():
        with open(ruta_csv, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f): csv_data[row['Jugador'].replace(' ', '_').lower()] = row

    # ==========================================
    # CREACIÓN DE DASHBOARDS
    # ==========================================
    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        libro = cargar_json(jugador_dir / "estadisticas" / "historial_puntos.json")
        if not libro: continue
        base_pred = cargar_json(jugador_dir / "pronosticos" / "grupos" / f"{jugador_dir.name}_base.json") or {}
        dir_vistas = jugador_dir / "vistas"
        dir_vistas.mkdir(parents=True, exist_ok=True)
        
        desglose_j = libro.get("desglose_jornadas", {})
        desglose_p = libro.get("desglose_partidos", {})
        premios = libro.get("premios_finales", {}).get("formularios", {}).get("detalles", {})
        j_row = csv_data.get(jugador_dir.name, {})
        pts_extra_totales = float(j_row.get('Puntos_Podio', 0)) + float(j_row.get('Puntos_Forms', 0))
        
        total_1x2 = sum(1 for p in desglose_p.values() if p.get("acierto_1x2"))
        total_exactos = sum(1 for p in desglose_p.values() if p.get("acierto_exacto"))
        victorias_j = sum(1 for j in desglose_j.values() if j.get("resultado") == "Ganador")
        derrotas_j = sum(1 for j in desglose_j.values() if j.get("resultado") == "Perdedor")
        
        pos_pred = calcular_clasificacion_grupos(base_pred.get("fase_grupos", {}))
        pasan_pred = base_pred.get("clasificados_a_dieciseisavos", [])
        aciertos_pase = sum(1 for eq in pasan_real if eq in pasan_pred)
        aciertos_pos = sum(1 for eq in pasan_real if eq in pasan_pred and pos_pred.get(eq) == pos_real.get(eq))

        pos_csv = j_row.get('Posicion', '-')
        pos_display = pos_csv + "º"
        if pos_csv == "1": pos_display = "🥇 1º"
        elif pos_csv == "2": pos_display = "🥈 2º"
        elif pos_csv == "3": pos_display = "🥉 3º"

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfil de {nombre}</title>
    <link rel="stylesheet" href="../../../theme.css">
    <script>
        function openTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.currentTarget.classList.add('active');
        }}
        function showSD(eqId) {{
            const target = document.getElementById('sd-' + eqId);
            const isVisible = target.style.display === 'block';
            document.querySelectorAll('.sd-detail-panel').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.sd-flag-btn').forEach(el => el.classList.remove('active'));
            if (!isVisible) {{
                target.style.display = 'block';
                event.currentTarget.classList.add('active');
            }}
        }}
    </script>
</head>
<body>
    {get_sidebar_html("../../../")}
    {get_header_html(f"👤 Dashboard: {nombre}", f"Posición Actual: <strong>{pos_display}</strong> | Puntos Totales: <strong style='color:var(--gold); font-size:1.2em;'>{j_row.get('TOTAL', 0)}</strong>", "../../../")}
    <div class="container">
"""
        # ==========================================
        # 1. INFORMACIÓN GENERAL (ANCHO COMPLETO)
        # ==========================================
        html += f"""
        <details open>
            <summary><h2>📊 Información General</h2></summary>
            <div class="table-wrapper" style="margin-bottom: 20px;">
                <table>
                    <tr>
                        <th>Aciertos<br><span style="font-size:0.8em">(Ex / 1x2)</span></th>
                        <th>Pase Elim.<br><span style="font-size:0.8em">(Pos / Pasan)</span></th>
                        <th>Sorpresa | Decepción</th><th>Extras<br>(Premios)</th><th>Récord<br>(W / L)</th><th>Total</th>
                    </tr>
                    <tr>
                        <td>{total_exactos} / {total_1x2}</td>
                        <td>{aciertos_pos} / {aciertos_pase}</td>
                        <td>+{premios.get('sorpresa', 0)} | +{premios.get('decepcion', 0)}</td>
                        <td>{pts_extra_totales:.2f}</td>
                        <td>{victorias_j}W - {derrotas_j}L</td>
                        <td class="pts-totales">{j_row.get('TOTAL', 0)}</td>
                    </tr>
                </table>
            </div>

            <div class="table-wrapper" style="margin-bottom: 10px;">
                <table>
                    <tr>
        """
        for j_key in jornadas_keys: html += f"<th>{j_key.upper()}</th>"
        html += "</tr><tr>"
        for j_key in jornadas_keys:
            info_j = desglose_j.get(j_key)
            if not info_j:
                html += "<td>-</td>"
                continue
            ex_j = sum(1 for p in jornadas_dict.get(j_key, []) if desglose_p.get(f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}", {}).get("acierto_exacto"))
            ac_1x2_j = info_j.get("acierto_1x2", info_j.get("aciertos_1x2", 0))
            pts_j = sum(desglose_p.get(f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}", {}).get("puntos_conseguidos", 0) for p in jornadas_dict.get(j_key, [])) + info_j.get("puntos_bono", 0)
            
            pts_str = f"+{pts_j}" if pts_j > 0 else f"{pts_j}"
            res = info_j.get("resultado", "")
            clase_css = ' class="ganador-jornada"' if res == "Ganador" else (' class="perdedor-jornada"' if res == "Perdedor" else "")
            html += f"<td{clase_css}><strong>{ex_j} / {ac_1x2_j}</strong><br><span style='font-size:0.85em; font-weight:normal; opacity:0.85;'>{pts_str} pts</span></td>"
        html += "</tr></table></div></details>"

        # ==========================================
        # 2. ÚLTIMOS DESEMPEÑOS (GRID 2x2)
        # ==========================================
        ultimos_terminados = []
        for g, partidos in realidad_dict.get("fase_grupos", {}).items():
            for p in partidos:
                if p.get("estado") == "finished": ultimos_terminados.append({"fase": g, "data": p, "limpia": "grupos"})
        for clave, nombre_fase in [("dieciseisavos", "1/16"), ("octavos", "1/8"), ("cuartos", "1/4"), ("semifinales", "Semis"), ("tercer_puesto", "3º Puesto"), ("final", "Final")]:
            for p in realidad_dict.get("eliminatorias", {}).get(clave, []):
                if p.get("estado") == "finished": ultimos_terminados.append({"fase": nombre_fase, "data": p, "limpia": clave})
                
        ultimos_4 = ultimos_terminados[-4:]
        ultimos_4.reverse()
        
        if ultimos_4:
            html += """<details open><summary><h2>🔥 Últimos Desempeños</h2></summary><div class="latest-grid" style="margin-bottom:30px;">"""
            dict_preds = {}
            for p_list in base_pred.get("fase_grupos", {}).values():
                for pp in p_list: dict_preds[f"{pp['local']}_vs_{pp['visitante']}"] = pp
            for f_k in ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]:
                f_data = cargar_json(jugador_dir / "pronosticos" / "eliminatorias" / f_k / f"{f_k}.json") or {}
                for f_dest, p_list in f_data.get("predicciones", {}).items():
                    r_fase = realidad_dict.get("eliminatorias", {}).get("tercer_puesto", []) + realidad_dict.get("eliminatorias", {}).get("final", []) if f_dest in ["finales", "final", "tercer_puesto"] else realidad_dict.get("eliminatorias", {}).get(f_dest, [])
                    for i, p_rl in enumerate(r_fase):
                        if i < len(p_list): dict_preds[f"ID_{p_rl['id_partido']}"] = p_list[i]

            for u_match in ultimos_4:
                p_real = u_match["data"]
                loc_r, vis_r = p_real.get("local", ""), p_real.get("visitante", "")
                clave = f"ID_{p_real['id_partido']}" if "id_partido" in p_real else f"{loc_r}_vs_{vis_r}"
                info_p = desglose_p.get(clave, {})
                p_pred = dict_preds.get(clave, {})
                
                if p_pred:
                    loc_p, vis_p = p_pred.get("local", ""), p_pred.get("visitante", "")
                    pred_txt = f"{loc_p} {p_pred.get('goles_local','-')}-{p_pred.get('goles_visitante','-')} {vis_p}" if (loc_p != loc_r or vis_p != vis_r) else f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}"
                else: pred_txt = "-"

                ac_ex, ac_1x2 = info_p.get("acierto_exacto", False), info_p.get("acierto_1x2", False)
                mult = info_p.get("multiplicador_aplicado", 1.0)
                
                if ac_ex: 
                    pred_styled = f"<span class='pred-exact'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[{PTS_1X2} Ac + {PTS_EX} Ex] &times; {mult}</span>"
                elif ac_1x2: 
                    pred_styled = f"<span class='pred-1x2'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[{PTS_1X2} Ac] &times; {mult}</span>"
                else: 
                    pred_styled = f"<span class='pred-miss'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:gray; font-size:0.85em;'>0 pts</span>"

                # Multiplicador Desplegable interno
                mult_html = f"x{mult}"
                if mult > 1.0:
                    r_loc = obtener_racha_fases(jugador_dir, p_real.get("local"), u_match["limpia"])
                    r_vis = obtener_racha_fases(jugador_dir, p_real.get("visitante"), u_match["limpia"])
                    content_html = ""
                    if r_loc:
                        content_html += f"<strong>{p_real.get('local')}:</strong><br>"
                        for r in r_loc: content_html += f"<a href='{r[1]}' target='_blank' class='mult-link'>+{CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a><br>"
                    if r_vis:
                        content_html += f"<strong>{p_real.get('visitante')}:</strong><br>"
                        for r in r_vis: content_html += f"<a href='{r[1]}' target='_blank' class='mult-link'>+{CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a><br>"
                    if content_html:
                        mult_html = f"<details class='mult-details'><summary>x{mult} ▼</summary><div class='mult-content'>{content_html}</div></details>"

                html += f"""
                <details class="match-card">
                    <summary>
                        <div class="match-header">{u_match['fase']}</div>
                        <div class="match-score">{loc_r} <span>{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}</span> {vis_r}</div>
                    </summary>
                    <div class="match-breakdown" style="padding:15px; text-align:center;">
                        <p style="margin:5px 0;">Tu Pronóstico: <strong>{pred_styled}</strong></p>
                        <p style="margin:5px 0;">Mult: {mult_html}</p>
                        <p style="margin:5px 0; font-size:1.1em;">Puntos: <strong style="color:var(--gold);">{info_p.get('puntos_conseguidos', 0)}</strong></p>
                    </div>
                </details>"""
            html += "</div></details>"

        # ==========================================
        # 3. SECCIÓN FASE DE GRUPOS (JaJ / GaG)
        # ==========================================
        html += """
        <details open>
            <summary><h2>🌍 Fase de Grupos</h2></summary>
            <div class="tabs-container">
                <button class="tab-btn active" onclick="openTab('tab-grupos-jaj')">Jornada a Jornada (JaJ)</button>
                <button class="tab-btn" onclick="openTab('tab-grupos-gag')">Grupo a Grupo (GaG)</button>
            </div>
            
            <div id="tab-grupos-jaj" class="tab-content active">
        """
        pts_grupos_acum = 0
        jornadas_grupos = [k for k in jornadas_keys if k.startswith("J")]
        
        for j_key in jornadas_grupos:
            html += f"<div style='margin-bottom:20px; background:#151515; padding:15px; border-radius:6px; border:1px solid #222;'><h3 style='color:var(--table-header); margin-top:0;'>📌 {j_key.upper()}</h3>"
            html += "<div class='table-wrapper'><table><tr><th>Partido Oficial</th><th>Tu Pronóstico</th><th>Resultado Real</th><th>Mult.</th><th>Pts</th></tr>"
            
            pts_jornada = exactos_j = 0
            for p in jornadas_dict[j_key]:
                clave = f"{p['local']}_vs_{p['visitante']}"
                info_p = desglose_p.get(clave, {})
                p_real = dict_reales.get(clave, {})
                p_pred = dict_preds.get(clave, {})
                
                loc_r, vis_r = p_real.get("local", "TBD"), p_real.get("visitante", "TBD")
                pred_txt = f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}" if p_pred else "-"
                real_txt = f"{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}" if p_real.get("estado") == "finished" else "⏳"
                
                ac_ex, ac_1x2 = info_p.get("acierto_exacto", False), info_p.get("acierto_1x2", False)
                if ac_ex: pred_styled = f"<span class='pred-exact'>{pred_txt} ({PTS_1X2} + {PTS_EX})</span>"
                elif ac_1x2: pred_styled = f"<span class='pred-1x2'>{pred_txt} ({PTS_1X2})</span>"
                else: pred_styled = f"<span class='pred-miss'>{pred_txt} (0)</span>"

                pts = info_p.get("puntos_conseguidos", 0)
                if ac_ex: exactos_j += 1
                pts_grupos_acum += pts
                pts_jornada += pts
                
                html += f"<tr><td>{loc_r} - {vis_r}</td><td>{pred_styled}</td><td><strong>{real_txt}</strong></td><td>x{info_p.get('multiplicador_aplicado', 1.0)}</td><td style='color:var(--gold); font-weight:bold;'>{pts}</td></tr>"

            info_dj = desglose_j.get(j_key, {})
            res_bono = info_dj.get("resultado", "Neutral")
            rank_j = rankings_jornada.get(j_key, {}).get(jugador_dir.name, "-")
            
            html += f"""</table></div>
            <div style="background:#111; padding:10px; margin-top:5px; border-left:4px solid var(--gold); border-radius:4px; font-size:0.9em; line-height:1.4;">
                Resumen {j_key.upper()}: <strong>{exactos_j}/{info_dj.get('aciertos_1x2', 0)}</strong> (Clavados/Aciertos). Posición <strong>{rank_j} de {total_jugadores}</strong>.<br>
                Resultado: <strong>{res_bono}</strong> ({info_dj.get('puntos_bono', 0)} pts)<br>
                <span style="color:var(--gold);">TOTAL JORNADA: <strong>{pts_jornada + info_dj.get('puntos_bono', 0)} pts</strong></span>
            </div></div>"""

        html += "</div>" # Cierre Tab JaJ

        # html += """<div id="tab-grupos-gag" class="tab-content"><div class="groups-grid">"""
        for grupo, partidos in sorted(base_pred.get("fase_grupos", {}).items()):
            html += f"""<div class="card" style="padding:15px; cursor:default;"><h3 style="color:var(--gold); border-bottom:1px solid #333; padding-bottom:5px; margin-top:0;">{grupo}</h3><table class="gag-table">"""
            pts_grupo = 0
            for p in partidos:
                clave = f"{p['local']}_vs_{p['visitante']}"
                info_p = desglose_p.get(clave, {})
                p_real = dict_reales.get(clave, {})
                
                real_txt = f"{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}" if p_real.get("estado") == "finished" else "⏳"
                pred_txt = f"{p.get('goles_local','-')} - {p.get('goles_visitante','-')}"
                
                ac_ex, ac_1x2 = info_p.get("acierto_exacto", False), info_p.get("acierto_1x2", False)
                if ac_ex: pred_styled = f"<span class='pred-exact'>{pred_txt} ({PTS_1X2} + {PTS_EX})</span>"
                elif ac_1x2: pred_styled = f"<span class='pred-1x2'>{pred_txt} ({PTS_1X2})</span>"
                else: pred_styled = f"<span class='pred-miss'>{pred_txt} (0)</span>"
                
                pts = info_p.get("puntos_conseguidos", 0)
                pts_grupo += pts
                
                html += f"""<tr class="gag-match-row"><td style="text-align:right; width:40%;">{p['local']}</td><td style="width:20%;">{real_txt}</td><td style="text-align:left; width:40%;">{p['visitante']}</td></tr>
                            <tr class="gag-pred-row"><td colspan="3" style="padding-top:2px; padding-bottom:8px; color:gray;">Pronóstico: {pred_styled} <span style="float:right; color:var(--gold);">{pts} pts</span></td></tr>"""
            html += f"""<tr><td colspan="3" class="gag-total-row">Total Grupo: {pts_grupo} pts</td></tr></table></div>"""
        html += "</div></div></details>" # Cierre Tab GaG y Bloque Grupos

        # ==========================================
        # 4. BALANCE FASE DE GRUPOS
        # ==========================================
        pts_bono_fase = libro.get("resolucion_fase_grupos", {}).get("puntos_conseguidos", 0)
        html += f"""
        <details open>
            <summary><h2>⚖️ Balance Fase de Grupos</h2></summary>
            <div style="text-align:center; font-size:1.1em; margin-bottom:15px;">
                Resumen: <strong>{aciertos_pos}/{aciertos_pase}</strong> (Clavados Pos. / Aciertos Pase) | Total Sumado: <strong style="color:var(--gold);">+{pts_bono_fase} pts</strong>
            </div>
            <div class="table-wrapper"><table>
                <tr><th>Equipo</th><th>Pasa (Tú)</th><th>Pos (Tú)</th><th>Pasa (Real)</th><th>Pos (Real)</th><th>Acierto Pase</th><th>Acierto Posición</th><th>Pts</th></tr>
        """
        for eq in sorted(list(pos_real.keys())):
            p_tu = "✅" if eq in pasan_pred else "❌"
            p_rl = "✅" if eq in pasan_real else "❌"
            pos_tu, pos_rl = f"{pos_pred.get(eq, '-')}º", f"{pos_real.get(eq, '-')}º"
            if eq in pasan_real:
                if eq in pasan_pred:
                    ac_pase = f"🎯 (+{PTS_PASE})"; pts_eq = PTS_PASE
                    if pos_pred.get(eq) == pos_real.get(eq): ac_pos = f"🎯 (+{PTS_POS})"; pts_eq += PTS_POS
                    else: ac_pos = "❌"
                else: ac_pase = ac_pos = "❌"; pts_eq = 0
            else: ac_pase = ac_pos = "-"; pts_eq = 0
            html += f"<tr><td>{eq}</td><td>{p_tu}</td><td>{pos_tu}</td><td>{p_rl}</td><td>{pos_rl}</td><td>{ac_pase}</td><td>{ac_pos}</td><td style='color:var(--gold); font-weight:bold;'>{pts_eq}</td></tr>"
        html += "</table></div></details>"

        # ==========================================
        # 5. ELIMINATORIAS (Estilo JaJ)
        # ==========================================
        jornadas_elim = [k for k in jornadas_keys if not k.startswith("J")]
        if jornadas_elim:
            html += """<details open><summary><h2>⚔️ Eliminatorias</h2></summary>"""
            for j_key in jornadas_elim:
                fase_limpia = j_key.split(".")[0] if "." in j_key else j_key
                html += f"<div style='margin-bottom:20px; background:#151515; padding:15px; border-radius:6px; border:1px solid #222;'><h3 style='color:var(--accent); margin-top:0;'>📌 {j_key.upper()}</h3>"
                html += "<div class='table-wrapper'><table><tr><th>Partido Oficial</th><th>Tu Pronóstico</th><th>Resultado Real</th><th>Mult.</th><th>Origen Extra</th><th>Pts</th></tr>"
                
                pts_jornada = exactos_j = 0
                for p in jornadas_dict[j_key]:
                    clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                    info_p = desglose_p.get(clave, {})
                    p_real = dict_reales.get(clave, {})
                    p_pred = dict_preds.get(clave, {})
                    
                    loc_r, vis_r = p_real.get("local", "TBD"), p_real.get("visitante", "TBD")
                    if loc_r == "TBD" and "id_partido" in p: loc_r, vis_r = f"Eq. {p['id_partido']}A", f"Eq. {p['id_partido']}B"
                    
                    if p_pred:
                        loc_p, vis_p = p_pred.get("local", ""), p_pred.get("visitante", "")
                        pred_txt = f"{loc_p} {p_pred.get('goles_local','-')}-{p_pred.get('goles_visitante','-')} {vis_p}" if (loc_p != loc_r or vis_p != vis_r) else f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}"
                    else: pred_txt = "-"
                    
                    real_txt = f"{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}" if p_real.get("estado") == "finished" else "⏳"
                    
                    ac_ex, ac_1x2 = info_p.get("acierto_exacto", False), info_p.get("acierto_1x2", False)
                    if ac_ex: pred_styled = f"<span class='pred-exact'>{pred_txt} ({PTS_1X2} + {PTS_EX})</span>"
                    elif ac_1x2: pred_styled = f"<span class='pred-1x2'>{pred_txt} ({PTS_1X2})</span>"
                    else: pred_styled = f"<span class='pred-miss'>{pred_txt} (0)</span>"

                    pts = info_p.get("puntos_conseguidos", 0)
                    mult = info_p.get("multiplicador_aplicado", 1.0)
                    if ac_ex: exactos_j += 1
                    pts_jornada += pts
                    
                    origen_txt = "-"
                    if mult > 1.0 and p_real.get("estado") == "finished":
                        r_loc = obtener_racha_fases(jugador_dir, p_real.get("local"), fase_limpia)
                        r_vis = obtener_racha_fases(jugador_dir, p_real.get("visitante"), fase_limpia)
                        det = []
                        if r_loc: det.append(f"<strong>{p_real.get('local')}</strong>:<br>" + "<br>".join([f"<a href='{r[1]}' target='_blank' class='mult-link'>+{CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a>" for r in r_loc]))
                        if r_vis: det.append(f"<strong>{p_real.get('visitante')}</strong>:<br>" + "<br>".join([f"<a href='{r[1]}' target='_blank' class='mult-link'>+{CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a>" for r in r_vis]))
                        if det: origen_txt = "<hr style='border:none; border-top:1px dashed #444; margin:5px 0;'>".join(det)
                        
                    html += f"<tr><td>{loc_r} - {vis_r}</td><td>{pred_styled}</td><td><strong>{real_txt}</strong></td><td>x{mult}</td><td style='font-size:0.8em; text-align:left;'>{origen_txt}</td><td style='color:var(--gold); font-weight:bold;'>{pts}</td></tr>"

                info_dj = desglose_j.get(j_key, {})
                res_bono = info_dj.get("resultado", "Neutral")
                rank_j = rankings_jornada.get(j_key, {}).get(jugador_dir.name, "-")
                
                html += f"""</table></div>
                <div style="background:#111; padding:10px; margin-top:5px; border-left:4px solid var(--gold); border-radius:4px; font-size:0.9em; line-height:1.4;">
                    Resumen {j_key.upper()}: <strong>{exactos_j}/{info_dj.get('aciertos_1x2', 0)}</strong> (Clavados/Aciertos). Posición <strong>{rank_j} de {total_jugadores}</strong>.<br>
                    Resultado: <strong>{res_bono}</strong> ({info_dj.get('puntos_bono', 0)} pts)<br>
                    <span style="color:var(--gold);">TOTAL JORNADA: <strong>{pts_jornada + info_dj.get('puntos_bono', 0)} pts</strong></span>
                </div></div>"""
            html += "</details>"

        # ==========================================
        # 6. SORPRESAS Y DECEPCIONES (FLAGS GRID)
        # ==========================================
        matriz_sd = libro.get("matriz_sorpresas_decepciones", {})
        if matriz_sd:
            html += """
        <details>
            <summary><h2>🎯 Sorpresas y Decepciones</h2></summary>
            <p style="font-size:0.9em; color:#aaa; margin-bottom:20px;">Selecciona un país para ver tu desviación respecto a la media global.</p>
            <div class="sd-flag-grid">
            """
            for eq in sorted(matriz_sd.keys()):
                eq_id = limpiar_nombre_id(eq)
                html += f"""<div class="sd-flag-btn" onclick="showSD('{eq_id}')">{eq}</div>"""
            html += "</div><div id='sd-details-container'>"
            
            for eq, datos in sorted(matriz_sd.items()):
                eq_id = limpiar_nombre_id(eq)
                M_val = safe_num(datos["media_grupo"], is_float=True)
                R_val = safe_num(fases_map_sd.get(datos["realidad"], 0))
                P_val = safe_num(fases_map_sd.get(datos["pronostico"], 0))
                U_val = safe_num(datos.get("umbral_aplicado", 1.0), is_float=True)
                
                timeline_html = ""
                for idx_fase, nom_fase in enumerate(nombres_columnas_sd):
                    inds_html = ""
                    if idx_fase == round(M_val): inds_html += "<div class='sd-indicator ind-media'>Media</div>"
                    if idx_fase == R_val: inds_html += "<div class='sd-indicator ind-real'>Real</div>"
                    if idx_fase == P_val: inds_html += "<div class='sd-indicator ind-tu'>Tú</div>"
                    
                    bg_col = "#1a1a1a"
                    if idx_fase <= (M_val - U_val): bg_col = "rgba(248, 113, 113, 0.15)"
                    elif idx_fase >= (M_val + U_val): bg_col = "rgba(74, 222, 128, 0.15)"
                    
                    pills_html = ""
                    for p_data in global_sd.get(eq, {}).get("predicciones", []):
                        if p_data["fase_id"] == idx_fase:
                            c_win = "win" if p_data["pts"] > 0 else ""
                            pills_html += f"<span class='sd-player-pill {c_win}'>{p_data['jugador']}</span>"
                            
                    timeline_html += f"""
                    <div class="sd-phase-col" style="background:{bg_col};">
                        <div style="min-height:45px; margin-bottom:5px;">{inds_html}</div>
                        <div class="sd-phase-title">{nom_fase}</div>
                        <div class="sd-players-list">{pills_html}</div>
                    </div>"""

                html += f"""
                <div id="sd-{eq_id}" class="sd-detail-panel">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #444; padding-bottom:10px;">
                        <h3 style="margin:0; color:var(--gold); font-size:1.5em;">{eq}</h3>
                        <div style="text-align:right;">
                            <span style="font-size:1.2em; font-weight:bold; color:var(--gold);">{datos['puntos']} pts</span><br>
                            <span style="font-size:0.8em; color:gray;">Resultado: {datos['resultado_calculo']}</span>
                        </div>
                    </div>
                    <div class="sd-timeline">{timeline_html}</div>
                    <p style="font-size:0.8em; color:gray; text-align:center; margin-top:15px;">Umbral de acierto: ±{U_val:.1f} fases desde la Media ({M_val:.1f}). Los jugadores en verde sumaron puntos.</p>
                </div>"""
            html += "</div></details>"

        html += "</div></body></html>"
        with open(dir_vistas / "dashboard.html", 'w', encoding='utf-8') as f:
            f.write(html)

def ejecutar_07c():
    print("=======================================================")
    print(" 📊 [07C] GENERANDO DASHBOARDS INDIVIDUALES FRONTEND 📊")
    print("=======================================================")
    generar_dashboards_html()
    print("✅ Dashboards de participantes generados con éxito.")

if __name__ == "__main__":
    ejecutar_07c()