import sys
import csv
import math
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

PTS_1X2 = html_utils.CONFIG.get("puntuacion", {}).get("acierto_1x2", 1)
PTS_EX = html_utils.CONFIG.get("puntuacion", {}).get("acierto_exacto", 3)
PTS_PASE = html_utils.CONFIG.get("puntuacion", {}).get("acierto_pase_grupo", 1)
PTS_POS = html_utils.CONFIG.get("puntuacion", {}).get("acierto_posicion_grupo", 2)
UMB_R_P = html_utils.CONFIG.get("sorpresas_decepciones_config", {}).get("distancia_maxima_pronostico_realidad", 1.0)

def safe_num(val, is_float=False):
    try: return float(val) if is_float else int(val)
    except: return 0.0 if is_float else 0

def limpiar_nombre_id(nombre):
    reemplazos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', ' ': '_'}
    res = str(nombre).lower()
    for orig, rep in reemplazos.items(): res = res.replace(orig, rep)
    return "".join(c for c in res if c.isalnum() or c == '_')

def format_fase(fase):
    mapeo = {
        "dieciseisavos.1": "1/16-1",
        "dieciseisavos.2": "1/16-2",
        "dieciseisavos": "1/16",
        "octavos": "1/8",
        "cuartos": "1/4",
        "semifinales": "1/2",
        "finales": "Finales",
        "tercer_puesto": "3º Puesto",
        "final": "Final"
    }
    return mapeo.get(fase.lower(), fase.upper())

