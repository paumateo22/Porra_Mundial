import sys
import json
import re
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

def generar_jornadas_html():
    print("=======================================================")
    print(" 📊 [07B8] GENERANDO VISTA CENTRAL DE JORNADAS 📊")
    print("=======================================================")

    jornadas_dict = html_utils.cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    jornadas_keys = list(jornadas_dict.keys())
    realidad_dict = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    
    # Preparamos los nombres reales para los multiplicadores
    dict_reales = {}
    for g, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos: dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    for f, partidos in realidad_dict.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p: dict_reales[f"ID_{p['id_partido']}"] = p

    # Cargar participantes
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
        /* Expansión del contenedor central solo para esta vista */
        .container {{ max-width: 1450px !important; margin: 0 auto; }}

        .sticky-nav {{ position: sticky; top: 0; z-index: 1000; background: rgba(18,18,18,0.95); padding: 12px; border-bottom: 2px solid var(--gold); display: flex; gap: 10px; justify-content: center; overflow-x: auto; flex-wrap: nowrap; backdrop-filter: blur(5px); box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 20px; }}
        .nav-btn {{ background: #222; color: white; border: 1px solid #444; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.2s; white-space: nowrap; }}
        .nav-btn.active, .nav-btn:hover {{ background: var(--gold); color: black; border-color: var(--gold); }}
        
        .tab-content {{ display: none; animation: fadeIn 0.4s; }}
        .tab-content.active {{ display: block; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        
        .mvp-card {{ background: linear-gradient(135deg, #DAA520 0%, #b8860b 100%); color: black; border-radius: 12px; padding: 20px; text-align: center; margin: 0 auto 30px auto; max-width: 400px; box-shadow: 0 8px 20px rgba(0,0,0,0.5); position: relative; overflow: hidden; border: 2px solid #fff; }}
        .mvp-card::after {{ content: '👑'; position: absolute; font-size: 6em; opacity: 0.15; right: -10px; top: -20px; transform: rotate(15deg); pointer-events: none; }}
        .mvp-title {{ font-weight: 900; font-size: 1.2em; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; opacity: 0.9; }}
        .mvp-name {{ font-size: 2.2em; font-weight: 900; margin: 5px 0; }}
        .mvp-pts {{ font-size: 1.4em; font-family: monospace; font-weight: bold; background: rgba(0,0,0,0.1); display: inline-block; padding: 5px 15px; border-radius: 20px; }}

        /* Ajustes de Tabla para evitar desbordamientos */
        .table-wrapper-spaced {{ overflow-x: auto; padding-bottom: 120px; margin-bottom: -90px; }}
        .table-jornada {{ width: 100%; min-width: 1100px; border-collapse: collapse; }}
        .table-jornada th {{ text-align: center; font-size: 0.8em; padding: 12px 4px; border-bottom: 2px solid #333; }}
        .table-jornada td {{ text-align: center; padding: 12px 4px; font-size: 0.9em; position: relative; border-bottom: 1px solid #222; }}
        .cell-pts {{ color: var(--gold); font-weight: bold; font-size: 1.1em; }}
        .cell-pred {{ margin-bottom: 4px; display: block; color: #ddd; letter-spacing: 1px; }}
        
        /* Desplegable Multiplicador CSS mejorado */
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
            
        partidos_jornada = jornadas_dict[j_key]
        ranking_jornada = []
        
        for j_id, d in datos_globales.items():
            pts_suma_manual = 0
            for p in partidos_jornada:
                clave_p = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                pts_suma_manual += d["libro"].get("desglose_partidos", {}).get(clave_p, {}).get("puntos_conseguidos", 0)
                
            bono = d["libro"].get("desglose_jornadas", {}).get(j_key, {}).get("puntos_bono", 0)
            pts_totales_j = pts_suma_manual + bono
            
            ranking_jornada.append({
                "id": j_id,
                "nombre": d["nombre"],
                "total": pts_totales_j,
                "libro": d["libro"],
                "preds": d["preds"],
                "dir_path": d["dir_path"]
            })
            
        ranking_jornada.sort(key=lambda x: x["total"], reverse=True)

        if ranking_jornada and ranking_jornada[0]["total"] > 0:
            mvp = ranking_jornada[0]
            html += f"""
            <div class="mvp-card">
                <div class="mvp-title">MVP de la Jornada</div>
                <div class="mvp-name">{mvp["nombre"]}</div>
                <div class="mvp-pts">{mvp["total"]} Puntos</div>
            </div>
            """

        # Tabla de Partidos
        html += """<div class="table-wrapper-spaced"><table class="table-jornada"><tr><th style="text-align:left; color:#ccc;">PARTICIPANTE</th>"""
        for p in partidos_jornada:
            loc = p.get("local", "")
            vis = p.get("visitante", "")
            if not loc and "id_partido" in p: loc, vis = f"Eq.{p['id_partido']}A", f"Eq.{p['id_partido']}B"
            html += f"<th><span style='font-size:0.8em; color:gray;'>MATCH</span><br><span style='color:white; font-size:1.1em;'>{loc[:3]} - {vis[:3]}</span></th>"
        html += "<th style='color:#ccc;'>TOTAL</th></tr>"

        for j in ranking_jornada:
            html += f"<tr><td style='text-align:left; font-weight:bold;'><a href='participantes/{j['id']}/vistas/dashboard.html' style='color:white; text-decoration:none; font-size:1.1em;'>{j['nombre']}</a></td>"
            
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
                
                color_pts = "var(--gold)" if pts > 0 else "gray"
                celda = f"<span class='cell-pred'>{gl_p} - {gv_p}</span>"
                celda += f"<span style='color:{color_pts}; font-weight:bold;'>{pts:.1f} pts</span>"
                
                if mult > 1.0:
                    fase_limpia = j_key.split(".")[0] if "." in j_key else j_key
                    p_real = dict_reales.get(clave, {})
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
                        <div style='flex:1; text-align:right;'><strong>{loc_r[:3]}</strong><br>{r_loc_html}</div>
                        <div style='flex:1; text-align:left; border-left:1px solid #444; padding-left:10px;'><strong>{vis_r[:3]}</strong><br>{r_vis_html}</div>
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
        
        r = []
        for j_id, d in datos_globales.items():
            pts_suma_manual = 0
            for p in jornadas_dict[j_key]:
                clave_p = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                pts_suma_manual += d["libro"].get("desglose_partidos", {}).get(clave_p, {}).get("puntos_conseguidos", 0)
            bono = d["libro"].get("desglose_jornadas", {}).get(j_key, {}).get("puntos_bono", 0)
            r.append({"n": d["nombre"], "t": pts_suma_manual + bono})
            
        r.sort(key=lambda x: x["t"], reverse=True)
        lbls = json.dumps([x["n"] for x in r])
        dats = json.dumps([x["t"] for x in r])
        
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
                            data: {dats},
                            backgroundColor: 'rgba(218, 165, 32, 0.7)',
                            borderColor: 'rgba(218, 165, 32, 1)',
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
                                    label: function(context) {{ return context.parsed.y + ' pts'; }}
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