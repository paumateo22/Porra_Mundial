import sys
import csv
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def get_racha_links_local(jugador_dir, equipo, fase_objetivo):
    """
    Calcula la racha real separando 3º Puesto y Final, y devuelve 
    directamente los enlaces HTML web (relativos) formateados.
    """
    racha_links = []
    racha_count = 0
    fases_cronologicas = ["grupos", "dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]
    
    fase_busqueda = "finales" if fase_objetivo in ["final", "tercer_puesto", "finales"] else fase_objetivo
    idx_limite = fases_cronologicas.index(fase_busqueda) if fase_busqueda in fases_cronologicas else 0
    jug_id = jugador_dir.name
    inc = html_utils.CONFIG.get("multiplicadores", {}).get("incremento_racha_por_fase", 0.5)
    
    for i in range(idx_limite):
        fase_origen = fases_cronologicas[i]
        encontrado = False
        
        if fase_origen == "grupos":
            ruta_base = jugador_dir / "pronosticos" / "grupos" / f"{jug_id}_base.json"
            if ruta_base.exists():
                base = html_utils.cargar_json(ruta_base) or {}
                if fase_objetivo in ["final", "tercer_puesto", "finales"]:
                    partidos_objetivo = base.get("eliminatorias", {}).get("final", []) + base.get("eliminatorias", {}).get("tercer_puesto", [])
                else:
                    partidos_objetivo = base.get("eliminatorias", {}).get(fase_objetivo, [])
                    
                encontrado = any(p.get("local") == equipo or p.get("visitante") == equipo for p in partidos_objetivo)
        else:
            ruta_ocr = jugador_dir / "pronosticos" / "eliminatorias" / fase_origen / f"{fase_origen}.json"
            if ruta_ocr.exists():
                ocr_data = html_utils.cargar_json(ruta_ocr) or {}
                
                # Aislamiento estricto entre 3º Puesto y Final
                if fase_objetivo in ["final", "tercer_puesto"]:
                    partidos_finales = ocr_data.get("predicciones", {}).get("finales", [])
                    partidos_objetivo = []
                    if len(partidos_finales) >= 2:
                        if fase_objetivo == "tercer_puesto": partidos_objetivo = [partidos_finales[0]]
                        elif fase_objetivo == "final": partidos_objetivo = [partidos_finales[1]]
                    elif len(partidos_finales) == 1:
                        if fase_objetivo == "final": partidos_objetivo = [partidos_finales[0]]
                else:
                    partidos_objetivo = ocr_data.get("predicciones", {}).get(fase_objetivo, [])
                    
                encontrado = any(p.get("local") == equipo or p.get("visitante") == equipo for p in partidos_objetivo)
                
        if encontrado:
            racha_count += 1
            # Mapeamos el nombre de la fase para que quede visualmente bonito
            nombres_fases = {"grupos": "Grupos", "dieciseisavos": "1/16", "octavos": "1/8", "cuartos": "1/4", "semifinales": "Semis", "finales": "Finales"}
            fase_texto = nombres_fases.get(fase_origen, fase_origen.capitalize())
            
            # Construimos el enlace web relativo
            href_val = f"participantes/{jug_id}/vistas/pronostico_{fase_origen}.html"
            racha_links.append(f"<a href='{href_val}' target='_blank' class='mult-link'>+{inc} ({fase_texto})</a>")
            
    return racha_links


def generar_index_html():
    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    if not ruta_csv.exists(): 
        print("❌ Error: No se encontró el ranking_oficial.csv")
        return False

    jornadas_dict = html_utils.cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    jornadas_keys = list(jornadas_dict.keys())
    
    realidad_dict = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    pos_real = html_utils.calcular_clasificacion_grupos(realidad_dict.get("fase_grupos", {}))
    pasan_real = realidad_dict.get("clasificados_a_dieciseisavos", [])

    # Obtener valores de puntos para el desglose dinámico
    pts_1x2_val = html_utils.CONFIG.get("puntuacion", {}).get("acierto_1x2", 1)
    pts_ex_val = html_utils.CONFIG.get("puntuacion", {}).get("acierto_exacto", 3)

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
    {html_utils.get_sidebar_html("")}
    {html_utils.get_header_html("🏆 Porra Mundial 2026", f"Panel de Estadísticas Oficiales | Actualizado: {fecha_act}", "", show_participa=True)}
    <div class="container">
"""
    
    jugadores_datos = []
    with open(ruta_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jug_id = row['Jugador'].replace(' ', '_').lower()
            jug_dir = ROOT_DIR / "participantes" / jug_id
            libro = html_utils.cargar_json(jug_dir / "estadisticas" / "historial_puntos.json") or {}
            base_pred = html_utils.cargar_json(jug_dir / "pronosticos" / "grupos" / f"{jug_id}_base.json") or {}
            
            premios = libro.get("premios_finales", {}).get("formularios", {}).get("detalles", {})
            pts_extra_totales = float(row.get('Puntos_Podio', 0)) + float(row.get('Puntos_Forms', 0))
            
            total_1x2 = sum(1 for p in libro.get("desglose_partidos", {}).values() if p.get("acierto_1x2"))
            total_exactos = sum(1 for p in libro.get("desglose_partidos", {}).values() if p.get("acierto_exacto"))
                
            victorias_j = sum(1 for j in libro.get("desglose_jornadas", {}).values() if j.get("resultado") == "Ganador")
            derrotas_j = sum(1 for j in libro.get("desglose_jornadas", {}).values() if j.get("resultado") == "Perdedor")
                
            pos_pred = html_utils.calcular_clasificacion_grupos(base_pred.get("fase_grupos", {}))
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
                "libro": libro,
                "dir_path": jug_dir
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
        pos_display = "🥇 1º" if j['pos_csv'] == "1" else ("🥈 2º" if j['pos_csv'] == "2" else ("🥉 3º" if j['pos_csv'] == "3" else f"{j['pos_csv']}º"))
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

    # SECCIÓN 2: ÚLTIMOS PARTIDOS (Plegados por defecto, Grid 2x2)
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
        for u_match in ultimos_4:
            fase_txt = u_match["fase"]
            p_real = u_match["data"]
            loc_r, vis_r = p_real.get("local", ""), p_real.get("visitante", "")
            clave = f"ID_{p_real['id_partido']}" if "id_partido" in p_real else f"{loc_r}_vs_{vis_r}"
            
            stats_match = []
            for j in jugadores_datos:
                info_p = j["libro"].get("desglose_partidos", {}).get(clave)
                if not info_p: continue
                
                # Obtener la predicción del JSON del jugador
                base_pred = html_utils.cargar_json(j["dir_path"] / "pronosticos" / "grupos" / f"{j['id']}_base.json") or {}
                dict_preds = {}
                for p_list in base_pred.get("fase_grupos", {}).values():
                    for pp in p_list: dict_preds[f"{pp['local']}_vs_{pp['visitante']}"] = pp
                for f_k in ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]:
                    f_data = html_utils.cargar_json(j["dir_path"] / "pronosticos" / "eliminatorias" / f_k / f"{f_k}.json") or {}
                    for f_dest, p_list in f_data.get("predicciones", {}).items():
                        r_fase = realidad_dict.get("eliminatorias", {}).get("tercer_puesto", []) + realidad_dict.get("eliminatorias", {}).get("final", []) if f_dest in ["finales", "final", "tercer_puesto"] else realidad_dict.get("eliminatorias", {}).get(f_dest, [])
                        for i, p_rl in enumerate(r_fase):
                            if i < len(p_list): dict_preds[f"ID_{p_rl['id_partido']}"] = p_list[i]

                p_pred = dict_preds.get(clave, {})
                if p_pred:
                    loc_p, vis_p = p_pred.get("local", ""), p_pred.get("visitante", "")
                    pred_txt = f"{loc_p} {p_pred.get('goles_local','-')}-{p_pred.get('goles_visitante','-')} {vis_p}" if (loc_p != loc_r or vis_p != vis_r) else f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}"
                else: pred_txt = "-"

                acierto_ex = info_p.get("acierto_exacto", False)
                acierto_1x2 = info_p.get("acierto_1x2", False)
                mult = info_p.get("multiplicador_aplicado", 1.0)
                pts_finales = info_p.get("puntos_conseguidos", 0)
                
                if acierto_ex: 
                    pred_styled = f"<span class='pred-exact'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[ {pts_1x2_val} <span class='pred-1x2'>Ac</span> + {pts_ex_val} <span class='pred-exact'>Ex</span> ] &times; {mult}</span>"
                elif acierto_1x2: 
                    pred_styled = f"<span class='pred-1x2'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:#ccc; font-size:0.85em;'>[ {pts_1x2_val} <span class='pred-1x2'>Ac</span> ] &times; {mult}</span>"
                else: 
                    pred_styled = f"<span class='pred-miss'>{pred_txt}</span>"
                    desglose_html = f"<span style='color:gray; font-size:0.85em;'>0 pts</span>"

                # Multiplicador Desplegable usando la nueva función depurada
                mult_html = f"x{mult}"
                if mult > 1.0:
                    links_loc = get_racha_links_local(j["dir_path"], p_real.get("local"), u_match["limpia"])
                    links_vis = get_racha_links_local(j["dir_path"], p_real.get("visitante"), u_match["limpia"])
                    
                    if links_loc or links_vis:
                        r_loc_html = "<br>".join(links_loc) if links_loc else "<span style='color:gray;'>-</span>"
                        r_vis_html = "<br>".join(links_vis) if links_vis else "<span style='color:gray;'>-</span>"
                        
                        # RESTAURADO: El contenedor flex para poner a izquierda y derecha
                        content_html = f"""
                        <div style="display:flex; justify-content:space-between; text-align:center; font-size:0.85em; padding-top:5px;">
                            <div style="flex:1; padding-right:5px;"><strong>{p_real.get('local')}</strong><br>{r_loc_html}</div>
                            <div style="flex:1; padding-left:5px; border-left:1px solid #333;"><strong>{p_real.get('visitante')}</strong><br>{r_vis_html}</div>
                        </div>"""
                        
                        mult_html = f"<details class='mult-details'><summary>x{mult} ▼</summary><div class='mult-content'>{content_html}</div></details>"

                stats_match.append({
                    "nombre": j['nombre'], "id": j['id'], "pts": pts_finales,
                    "mult": mult_html, "pred": pred_styled, "desglose": desglose_html
                })

            stats_match.sort(key=lambda x: x['pts'], reverse=True)

            html += f"""
            <details class="match-card" open>
                <summary>
                    <div class="match-header" style="text-align: center;">{fase_txt}</div>
                    <div class="match-score">{loc_r} <span>{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}</span> {vis_r}</div>
                </summary>
                <div class="match-breakdown">
                    <table style="font-size:0.9em; background:transparent;">
                        <tr><th style="background:#111;">Jugador</th><th style="background:#111;">Pronóstico</th><th style="background:#111; width:70px;">Mult.</th><th style="background:#111;">Cálculo</th><th style="background:#111;">Pts</th></tr>"""
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
                    <tr><th>Pos</th><th>Jugador</th>
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
                
            aciertos_1x2_j = info_j.get("acierto_1x2", info_j.get("aciertos_1x2", 0))
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
    print("✅ index.html global generado con éxito.")
    return True

if __name__ == "__main__":
    generar_index_html()