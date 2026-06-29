import sys
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def esta_bloqueado(jornada_key):
    fase_busqueda = "grupos"
    if "dieciseisavos" in jornada_key: fase_busqueda = "dieciseisavos"
    elif "octavos" in jornada_key: fase_busqueda = "octavos"
    elif "cuartos" in jornada_key: fase_busqueda = "cuartos"
    elif "semifinales" in jornada_key: fase_busqueda = "semifinales"
    elif "finales" in jornada_key: fase_busqueda = "finales"
    
    horarios = html_utils.CONFIG.get("horarios", {})
    fecha_str = horarios.get(f"apertura_{fase_busqueda}")
    if not fecha_str: return False, ""
    
    try:
        fecha_apertura = datetime.fromisoformat(fecha_str).replace(tzinfo=ZoneInfo("Europe/Madrid"))
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        if ahora < fecha_apertura:
            return True, fecha_apertura.strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    return False, ""

def get_nombre_bonito(jornada_key):
    mapeo = {
        "dieciseisavos.1": "1/16-1", "dieciseisavos.2": "1/16-2",
        "octavos": "Octavos", "cuartos": "Cuartos", 
        "semifinales": "Semifinales", "finales": "Finales"
    }
    return mapeo.get(jornada_key, jornada_key.upper())

def acortar_nombre(n):
    if not n: return ""
    if n.startswith("Ganador "): return "W" + n.split(" ")[1]
    if n.startswith("Perdedor "): return "L" + n.split(" ")[1]
    if n.startswith("W") and n[1:].isdigit(): return n
    return n[:3].upper()