def map_fase_to_num(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        f = str(val).lower().strip()
        if f in ["grupos", "fase_grupos", "fase de grupos", "grupo"]: return 0
        if f in ["dieciseisavos", "1/16", "16vos", "dieciseisavos.1", "dieciseisavos.2"]: return 1
        if f in ["octavos", "1/8", "8vos"]: return 2
        if f in ["cuartos", "1/4"]: return 3
        if f in ["semifinales", "semis", "1/2"]: return 4
        if f in ["finales", "final", "tercer_puesto", "3º puesto", "ganador"]: return 5
        return 0

def esta_bloqueado(fase):
    horarios = html_utils.CONFIG.get("horarios", {})
    fecha_str = horarios.get(f"apertura_{fase}")
    if not fecha_str:
        return False, ""
    
    try:
        fecha_apertura = datetime.fromisoformat(fecha_str).replace(tzinfo=ZoneInfo("Europe/Madrid"))
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        if ahora < fecha_apertura:
            return True, fecha_apertura.strftime("%d/%m/%Y a las %H:%M")
    except Exception:
        pass
    return False, ""

def generar_dashboards_html():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    total_jugadores = len(jugadores)
    
    jornadas_dict = html_utils.cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    jornadas_keys = list(jornadas_dict.keys())
    realidad_dict = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    global_sd = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "global_sd.json") or {}
    
    pos_real = html_utils.calcular_clasificacion_grupos(realidad_dict.get("fase_grupos", {}))
    pasan_real = realidad_dict.get("clasificados_a_dieciseisavos", [])
    
    dict_reales = {}
    for g, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos: dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    for f, partidos in realidad_dict.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p: dict_reales[f"ID_{p['id_partido']}"] = p

    nombres_columnas_sd = ["GRUPOS", "1/16", "1/8", "1/4", "1/2", "FINAL"]

    rankings_jornada = {}
    for j_key in jornadas_keys:
        hits = []
        for j_dir in jugadores:
            lib = html_utils.cargar_json(j_dir / "estadisticas" / "historial_puntos.json") or {}
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

    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        libro = html_utils.cargar_json(jugador_dir / "estadisticas" / "historial_puntos.json")
        if not libro: continue
        base_pred = html_utils.cargar_json(jugador_dir / "pronosticos" / "grupos" / f"{jugador_dir.name}_base.json") or {}
        dir_vistas = jugador_dir / "vistas"
        dir_vistas.mkdir(parents=True, exist_ok=True)
        
        dict_preds_global = {}
        for p_list in base_pred.get("fase_grupos", {}).values():
            for pp in p_list: dict_preds_global[f"{pp['local']}_vs_{pp['visitante']}"] = pp
        for f_k in ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]:
            f_data = html_utils.cargar_json(jugador_dir / "pronosticos" / "eliminatorias" / f_k / f"{f_k}.json") or {}
            for f_dest, p_list in f_data.get("predicciones", {}).items():
                r_fase = realidad_dict.get("eliminatorias", {}).get("tercer_puesto", []) + realidad_dict.get("eliminatorias", {}).get("final", []) if f_dest in ["finales", "final", "tercer_puesto"] else realidad_dict.get("eliminatorias", {}).get(f_dest, [])
                for i, p_rl in enumerate(r_fase):
                    if i < len(p_list): dict_preds_global[f"ID_{p_rl['id_partido']}"] = p_list[i]

        desglose_j = libro.get("desglose_jornadas", {})
        desglose_p = libro.get("desglose_partidos", {})
        premios = libro.get("premios_finales", {}).get("formularios", {}).get("detalles", {})
        j_row = csv_data.get(jugador_dir.name, {})
        pts_extra_totales = float(j_row.get('Puntos_Podio', 0)) + float(j_row.get('Puntos_Forms', 0))
        
        total_1x2 = sum(1 for p in desglose_p.values() if p.get("acierto_1x2"))
        total_exactos = sum(1 for p in desglose_p.values() if p.get("acierto_exacto"))
        victorias_j = sum(1 for j in desglose_j.values() if j.get("resultado") == "Ganador")
        derrotas_j = sum(1 for j in desglose_j.values() if j.get("resultado") == "Perdedor")
        
        pos_pred = html_utils.calcular_clasificacion_grupos(base_pred.get("fase_grupos", {}))
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
    <style>
        .sticky-nav {{ position: sticky; top: 0; z-index: 100; background: rgba(18,18,18,0.95); padding: 12px; border-bottom: 2px solid var(--gold); display: flex; gap: 10px; justify-content: center; overflow-x: auto; flex-wrap: nowrap; backdrop-filter: blur(5px); box-shadow: 0 4px 10px rgba(0,0,0,0.5); }}
        .sticky-nav a {{ text-decoration:none; font-size:0.85em; font-weight:bold; white-space:nowrap; background:#333; color:white; padding:8px 15px; border-radius:4px; border:1px solid #444; transition:0.3s; }}
        .sticky-nav a:hover {{ background:var(--gold); color:black; border-color:var(--gold); }}

        .match-grid-2col {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
        .group-grid-2col {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
        .group-grid-4col {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
        @media (max-width: 950px) {{ .group-grid-4col {{ grid-template-columns: repeat(2, 1fr); }} }}
        @media (max-width: 768px) {{ .match-grid-2col, .group-grid-2col, .group-grid-4col {{ grid-template-columns: 1fr; }} }}
        
        .pred-summary {{ margin:0; cursor:pointer; list-style:none; outline:none; }}
        .pred-summary::-webkit-details-marker {{ display:none; }}
        .pred-summary::marker {{ display:none; }}
        .jornada-details > summary h3::after, .jornada-details > summary h2::after {{ content: ' ▼'; font-size: 0.7em; color: gray; transition: 0.3s; margin-left: 8px; }}
        .jornada-details[open] > summary h3::after, .jornada-details[open] > summary h2::after {{ content: ' ▲'; color: var(--gold); }}
        .pred-card-details {{ margin:0 auto; width: 100%; max-width: 350px; background: #1a1a1a; padding: 10px; border-radius: 6px; border: 1px solid #333; }}
        .pred-card-details[open] {{ background: #1f1f1f; }}
        
        /* SD CONTINUAS */
        .sd-indicator {{ display: block; padding: 4px; border-radius: 4px; font-size: 0.85em; font-weight: bold; margin-bottom: 5px; width: 100%; box-sizing: border-box; text-align: center; border:1px solid transparent; }}
        .ind-real {{ background: var(--gold); color: black; }}
        .ind-media {{ background: white; color: black; box-shadow: 0 0 5px white; }}
        .ind-tu {{ background: #3b82f6; color: white; }}
        .sd-player-pill {{ display: block; background: #252525; font-size: 0.85em; padding: 6px; border-radius: 4px; color: #ccc; text-align: center; border: 1px solid transparent; transition: 0.2s; }}
        .sd-player-pill:hover {{ border-color: var(--gold); background: #333; color: white; }}
        .sd-player-pill.win-sorp {{ background: rgba(74, 222, 128, 0.15); border-color: #4ade80; color: #4ade80; font-weight: bold; }}
        .sd-player-pill.win-dec {{ background: rgba(248, 113, 113, 0.15); border-color: #f87171; color: #f87171; font-weight: bold; }}
        .ind-tu-pill {{ background: #3b82f6 !important; color: white !important; font-weight: bold; border-color: #2563eb !important; }}
        .ind-tu-pill.win-sorp {{ background: #22c55e !important; color: black !important; border-color: #16a34a !important; }}
        .ind-tu-pill.win-dec {{ background: #ef4444 !important; color: black !important; border-color: #dc2626 !important; }}
    </style>
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
    {html_utils.get_sidebar_html("../../../")}
    {html_utils.get_header_html(f"👤 Dashboard: {nombre}", f"Posición Actual: <strong>{pos_display}</strong> | Puntos Totales: <strong style='color:var(--gold); font-size:1.2em;'>{j_row.get('TOTAL', 0)}</strong>", "../../../")}
    
    <div class="sticky-nav">
        <a href="pronostico_grupos.html">📓 Pronósticos</a>
        <a href="#info">📊 Info General</a>
        <a href="#ultimos">🔥 Últimos</a>
        <a href="#grupos">🌍 Grupos</a>
        <a href="#balance">⚖️ Balance</a>
        <a href="#eliminatorias">⚔️ Eliminatorias</a>
        <a href="#sd">🎯 Sorpresas y Decepciones</a>
    </div>

    <div class="container">
    """
        html += f"""
        <details id="pronosticos" class="jornada-details" open style="margin-bottom: 20px; background:#151515; padding:15px; border-radius:8px; border:1px solid #333;">
            <summary style="cursor:pointer; border:none; outline:none;">
                <h2 style="display:inline-block; margin-top:0; color:var(--gold);">📓 Tus Pronósticos (Cápsula del Tiempo)</h2>
            </summary>
            <div style="display:flex; flex-wrap:wrap; gap:10px; justify-content:center;">
                <a href="pronostico_grupos.html" style="text-decoration:none; padding:8px 15px; border-radius:4px; background:#222; color:white; border:1px solid #444; font-weight:bold; transition:0.3s;" onmouseover="this.style.borderColor='var(--gold)'; this.style.color='var(--gold)';" onmouseout="this.style.borderColor='#444'; this.style.color='white';">🌍 Grupos</a>
                <a href="pronostico_dieciseisavos.html" style="text-decoration:none; padding:8px 15px; border-radius:4px; background:#222; color:white; border:1px solid #444; font-weight:bold; transition:0.3s;" onmouseover="this.style.borderColor='var(--gold)'; this.style.color='var(--gold)';" onmouseout="this.style.borderColor='#444'; this.style.color='white';">⚔️ 1/16</a>
                <a href="pronostico_octavos.html" style="text-decoration:none; padding:8px 15px; border-radius:4px; background:#222; color:white; border:1px solid #444; font-weight:bold; transition:0.3s;" onmouseover="this.style.borderColor='var(--gold)'; this.style.color='var(--gold)';" onmouseout="this.style.borderColor='#444'; this.style.color='white';">⚔️ 1/8</a>
                <a href="pronostico_cuartos.html" style="text-decoration:none; padding:8px 15px; border-radius:4px; background:#222; color:white; border:1px solid #444; font-weight:bold; transition:0.3s;" onmouseover="this.style.borderColor='var(--gold)'; this.style.color='var(--gold)';" onmouseout="this.style.borderColor='#444'; this.style.color='white';">⚔️ 1/4</a>
                <a href="pronostico_semifinales.html" style="text-decoration:none; padding:8px 15px; border-radius:4px; background:#222; color:white; border:1px solid #444; font-weight:bold; transition:0.3s;" onmouseover="this.style.borderColor='var(--gold)'; this.style.color='var(--gold)';" onmouseout="this.style.borderColor='#444'; this.style.color='white';">⚔️ Semis</a>
                <a href="pronostico_finales.html" style="text-decoration:none; padding:8px 15px; border-radius:4px; background:#222; color:white; border:1px solid #444; font-weight:bold; transition:0.3s;" onmouseover="this.style.borderColor='var(--gold)'; this.style.color='var(--gold)';" onmouseout="this.style.borderColor='#444'; this.style.color='white';">🏆 Finales</a>
                <a href="pronostico_premios.html" style="text-decoration:none; padding:8px 15px; border-radius:4px; background:#222; color:white; border:1px solid #444; font-weight:bold; transition:0.3s;" onmouseover="this.style.borderColor='var(--gold)'; this.style.color='var(--gold)';" onmouseout="this.style.borderColor='#444'; this.style.color='white';">🎖️ Premios</a>
            </div>
        </details>
        """

        html += f"""
        <details id="info" class="jornada-details" open>
            <summary style="cursor:pointer; border:none; outline:none;"><h2 style="display:inline-block; margin-top:0;">📊 Información General</h2></summary>
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
        for j_key in jornadas_keys: html += f"<th>{format_fase(j_key)}</th>"
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

        ultimos_terminados = []
        for g, partidos in realidad_dict.get("fase_grupos", {}).items():
            for p in partidos:
                if p.get("estado") in ["finished", "jugandose"]: ultimos_terminados.append({"fase": g, "data": p, "limpia": "grupos"})
        for clave, nombre_fase in [("dieciseisavos", "1/16"), ("octavos", "1/8"), ("cuartos", "1/4"), ("semifinales", "1/2"), ("tercer_puesto", "3º Puesto"), ("final", "Final")]:
            for p in realidad_dict.get("eliminatorias", {}).get(clave, []):
                if p.get("estado") in ["finished", "jugandose"]: ultimos_terminados.append({"fase": nombre_fase, "data": p, "limpia": clave})
                
        ultimos_4 = ultimos_terminados[-4:]
        ultimos_4.reverse()
        
        if ultimos_4:
            html += """<details id="ultimos" class="jornada-details" open><summary style="cursor:pointer; border:none; outline:none;"><h2 style="display:inline-block; margin-top:0;">🔥 Últimos Desempeños</h2></summary><div class="latest-grid" style="margin-bottom:30px;">"""

            for u_match in ultimos_4:
                p_real = u_match["data"]
                loc_r, vis_r = p_real.get("local", ""), p_real.get("visitante", "")
                clave = f"ID_{p_real['id_partido']}" if "id_partido" in p_real else f"{loc_r}_vs_{vis_r}"
                info_p = desglose_p.get(clave, {})
                p_pred = dict_preds_global.get(clave, {})
                fase_limpia = u_match["limpia"]
                
                if p_pred:
                    loc_p, vis_p = p_pred.get("local", ""), p_pred.get("visitante", "")
                    pred_txt = f"{loc_p} {p_pred.get('goles_local','-')}-{p_pred.get('goles_visitante','-')} {vis_p}" if (loc_p != loc_r or vis_p != vis_r) else f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}"
                else: pred_txt = "-"

                ac_ex, ac_1x2 = info_p.get("acierto_exacto", False), info_p.get("acierto_1x2", False)
                mult = info_p.get("multiplicador_aplicado", 1.0)
                pts = info_p.get('puntos_conseguidos', 0)
                
                if ac_ex: 
                    pred_styled = f"<span class='pred-exact'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[ <span class='pred-1x2'>{PTS_1X2} Ac</span> + <span class='pred-exact'>{PTS_EX} Ex</span> ] &times; {mult}</span>"
                elif ac_1x2: 
                    pred_styled = f"<span class='pred-1x2'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[ <span class='pred-1x2'>{PTS_1X2} Ac</span> ] &times; {mult}</span>"
                else: 
                    pred_styled = f"<span class='pred-miss'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:gray; font-size:0.85em;'>[ <span class='pred-miss'>0</span> ] &times; {mult}</span>"

                mult_html = f"""
                <div style="margin-top:10px; padding-top:10px; border-top:1px dotted #555; text-align:center;">
                    <div style="margin-bottom:8px;">{desglose_html}</div>"""
                
                if mult > 1.0 and p_real.get("estado") in ["finished", "jugandose"]:
                    r_loc = html_utils.obtener_racha_fases(jugador_dir, p_real.get("local"), fase_limpia)
                    r_vis = html_utils.obtener_racha_fases(jugador_dir, p_real.get("visitante"), fase_limpia)
                    
                    r_loc_html = "<br>".join([f"<a href='pronostico_{r[1].strip('/').split('/')[-1].replace('.json', '')}.html' target='_blank' style='color:#88b04b; text-decoration:none;'>+{html_utils.CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a>" for r in r_loc]) if r_loc else "<span style='color:gray;'>-</span>"
                    r_vis_html = "<br>".join([f"<a href='pronostico_{r[1].strip('/').split('/')[-1].replace('.json', '')}.html' target='_blank' style='color:#88b04b; text-decoration:none;'>+{html_utils.CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a>" for r in r_vis]) if r_vis else "<span style='color:gray;'>-</span>"
                    
                    if "base.html" in r_loc_html: r_loc_html = re.sub(r'pronostico_[^"\'\s]+_base\.html', 'pronostico_grupos.html', r_loc_html)
                    if "base.html" in r_vis_html: r_vis_html = re.sub(r'pronostico_[^"\'\s]+_base\.html', 'pronostico_grupos.html', r_vis_html)

                    mult_html += f"""
                    <div style="display:flex; justify-content:space-between; text-align:center; font-size:0.85em;">
                        <div style="flex:1; padding-right:5px;"><strong>{p_real.get('local')}</strong><br>{r_loc_html}</div>
                        <div style="flex:1; padding-left:5px; border-left:1px solid #333;"><strong>{p_real.get('visitante')}</strong><br>{r_vis_html}</div>
                    </div>"""
                mult_html += "</div>"

                score_clase = "live-score" if p_real.get("estado") == "jugandose" else ""
                balon_html = "<span class='live-ball'>⚽</span>" if p_real.get("estado") == "jugandose" else ""

                html += f"""
                <div style="background:#111; border:1px solid #222; border-radius:4px; padding:15px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div>
                        <div style="display:flex; justify-content:center; margin-bottom:12px; color:var(--table-header); font-weight:bold; letter-spacing:1px; font-size:0.9em; text-transform:uppercase;">
                            {u_match['fase']}
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:15px; font-size:1.1em; font-weight:bold;">
                            <span style="flex:1; text-align:right;">{loc_r}</span>
                            <span style="flex:0.3; text-align:center; color:white; background:#222; border-radius:4px; padding:2px; margin:0 10px;"><span class="{score_clase}">{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}</span>{balon_html}</span>
                            <span style="flex:1; text-align:left;">{vis_r}</span>
                        </div>
                    </div>
                    <div style="display:flex; align-items:flex-start; gap:10px; border-top:1px dashed #333; padding-top:15px;">
                        <div style="flex:1; text-align:center;">
                            <details class="pred-card-details">
                                <summary class="pred-summary" style="padding: 5px;">Tu Pronóstico: <strong>{pred_styled}</strong></summary>
                                {mult_html}
                            </details>
                        </div>
                        <div style="color:var(--gold); font-weight:bold; font-size:1.4em; align-self:center; padding-right:5px;">{pts}</div>
                    </div>
                </div>"""
            html += "</div></details>"

        bloqueado_grupos, fecha_grupos = esta_bloqueado("grupos")
        
        html += """
        <details id="grupos" class="jornada-details" open>
            <summary style="cursor:pointer; border:none; outline:none;"><h2 style="display:inline-block; margin-top:0;">🌍 Fase de Grupos</h2></summary>
        """
        if bloqueado_grupos:
            html += f"""
            <div style="background:#111; padding:40px 20px; text-align:center; border:1px solid #333; border-radius:8px; margin-top:15px;">
                <div style="font-size:3.5em; margin-bottom:15px;">🔒</div>
                <h2 style="color:var(--gold); margin-top:0;">Fase Protegida</h2>
                <p style="color:#ddd; font-size:1.1em; margin-bottom:5px;">Los pronósticos de Fase de Grupos están ocultos.</p>
                <p style="color:gray; font-size:0.95em;">Se revelarán el <strong>{fecha_grupos}</strong>.</p>
            </div></details>
            """
        else:
            html += """
            <div class="tabs-container">
                <button class="tab-btn active" onclick="openTab('tab-grupos-jaj')">Jornada a Jornada (JaJ)</button>
                <button class="tab-btn" onclick="openTab('tab-grupos-gag')">Grupo a Grupo (GaG)</button>
            </div>
            
            <div id="tab-grupos-jaj" class="tab-content active">
            """
            pts_grupos_acum = 0
            jornadas_grupos = [k for k in jornadas_keys if k.startswith("J")]
            
            for j_key in jornadas_grupos:
                html += f"<details class='jornada-details' open style='margin-bottom:20px; background:#151515; padding:15px; border-radius:8px; border:1px solid #333;'>"
                html += f"<summary style='border:none; padding:0; margin:0; outline:none; cursor:pointer;'><h3 style='color:var(--table-header); margin-top:0; text-align:center; border-bottom:1px solid #444; padding-bottom:5px; display:inline-block; width:100%;'>📌 {format_fase(j_key)}</h3></summary>"
                html += "<div class='match-grid-2col' style='margin-top:15px;'>"
                
                pts_jornada = exactos_j = 0
                partidos_ordenados = sorted(jornadas_dict[j_key], key=lambda x: dict_reales.get(f"{x['local']}_vs_{x['visitante']}", {}).get("fecha", ""))
                for p in partidos_ordenados:
                    clave = f"{p['local']}_vs_{p['visitante']}"
                    info_p = desglose_p.get(clave, {})
                    p_real = dict_reales.get(clave, {})
                    p_pred = dict_preds_global.get(clave, {})
                    
                    loc_r = p_real.get("local") or p.get("local", "TBD")
                    vis_r = p_real.get("visitante") or p.get("visitante", "TBD")
                    pred_txt = f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}" if p_pred else "-"
                    
                    if p_real.get("estado") == "jugandose":
                        real_txt = f"<span class='live-score'>{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}</span><span class='live-ball'>⚽</span>"
                    elif p_real.get("estado") == "finished":
                        real_txt = f"{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}"
                    else:
                        real_txt = "⏳"
                    
                    ac_ex, ac_1x2 = info_p.get("acierto_exacto", False), info_p.get("acierto_1x2", False)
                    if ac_ex: pred_styled = f"<span class='pred-exact'>{pred_txt} ({PTS_1X2} + {PTS_EX})</span>"
                    elif ac_1x2: pred_styled = f"<span class='pred-1x2'>{pred_txt} ({PTS_1X2})</span>"
                    else: pred_styled = f"<span class='pred-miss'>{pred_txt} (0)</span>"

                    pts = info_p.get("puntos_conseguidos", 0)
                    if ac_ex: exactos_j += 1
                    pts_grupos_acum += pts
                    pts_jornada += pts
                    
                    html += f"""
                    <div style="background:#111; border:1px solid #222; border-radius:4px; padding:10px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-weight:bold; font-size:1em;">
                            <span style="flex:1; text-align:right;">{loc_r}</span>
                            <span style="flex:0.4; text-align:center; color:white; background:#222; border-radius:4px; padding:2px; margin:0 5px;">{real_txt}</span>
                            <span style="flex:1; text-align:left;">{vis_r}</span>
                        </div>
                        <div style="font-size:0.9em; color:gray; text-align:left; border-top:1px dashed #333; padding-top:8px; display:flex; justify-content:space-between; align-items:center;">
                            <span style="flex:1; text-align:center;">Pronóstico: <strong>{pred_styled}</strong></span>
                            <span style="color:var(--gold); font-weight:bold; font-size:1.1em;">{pts} pts</span>
                        </div>
                    </div>
                    """
                html += "</div>"

                info_dj = desglose_j.get(j_key, {})
                res_bono = info_dj.get("resultado", "Neutral")
                res_val = info_dj.get('puntos_bono', 0)
                signo = "+" if res_val > 0 else ""
                rank_j = rankings_jornada.get(j_key, {}).get(jugador_dir.name, "-")
                
                html += f"""
                <div style="background:#222; padding:10px; margin-top:15px; border-left:4px solid var(--gold); border-radius:4px; font-size:0.9em; line-height:1.4;">
                    Resumen {format_fase(j_key)}: {exactos_j}/{info_dj.get('aciertos_1x2', 0)} (Clavados/Aciertos). Posición {rank_j} de {total_jugadores}.<br>
                    Resultado: {res_bono} ({signo}{res_val} pts)<br>
                    TOTAL JORNADA: {pts_jornada + res_val} pts
                </div></details>"""
            html += "</div>"

            html += """<div id="tab-grupos-gag" class="tab-content">
                <div style="background:rgba(218, 165, 32, 0.1); border-left:4px solid var(--gold); padding:10px; margin-bottom:20px; font-size:0.85em; text-align:center;">
                    <i>⚠️ Nota: Los puntos oficiales se reparten Jornada a Jornada. Esta vista es puramente una alternativa de visualización.</i>
                </div>
                <div class="group-grid-2col">"""
                
            for grupo, partidos in sorted(base_pred.get("fase_grupos", {}).items()):
                html += f"""<div class="card" style="padding:15px; cursor:default;"><h3 style="color:var(--gold); border-bottom:1px solid #333; padding-bottom:5px; margin-top:0;">{grupo}</h3><table class="gag-table">"""
                pts_grupo = 0
                for p in partidos:
                    clave = f"{p['local']}_vs_{p['visitante']}"
                    info_p = desglose_p.get(clave, {})
                    p_real = dict_reales.get(clave, {})
                    
                    if p_real.get("estado") == "jugandose":
                        real_txt = f"<span class='live-score'>{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}</span><span class='live-ball'>⚽</span>"
                    elif p_real.get("estado") == "finished":
                        real_txt = f"{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}"
                    else:
                        real_txt = "⏳"
                        
                    pred_txt = f"{p.get('goles_local','-')} - {p.get('goles_visitante','-')}"
                    
                    ac_ex, ac_1x2 = info_p.get("acierto_exacto", False), info_p.get("acierto_1x2", False)
                    if ac_ex: pred_styled = f"<span class='pred-exact'>{pred_txt} ({PTS_1X2} + {PTS_EX})</span>"
                    elif ac_1x2: pred_styled = f"<span class='pred-1x2'>{pred_txt} ({PTS_1X2})</span>"
                    else: pred_styled = f"<span class='pred-miss'>{pred_txt} (0)</span>"
                    
                    pts = info_p.get("puntos_conseguidos", 0)
                    pts_grupo += pts
                    
                    html += f"""<tr class="gag-match-row"><td style="text-align:right; width:40%;">{p['local']}</td><td style="width:20%;">{real_txt}</td><td style="text-align:left; width:40%;">{p['visitante']}</td></tr>
                                <tr class="gag-pred-row"><td colspan="3" style="padding-top:2px; padding-bottom:8px; color:gray;">Pronóstico: {pred_styled} <span style="float:right; color:var(--gold); font-weight:bold;">{pts} pts</span></td></tr>"""
                html += f"""<tr><td colspan="3" class="gag-total-row">Total Grupo: {pts_grupo} pts</td></tr></table></div>"""
            html += "</div></div></details>"

        bloqueado_balance, _ = esta_bloqueado("fin_fase_grupos")

        if not bloqueado_balance:
            pts_bono_fase = libro.get("resolucion_fase_grupos", {}).get("puntos_conseguidos", 0)
            html += f"""
            <details id="balance" class="jornada-details" open>
                <summary style="cursor:pointer; border:none; outline:none;"><h2 style="display:inline-block; margin-top:0;">⚖️ Balance Fase de Grupos</h2></summary>
                <div style="text-align:center; font-size:1.1em; margin-bottom:15px;">
                    Resumen: <strong>{aciertos_pos}/{aciertos_pase}</strong> (Clavados Pos. / Aciertos Pase)<br>
                    <span style="color:var(--gold); font-size:1.2em; font-weight:bold; margin-top:5px; display:inline-block;">Bono Total Obtenido: +{pts_bono_fase} pts</span>
                </div>
                <div class="group-grid-4col">
            """
            for eq in sorted(list(pos_real.keys())):
                p_tu = "✅" if eq in pasan_pred else "❌"
                p_rl = "✅" if eq in pasan_real else "❌"
                pos_tu, pos_rl = f"{pos_pred.get(eq, '-')}º", f"{pos_real.get(eq, '-')}º"
                
                pts_eq = 0
                if eq in pasan_real and eq in pasan_pred:
                    pts_eq = PTS_PASE
                    if pos_pred.get(eq) == pos_real.get(eq): pts_eq += PTS_POS

                color_class = "pred-exact" if pts_eq == (PTS_PASE + PTS_POS) else ("pred-1x2" if pts_eq == PTS_PASE else "pred-miss")
                
                if pts_eq == (PTS_PASE + PTS_POS): pts_desc = f"[ <span class='pred-1x2'>{PTS_PASE}</span> + <span class='pred-exact'>{PTS_POS}</span> ]"
                elif pts_eq == PTS_PASE: pts_desc = f"[ <span class='pred-1x2'>{PTS_PASE}</span> ]"
                else: pts_desc = f"[ <span class='pred-miss'>0</span> ]"
                
                html += f"""
                <div style="background:#111; border:1px solid #333; border-radius:4px; padding:10px; display:flex; flex-direction:column; align-items:center;">
                    <strong style="color:white; font-size:1.1em; margin-bottom:5px;">{eq}</strong>
                    <div style="font-size:0.85em; color:#aaa; text-align:center; margin-bottom:10px;">
                        Real: <strong>{pos_rl}</strong> {p_rl}<br>
                        Tú: <strong>{pos_tu}</strong> {p_tu}
                    </div>
                    <div style="font-size:1.4em; font-weight:bold; margin-bottom:2px;" class="{color_class}">
                        {pts_eq}
                    </div>
                    <div style="font-size:0.75em; color:gray;">
                        {pts_desc}
                    </div>
                </div>"""
            html += "</div></details>"

        jornadas_elim = [k for k in jornadas_keys if not k.startswith("J")]
        if jornadas_elim:
            html += """<details id="eliminatorias" class="jornada-details" open><summary style="cursor:pointer; border:none; outline:none;"><h2 style="display:inline-block; margin-top:0;">⚔️ Eliminatorias</h2></summary>"""
            for j_key in jornadas_elim:
                fase_limpia = j_key.split(".")[0] if "." in j_key else j_key
                bloqueado_elim, fecha_elim = esta_bloqueado(fase_limpia)
                
                html += f"<details class='jornada-details' open style='margin-bottom:20px; background:#151515; padding:15px; border-radius:8px; border:1px solid #333;'>"
                html += f"<summary style='border:none; padding:0; margin:0; outline:none; cursor:pointer;'><h3 style='color:var(--accent); margin-top:0; text-align:center; border-bottom:1px solid #444; padding-bottom:5px; display:inline-block; width:100%;'>📌 {format_fase(j_key)}</h3></summary>"
                
                if bloqueado_elim:
                    html += f"""
                    <div style="background:#1a1a1a; padding:30px 20px; text-align:center; border:1px dashed #444; border-radius:8px; margin-top:15px;">
                        <div style="font-size:2.5em; margin-bottom:10px;">🔒</div>
                        <h3 style="color:var(--gold); margin-top:0;">Pronósticos Ocultos</h3>
                        <p style="color:gray; font-size:0.9em;">Se revelarán el <strong>{fecha_elim}</strong></p>
                    </div></details>"""
                else:
                    html += "<div class='match-grid-2col' style='margin-top:15px;'>"
                    
                    pts_jornada = exactos_j = 0
                    partidos_ordenados = sorted(jornadas_dict[j_key], key=lambda x: dict_reales.get(f"ID_{x['id_partido']}" if "id_partido" in x else f"{x['local']}_vs_{x['visitante']}", {}).get("fecha", ""))
                    for p in partidos_ordenados:
                        clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                        info_p = desglose_p.get(clave, {})
                        p_real = dict_reales.get(clave, {})
                        p_pred = dict_preds_global.get(clave, {})
                        
                        loc_r = p_real.get("local") or p.get("local") or p.get("placeholder_local", "TBD")
                        vis_r = p_real.get("visitante") or p.get("visitante") or p.get("placeholder_visitante", "TBD")
                        if loc_r == "TBD" and "id_partido" in p: loc_r, vis_r = f"Eq. {p['id_partido']}A", f"Eq. {p['id_partido']}B"
                        
                        subtitle_html = ""
                        if j_key.lower() == "finales":
                            if "103" in str(p.get("id_partido", "")):
                                subtitle_html = "<div style='text-align:center; color:#a9b7c6; font-size:0.85em; font-weight:bold; margin-bottom:10px;'>🥉 3º Puesto</div>"
                            elif "104" in str(p.get("id_partido", "")):
                                subtitle_html = "<div style='text-align:center; color:var(--gold); font-size:0.85em; font-weight:bold; margin-bottom:10px;'>🏆 Final</div>"

                        if p_pred:
                            loc_p, vis_p = p_pred.get("local", ""), p_pred.get("visitante", "")
                            pred_txt = f"{loc_p} {p_pred.get('goles_local','-')}-{p_pred.get('goles_visitante','-')} {vis_p}" if (loc_p != loc_r or vis_p != vis_r) else f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}"
                        else: pred_txt = "-"
                        
                        if p_real.get("estado") == "jugandose":
                            real_txt = f"<span class='live-score'>{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}</span><span class='live-ball'>⚽</span>"
                        elif p_real.get("estado") == "finished":
                            real_txt = f"{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}"
                        else:
                            real_txt = "⏳"
                        
                        ac_ex, ac_1x2 = info_p.get("acierto_exacto", False), info_p.get("acierto_1x2", False)
                        mult = info_p.get("multiplicador_aplicado", 1.0)
                        pts = info_p.get("puntos_conseguidos", 0)
                        
                        if ac_ex: 
                            pred_styled = f"<span class='pred-exact'>{pred_txt}</span>"
                            desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[ <span class='pred-1x2'>{PTS_1X2} Ac</span> + <span class='pred-exact'>{PTS_EX} Ex</span> ] &times; {mult}</span>"
                        elif ac_1x2: 
                            pred_styled = f"<span class='pred-1x2'>{pred_txt}</span>"
                            desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[ <span class='pred-1x2'>{PTS_1X2} Ac</span> ] &times; {mult}</span>"
                        else: 
                            pred_styled = f"<span class='pred-miss'>{pred_txt}</span>"
                            desglose_html = f"<span style='color:gray; font-size:0.85em;'>[ <span class='pred-miss'>0</span> ] &times; {mult}</span>"

                        if ac_ex: exactos_j += 1
                        pts_jornada += pts
                        
                        mult_html = f"""
                        <div style="margin-top:10px; padding-top:10px; border-top:1px dotted #555; text-align:center;">
                            <div style="margin-bottom:8px;">{desglose_html}</div>"""
                        
                        if mult > 1.0 and p_real.get("estado") in ["finished", "jugandose"]:
                            r_loc = html_utils.obtener_racha_fases(jugador_dir, p_real.get("local"), fase_limpia)
                            r_vis = html_utils.obtener_racha_fases(jugador_dir, p_real.get("visitante"), fase_limpia)
                            
                            r_loc_html = "<br>".join([f"<a href='pronostico_{r[1].strip('/').split('/')[-1].replace('.json', '')}.html' target='_blank' style='color:#88b04b; text-decoration:none;'>+{html_utils.CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a>" for r in r_loc]) if r_loc else "<span style='color:gray;'>-</span>"
                            r_vis_html = "<br>".join([f"<a href='pronostico_{r[1].strip('/').split('/')[-1].replace('.json', '')}.html' target='_blank' style='color:#88b04b; text-decoration:none;'>+{html_utils.CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a>" for r in r_vis]) if r_vis else "<span style='color:gray;'>-</span>"

                            if "base.html" in r_loc_html: r_loc_html = re.sub(r'pronostico_[^"\'\s]+_base\.html', 'pronostico_grupos.html', r_loc_html)
                            if "base.html" in r_vis_html: r_vis_html = re.sub(r'pronostico_[^"\'\s]+_base\.html', 'pronostico_grupos.html', r_vis_html)
                                                    
                            mult_html += f"""
                            <div style="display:flex; justify-content:space-between; text-align:center; font-size:0.85em;">
                                <div style="flex:1; padding-right:5px;"><strong>{p_real.get('local')}</strong><br>{r_loc_html}</div>
                                <div style="flex:1; padding-left:5px; border-left:1px solid #333;"><strong>{p_real.get('visitante')}</strong><br>{r_vis_html}</div>
                            </div>"""
                        mult_html += "</div>"
                            
                        html += f"""
                        <div style="background:#1a1a1a; border:1px solid #333; border-radius:4px; padding:15px; display:flex; flex-direction:column; justify-content:space-between;">
                            <div>
                                {subtitle_html}
                                <div style="display:flex; justify-content:space-between; margin-bottom:15px; font-size:1.1em; font-weight:bold;">
                                    <span style="flex:1; text-align:right;">{loc_r}</span>
                                    <span style="flex:0.3; text-align:center; color:white; background:#222; border-radius:4px; padding:2px; margin:0 10px;">{real_txt}</span>
                                    <span style="flex:1; text-align:left;">{vis_r}</span>
                                </div>
                            </div>
                            <div style="display:flex; align-items:flex-start; gap:10px; border-top:1px dashed #444; padding-top:15px;">
                                <div style="flex:1; text-align:center;">
                                    <details class="pred-card-details">
                                        <summary class="pred-summary" style="padding: 5px;">Tu Pronóstico: <strong>{pred_styled}</strong></summary>
                                        {mult_html}
                                    </details>
                                </div>
                                <div style="color:var(--gold); font-weight:bold; font-size:1.4em; align-self:center; padding-right:5px;">{pts}</div>
                            </div>
                        </div>
                        """
                    html += "</div>"

                    info_dj = desglose_j.get(j_key, {})
                    res_bono = info_dj.get("resultado", "Neutral")
                    res_val = info_dj.get('puntos_bono', 0)
                    signo = "+" if res_val > 0 else ""
                    rank_j = rankings_jornada.get(j_key, {}).get(jugador_dir.name, "-")
                    
                    html += f"""
                    <div style="background:#222; padding:10px; margin-top:15px; border-left:4px solid var(--gold); border-radius:4px; font-size:0.9em; line-height:1.4;">
                        Resumen {format_fase(j_key)}: {exactos_j}/{info_dj.get('aciertos_1x2', 0)} (Clavados/Aciertos). Posición {rank_j} de {total_jugadores}.<br>
                        Resultado: {res_bono} ({signo}{res_val} pts)<br>
                        TOTAL JORNADA: {pts_jornada + res_val} pts
                    </div></details>"""
            html += "</details>"

        bloqueado_sd, _ = esta_bloqueado("fin_fase_grupos")

        if not bloqueado_sd:
            matriz_sd = libro.get("matriz_sorpresas_decepciones", {})
            if global_sd:
                pts_sorpresa_tot = sum(d['puntos'] for d in matriz_sd.values() if d['resultado_calculo'] == 'Sorpresa')
                pts_decepcion_tot = sum(d['puntos'] for d in matriz_sd.values() if d['resultado_calculo'] == 'Decepción')
                
                html += f"""
            <details id="sd" class="jornada-details" open>
                <summary style="cursor:pointer; border:none; outline:none;"><h2 style="display:inline-block; margin-top:0;">🎯 Sorpresas y Decepciones</h2></summary>
                
                <div style="text-align:center; font-size:1.1em; margin-bottom:15px;">
                    Total Sorpresas: <strong style="color:#4ade80;">+{pts_sorpresa_tot} pts</strong> | Total Decepciones: <strong style="color:#f87171;">+{pts_decepcion_tot} pts</strong>
                </div>
                
                <p style="font-size:0.9em; color:#aaa; margin-bottom:20px;">Selecciona un país para ver tu desviación respecto a la media global.</p>
                <div class="sd-flag-grid">
                """
                for eq, datos in sorted(matriz_sd.items()):
                    eq_id = limpiar_nombre_id(eq)
                    res_calc = datos.get("resultado_calculo", "")
                    
                    color_style = ""
                    if res_calc == 'Sorpresa' and datos['puntos'] > 0: color_style = "color:#4ade80; border-color:#4ade80;"
                    elif res_calc == 'Decepción' and datos['puntos'] > 0: color_style = "color:#f87171; border-color:#f87171;"
                    
                    html += f"""<div class="sd-flag-btn" style="{color_style}" onclick="showSD('{eq_id}')">{eq}</div>"""
                html += "</div><div id='sd-details-container'>"
                
                def get_x_percent(val): return max(0, min(100, ((val + 0.5) / 6.0) * 100.0))

                for eq, datos_global in sorted(global_sd.items()):
                    eq_id = limpiar_nombre_id(eq)
                    M_val = datos_global["media"]
                    R_val = datos_global["realidad"]
                    U_val = datos_global["umbral"]
                    
                    datos_tu = matriz_sd.get(eq, {})
                    P_val = map_fase_to_num(datos_tu.get("pronostico", -1))
                    puntos_tu = datos_tu.get("puntos", 0)
                    res_tu = datos_tu.get("resultado_calculo", "")
                    
                    limite_rojo_visual = math.ceil(M_val - U_val) - 1
                    limite_verde_visual = math.floor(M_val + U_val) + 1
                    
                    w_dec = get_x_percent(limite_rojo_visual + 0.5)
                    left_sorp = get_x_percent(limite_verde_visual - 0.5)
                    w_sorp = 100.0 - left_sorp

                    pos_M = get_x_percent(M_val)
                    
                    gold_left = get_x_percent(R_val - UMB_R_P)
                    gold_right = get_x_percent(R_val + UMB_R_P)
                    w_gold = gold_right - gold_left

                    timeline_html = f"""
                    <div style="overflow-x:auto; padding-bottom:10px;">
                        <div style="position:relative; width:100%; min-width:700px; border:1px solid #333; border-radius:6px; background:#111; overflow:hidden; margin-top:20px; display:flex;">
                            
                            <div style="position:absolute; top:0; left:0; height:100%; width:{w_dec}%; background:rgba(248, 113, 113, 0.2); border-right:2px dashed #f87171; pointer-events:none; z-index:1;"></div>
                            <div style="position:absolute; top:0; left:{left_sorp}%; height:100%; width:{w_sorp}%; background:rgba(74, 222, 128, 0.2); border-left:2px dashed #4ade80; pointer-events:none; z-index:1;"></div>
                            
                            <div style="position:absolute; top:0; left:{gold_left}%; height:100%; width:{w_gold}%; background:rgba(218, 165, 32, 0.08); border-left:1.5px dashed rgba(218, 165, 32, 0.4); border-right:1.5px dashed rgba(218, 165, 32, 0.4); pointer-events:none; z-index:2; transform:scaleX(1.5); transform-origin:center;"></div>
                    """

                    M_idx = int(M_val)

                    for idx_fase, nom_fase in enumerate(nombres_columnas_sd):
                        inds_html = ""
                        
                        if idx_fase == M_idx:
                            inds_html += f"<div class='sd-indicator' style='background:white; color:black; box-shadow:0 0 5px white; border:1px solid #ccc;'>Media {M_val:.1f}</div>"
                        
                        if idx_fase == R_val: 
                            inds_html += "<div class='sd-indicator ind-real'>Real</div>"
                        
                        pills_html = ""
                        for p_data in datos_global.get("predicciones", []):
                            if p_data["fase_pronostico"] == idx_fase:
                                pts_val = p_data["puntos"]
                                p_id = p_data["jugador_id"]
                                
                                is_tu = (p_id == jugador_dir.name)
                                nombre_mostrar = "Tú" if is_tu else p_data["jugador_nombre"]
                                
                                if pts_val > 0:
                                    c_win = "win-dec" if p_data["resultado"] == "Decepción" else "win-sorp"
                                    pill_content = f"{nombre_mostrar} <span style='float:right;'>+{pts_val}</span>"
                                    
                                    if is_tu:
                                        pills_html += f"<div class='sd-player-pill ind-tu-pill {c_win}'>{pill_content}</div>"
                                    else:
                                        link = f"../../{p_id}/vistas/dashboard.html"
                                        pills_html += f"<a href='{link}' style='text-decoration:none;'><div class='sd-player-pill {c_win}'>{pill_content}</div></a>"
                                else:
                                    if is_tu:
                                        pills_html += f"<div class='sd-player-pill ind-tu-pill'>{nombre_mostrar}</div>"
                                    else:
                                        link = f"../../{p_id}/vistas/dashboard.html"
                                        pills_html += f"<a href='{link}' style='text-decoration:none;'><div class='sd-player-pill'>{nombre_mostrar}</div></a>"
                                    
                        timeline_html += f"""
                            <div style="flex:1; padding:10px; border-right:1px solid #333; display:flex; flex-direction:column; align-items:center; z-index:3; position:relative;">
                                <div style="height:75px; width:100%; display:flex; flex-direction:column; justify-content:flex-end; gap:4px; align-items:center; margin-top:15px;">
                                    {inds_html}
                                </div>
                                <div style="font-size:0.75em; color:var(--table-header); text-transform:uppercase; border-top:1px dashed #444; border-bottom:1px dashed #444; padding:5px 0; margin:10px 0; width:100%; letter-spacing:1px; text-align:center; font-weight:bold;">{nom_fase}</div>
                                <div style="width:100%; display:flex; flex-direction:column; gap:6px;">
                                    {pills_html}
                                </div>
                            </div>"""
                    
                    timeline_html += "</div></div>"

                    html += f"""
                    <div id="sd-{eq_id}" class="sd-detail-panel">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #444; padding-bottom:10px;">
                            <h3 style="margin:0; color:var(--gold); font-size:1.5em;">{eq}</h3>
                            <div style="text-align:right;">
                                <span style="font-size:1.2em; font-weight:bold; color:var(--gold);">{puntos_tu} pts</span><br>
                                <span style="font-size:0.8em; color:gray;">Resultado: {res_tu if res_tu else "Ninguno"}</span>
                            </div>
                        </div>
                        {timeline_html}
                        <p style="font-size:0.8em; color:gray; text-align:center; margin-top:15px;">Umbral de acierto: ±{U_val:.1f} fases desde la Media ({M_val:.1f}). Los jugadores coloreados sumaron puntos.</p>
                    </div>"""
                html += "</div></details>"

        html += "</div></body></html>"
        with open(dir_vistas / "dashboard.html", 'w', encoding='utf-8') as f:
            f.write(html)

if __name__ == "__main__":
    print("=======================================================")
    print(" 📊 [07B5] GENERANDO DASHBOARDS INDIVIDUALES FRONTEND 📊")
    print("=======================================================")
    generar_dashboards_html()
    print("✅ Dashboards de participantes generados con éxito.")