def generar_jornadas_html():
    print("=======================================================")
    print(" 📊 [07B8] GENERANDO VISTA CENTRAL DE JORNADAS 📊")
    print("=======================================================")

    jornadas_dict = html_utils.cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    jornadas_keys = list(jornadas_dict.keys())
    realidad_dict = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    
    dict_reales = {}
    for g, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos: dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    for f, partidos in realidad_dict.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p: dict_reales[f"ID_{p['id_partido']}"] = p

    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    datos_globales = {}
    for j in jugadores:
        j_id = j.name
        libro = html_utils.cargar_json(j / "estadisticas" / "historial_puntos.json") or {}
        
        preds_jugador = {}
        base = html_utils.cargar_json(j / "pronosticos" / "grupos" / f"{j_id}_base.json") or {}
        for p_list in base.get("fase_grupos", {}).values():
            for pp in p_list: preds_jugador[f"{pp['local']}_vs_{pp['visitante']}"] = pp
            
        for f_k in ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]:
            f_data = html_utils.cargar_json(j / "pronosticos" / "eliminatorias" / f_k / f"{f_k}.json") or {}
            for f_dest, p_list in f_data.get("predicciones", {}).items():
                r_fase = realidad_dict.get("eliminatorias", {}).get("tercer_puesto", []) + realidad_dict.get("eliminatorias", {}).get("final", []) if f_dest in ["finales", "final", "tercer_puesto"] else realidad_dict.get("eliminatorias", {}).get(f_dest, [])
                for i, p_rl in enumerate(r_fase):
                    if i < len(p_list): preds_jugador[f"ID_{p_rl['id_partido']}"] = p_list[i]
                    
        datos_globales[j_id] = {
            "nombre": j_id.replace('_', ' ').title(),
            "libro": libro,
            "preds": preds_jugador,
            "dir_path": j
        }

    fecha_act = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M")
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jornadas | Porra Mundial 2026</title>
    <link rel="stylesheet" href="theme.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .container {{ max-width: 1450px !important; margin: 0 auto; }}

        .sticky-nav {{ position: sticky; top: 0; z-index: 1000; background: rgba(18,18,18,0.95); padding: 12px; border-bottom: 2px solid var(--gold); display: flex; gap: 10px; justify-content: center; overflow-x: auto; flex-wrap: nowrap; backdrop-filter: blur(5px); box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 20px; }}
        .nav-btn {{ background: #222; color: white; border: 1px solid #444; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s; white-space: nowrap; }}
        .nav-btn.active, .nav-btn:hover {{ background: var(--gold); color: black; border-color: var(--gold); }}
        
        .tab-content {{ display: none; animation: fadeIn 0.4s; }}
        .tab-content.active {{ display: block; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        
        .cards-wrapper {{ display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin-bottom: 30px; }}
        
        .mvp-card {{ flex: 1; min-width: 280px; max-width: 450px; background: linear-gradient(135deg, #DAA520 0%, #b8860b 100%); color: black; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.5); position: relative; overflow: hidden; border: 2px solid #fff; }}
        .mvp-card::after {{ content: '👑'; position: absolute; font-size: 6em; opacity: 0.15; right: -10px; top: -20px; transform: rotate(15deg); pointer-events: none; }}
        
        .loser-card {{ flex: 1; min-width: 280px; max-width: 450px; background: linear-gradient(135deg, #2c3e50 0%, #1a252f 100%); color: white; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.5); position: relative; overflow: hidden; border: 2px solid #555; }}
        .loser-card::after {{ content: '🐢'; position: absolute; font-size: 6em; opacity: 0.10; right: -10px; top: -20px; transform: rotate(15deg); pointer-events: none; }}
        
        .card-title {{ font-weight: 900; font-size: 1.1em; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; opacity: 0.9; }}
        .card-name {{ font-weight: 900; margin: 5px 0; }}
        .card-pts {{ font-size: 1.3em; font-family: monospace; font-weight: bold; background: rgba(0,0,0,0.15); display: inline-block; padding: 5px 15px; border-radius: 20px; }}

        .table-wrapper-spaced {{ overflow-x: auto; padding-bottom: 120px; margin-bottom: -90px; }}
        .table-jornada {{ width: 100%; min-width: 1100px; border-collapse: collapse; }}
        .table-jornada th {{ text-align: center; font-size: 0.8em; padding: 12px 4px; border-bottom: 2px solid #333; }}
        .table-jornada td {{ text-align: center; padding: 12px 4px; font-size: 0.9em; position: relative; border-bottom: 1px solid #222; }}
        .cell-pts {{ color: var(--gold); font-weight: bold; font-size: 1.1em; }}
        .cell-pred {{ margin-bottom: 4px; display: block; color: #ddd; letter-spacing: 1px; }}
        
        .cell-mult-details {{ position: relative; display: inline-block; margin-top: 4px; }}
        .cell-mult-details summary {{ font-size: 0.75em; background: rgba(218,165,32,0.1); color: var(--gold); border-radius: 4px; padding: 3px 8px; cursor: pointer; list-style: none; border: 1px dashed rgba(218,165,32,0.5); font-weight: bold; transition: 0.2s; }}
        .cell-mult-details summary:hover {{ background: rgba(218,165,32,0.25); }}
        .cell-mult-details summary::-webkit-details-marker {{ display: none; }}
        .cell-mult-content {{ position: absolute; z-index: 9999; background: #1a1a1a; border: 1px solid var(--gold); padding: 12px; border-radius: 6px; top: 130%; left: 50%; transform: translateX(-50%); width: 200px; box-shadow: 0 8px 25px rgba(0,0,0,0.9); text-align: center; }}
        
        .chart-container {{ background: #151515; border: 1px solid #333; border-radius: 8px; padding: 20px; margin-top: 30px; height: 400px; position: relative; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
    </style>
</head>
<body>
    {html_utils.get_sidebar_html("")}
    {html_utils.get_header_html("📊 Dashboard de Jornadas", f"Análisis detallado por bloque | Actualizado: {fecha_act}", "")}
    
    <div class="sticky-nav" id="jornadas-nav">
"""
    for i, j_key in enumerate(jornadas_keys):
        active_class = "active" if i == 0 else ""
        html += f"""<button class="nav-btn {active_class}" onclick="openJornada('{j_key}', this)">{get_nombre_bonito(j_key)}</button>"""
    html += "</div><div class='container'>"

    rankings_por_jornada = {}

    for i, j_key in enumerate(jornadas_keys):
        active_class = "active" if i == 0 else ""
        html += f"""<div id="{j_key}" class="tab-content {active_class}">"""
        
        bloqueado, fecha_apertura = esta_bloqueado(j_key)
        if bloqueado:
            html += f"""
            <div style="background:#111; padding:60px 20px; text-align:center; border:1px solid #333; border-radius:12px; margin-top:20px;">
                <div style="font-size:4em; margin-bottom:15px;">🔒</div>
                <h2 style="color:var(--gold); margin-top:0; font-size:2em;">Jornada Protegida</h2>
                <p style="color:#ddd; font-size:1.2em; margin-bottom:5px;">Los datos de esta ronda están ocultos temporalmente.</p>
                <p style="color:gray; font-size:1em;">Se revelarán el <strong>{fecha_apertura}</strong> (Hora Peninsular).</p>
            </div></div>"""
            continue
            
        partidos_jornada = sorted(jornadas_dict[j_key], key=lambda x: dict_reales.get(f"ID_{x['id_partido']}" if "id_partido" in x else f"{x['local']}_vs_{x['visitante']}", {}).get("fecha", ""))
        ranking_jornada = []
        
        for j_id, d in datos_globales.items():
            pts_suma_manual = 0
            pts_exacto = 0
            pts_1x2 = 0
            pts_mult = 0
            
            count_1x2 = 0
            count_exacto = 0
            
            for p in partidos_jornada:
                clave_p = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                info_p = d["libro"].get("desglose_partidos", {}).get(clave_p, {})
                pts = info_p.get("puntos_conseguidos", 0)
                mult = info_p.get("multiplicador_aplicado", 1.0)
                pts_suma_manual += pts
                
                pred_p = d["preds"].get(clave_p, {})
                p_real = dict_reales.get(clave_p, {})
                if pts > 0 and pred_p and p_real:
                    pts_base = pts / mult
                    pts_mult += (pts - pts_base)
                    
                    gl_p, gv_p = str(pred_p.get('goles_local', '-')), str(pred_p.get('goles_visitante', '-'))
                    gl_r, gv_r = str(p_real.get('goles_local', 'X')), str(p_real.get('goles_visitante', 'Y'))
                    
                    if gl_p == gl_r and gv_p == gv_r:
                        count_1x2 += 1
                        count_exacto += 1
                        pts_1x2 += 1.0
                        pts_exacto += (pts_base - 1.0)
                    else:
                        count_1x2 += 1
                        pts_1x2 += pts_base
                
            bono = d["libro"].get("desglose_jornadas", {}).get(j_key, {}).get("puntos_bono", 0)
            pts_totales_j = pts_suma_manual + bono
            
            ranking_jornada.append({
                "id": j_id,
                "nombre": d["nombre"],
                "total": pts_totales_j,
                "exactos": pts_exacto,
                "p1x2": pts_1x2,
                "mult": pts_mult,
                "bono": bono,
                "count_1x2": count_1x2,
                "count_exacto": count_exacto,
                "libro": d["libro"],
                "preds": d["preds"],
                "dir_path": d["dir_path"]
            })
            
        ranking_jornada.sort(key=lambda x: (x["total"], x["count_1x2"], x["count_exacto"]), reverse=True)
        rankings_por_jornada[j_key] = ranking_jornada

        if ranking_jornada:
            max_aciertos = max([j["count_1x2"] for j in ranking_jornada])
            min_aciertos = min([j["count_1x2"] for j in ranking_jornada])
            
            ganadores = [j for j in ranking_jornada if j["count_1x2"] == max_aciertos]
            perdedores = [j for j in ranking_jornada if j["count_1x2"] == min_aciertos]
            
            def formatear_nombres(lista_jugadores):
                nombres = [g["nombre"] for g in lista_jugadores]
                if len(nombres) == 1: return nombres[0]
                return " y ".join(nombres) if len(nombres) == 2 else ", ".join(nombres[:-1]) + " y " + nombres[-1]

            nombres_ganadores = formatear_nombres(ganadores)
            nombres_perdedores = formatear_nombres(perdedores)
            
            tit_ganador = "Campeón de la Jornada" if len(ganadores) == 1 else "Campeones de la Jornada"
            tit_perdedor = "Perdedor de la Jornada" if len(perdedores) == 1 else "Perdedores de la Jornada"
            
            style_g = "font-size: 1.6em;" if len(ganadores) >= 3 else "font-size: 2.2em;"
            style_p = "font-size: 1.6em;" if len(perdedores) >= 3 else "font-size: 2.2em;"

            html += f"""
            <div class="cards-wrapper">
                <div class="mvp-card">
                    <div class="card-title">{tit_ganador}</div>
                    <div class="card-name" style="{style_g}">{nombres_ganadores}</div>
                    <div class="card-pts">{max_aciertos} Aciertos</div>
                </div>
                <div class="loser-card">
                    <div class="card-title">{tit_perdedor}</div>
                    <div class="card-name" style="{style_p}">{nombres_perdedores}</div>
                    <div class="card-pts">{min_aciertos} Aciertos</div>
                </div>
            </div>
            """

        html += """<div class="table-wrapper-spaced"><table class="table-jornada"><tr><th style="text-align:center; color:#ccc;">PARTICIPANTE</th>"""
        for p in partidos_jornada:
            clave_p = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
            p_real = dict_reales.get(clave_p, {})
            
            loc = p_real.get("local") or p.get("local", "")
            vis = p_real.get("visitante") or p.get("visitante", "")
            if not loc and "id_partido" in p: loc, vis = f"Eq.{p['id_partido']}A", f"Eq.{p['id_partido']}B"
            
            loc_short = acortar_nombre(loc)
            vis_short = acortar_nombre(vis)
            
            if p_real.get("estado") == "jugandose":
                marcador = f"<br><span class='live-score'>{p_real.get('goles_local')} - {p_real.get('goles_visitante')}</span><span class='live-ball'>⚽</span>"
            elif p_real.get("estado") == "finished":
                marcador = f"<br><span style='font-size:0.8em; color:#888;'>{p_real.get('goles_local')} - {p_real.get('goles_visitante')}</span>"
            else:
                marcador = ""
                
            html += f"<th><span style='font-size:0.8em; color:gray;'>MATCH</span><br><span style='color:white; font-size:1.1em;'>{loc_short} - {vis_short}</span>{marcador}</th>"
        html += "<th style='color:#ccc;'>TOTAL</th></tr>"

        for j in ranking_jornada:
            html += f"<tr><td style='text-align:center; font-weight:bold;'><a href='participantes/{j['id']}/vistas/dashboard.html' style='color:white; text-decoration:none; font-size:1.1em;'>{j['nombre']}</a></td>"
            
            for p in partidos_jornada:
                clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                info_p = j["libro"].get("desglose_partidos", {}).get(clave, {})
                pred_p = j["preds"].get(clave, {})
                
                if not pred_p:
                    html += "<td><span style='color:gray;'>-</span></td>"
                    continue
                    
                gl_p, gv_p = pred_p.get('goles_local', '-'), pred_p.get('goles_visitante', '-')
                pts = info_p.get('puntos_conseguidos', 0)
                mult = info_p.get('multiplicador_aplicado', 1.0)
                
                p_real = dict_reales.get(clave, {})
                gl_r = str(p_real.get("goles_local", "X"))
                gv_r = str(p_real.get("goles_visitante", "Y"))
                
                if pts > 0:
                    if str(gl_p) == gl_r and str(gv_p) == gv_r:
                        color_pts = "#4CAF50" 
                    else:
                        color_pts = "#64B5F6" 
                else:
                    color_pts = "gray" 
                
                celda = f"<span class='cell-pred'>{gl_p} - {gv_p}</span>"
                celda += f"<span style='color:{color_pts}; font-weight:bold;'>{pts:.1f} pts</span>"
                
                if mult > 1.0:
                    fase_limpia = j_key.split(".")[0] if "." in j_key else j_key
                    loc_r = p_real.get("local") or p.get("local", "")
                    vis_r = p_real.get("visitante") or p.get("visitante", "")
                    
                    r_loc = html_utils.obtener_racha_fases(j["dir_path"], loc_r, fase_limpia)
                    r_vis = html_utils.obtener_racha_fases(j["dir_path"], vis_r, fase_limpia)
                    
                    def fmt_link(r):
                        fase_url = r[1].split('/')[-2]
                        if "base.json" in r[1]: fase_url = "grupos"
                        return f"<a href='participantes/{j['id']}/vistas/pronostico_{fase_url}.html' target='_blank' style='color:#88b04b; text-decoration:none;'>+{html_utils.CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a>"
                        
                    r_loc_html = "<br>".join([fmt_link(r) for r in r_loc]) if r_loc else "<span style='color:gray'>-</span>"
                    r_vis_html = "<br>".join([fmt_link(r) for r in r_vis]) if r_vis else "<span style='color:gray'>-</span>"
                    
                    content_html = f"""
                    <div style='display:flex; justify-content:space-between; gap:10px; font-size:0.9em;'>
                        <div style='flex:1; text-align:right;'><strong>{acortar_nombre(loc_r)}</strong><br>{r_loc_html}</div>
                        <div style='flex:1; text-align:left; border-left:1px solid #444; padding-left:10px;'><strong>{acortar_nombre(vis_r)}</strong><br>{r_vis_html}</div>
                    </div>
                    """
                    celda += f"<br><details class='cell-mult-details'><summary>x{mult} ▼</summary><div class='cell-mult-content'>{content_html}</div></details>"
                    
                html += f"<td>{celda}</td>"
                
            html += f"<td class='cell-pts'>{j['total']:.1f}</td></tr>"
            
        html += "</table></div>"
        
        html += f"""
        <div class="chart-container">
            <canvas id="chart-{j_key}"></canvas>
        </div>
        """
        html += "</div>"

    html += """
    </div>
    <script>
        function openJornada(jornadaId, btnEl) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
            
            document.getElementById(jornadaId).classList.add('active');
            if(btnEl) btnEl.classList.add('active');
        }
    """
    
    for j_key in jornadas_keys:
        bloq, _ = esta_bloqueado(j_key)
        if bloq: continue
        
        r = rankings_por_jornada.get(j_key, [])
        
        puntos = [x["total"] for x in r]
        max_p = max(puntos) if puntos else 0
        min_p = min(puntos) if puntos else 0
        
        bg_colors = []
        bd_colors = []
        for x in r:
            if max_p == min_p or max_p == 0:
                opacidad = 0.8
            else:
                opacidad = 0.2 + 0.8 * ((x["total"] - min_p) / (max_p - min_p))
            
            bg_colors.append(f"rgba(218, 165, 32, {opacidad:.2f})")
            bd_colors.append(f"rgba(218, 165, 32, {min(1.0, opacidad + 0.2):.2f})")
        
        lbls = json.dumps([x["nombre"] for x in r])
        dats_total = json.dumps([round(x["total"], 2) for x in r])
        dats_ex = json.dumps([round(x["exactos"], 2) for x in r])
        dats_1x2 = json.dumps([round(x["p1x2"], 2) for x in r])
        dats_mult = json.dumps([round(x["mult"], 2) for x in r])
        dats_bn = json.dumps([round(x["bono"], 2) for x in r])
        
        bg_colors_json = json.dumps(bg_colors)
        bd_colors_json = json.dumps(bd_colors)
        
        html += f"""
        setTimeout(() => {{
            const ctx_{j_key.replace('.','_')} = document.getElementById('chart-{j_key}');
            if (ctx_{j_key.replace('.','_')}) {{
                new Chart(ctx_{j_key.replace('.','_')}, {{
                    type: 'bar',
                    data: {{
                        labels: {lbls},
                        datasets: [{{
                            label: 'Puntos Totales',
                            data: {dats_total},
                            backgroundColor: {bg_colors_json},
                            borderColor: {bd_colors_json},
                            borderWidth: 1,
                            borderRadius: 4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        let idx = context.dataIndex;
                                        let total = context.parsed.y;
                                        
                                        let arr_ex = {dats_ex};
                                        let arr_1x2 = {dats_1x2};
                                        let arr_mult = {dats_mult};
                                        let arr_bn = {dats_bn};
                                        
                                        let ex = arr_ex[idx];
                                        let p1x2 = arr_1x2[idx];
                                        let mult = arr_mult[idx];
                                        let bn = arr_bn[idx];
                                        
                                        let lines = ['Total: ' + total + ' pts'];
                                        if (bn !== 0) lines.push((bn > 0 ? '+' : '') + bn + ' por jornada (ganar/perder)');
                                        if (ex > 0) lines.push('+' + ex + ' por acierto exacto');
                                        if (p1x2 > 0) lines.push('+' + p1x2 + ' por acierto 1X2');
                                        if (mult > 0) lines.push('+' + mult + ' gracias a multiplicadores');
                                        
                                        return lines;
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{ beginAtZero: true, grid: {{ color: 'rgba(255, 255, 255, 0.05)' }} }},
                            x: {{ grid: {{ display: false }} }}
                        }}
                    }}
                }});
            }}
        }}, 500);
        """

    html += """
    </script>
</body>
</html>
    """

    with open(ROOT_DIR / "jornadas.html", 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ Vista de Jornadas (jornadas.html) recalibrada y generada con éxito.")

if __name__ == "__main__":
    generar_jornadas_html()