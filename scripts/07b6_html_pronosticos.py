import sys
import json
import csv  # Inyectamos csv para procesar el archivo de registro
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

PTS_1X2 = html_utils.CONFIG.get("puntuacion", {}).get("acierto_1x2", 1)
PTS_EX = html_utils.CONFIG.get("puntuacion", {}).get("acierto_exacto", 3)

FASES_ORDEN = ["grupos", "dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

def format_fase(fase):
    mapeo = {
        "dieciseisavos.1": "1/16-1",
        "dieciseisavos.2": "1/16-2",
        "grupos": "Grupos",
        "dieciseisavos": "1/16",
        "octavos": "1/8",
        "cuartos": "1/4",
        "semifinales": "Semis",
        "finales": "Finales",
        "premios": "Premios"
    }
    return mapeo.get(fase.lower(), fase.upper())

def get_nav_html(fase_actual):
    nav = """<div class="sticky-nav" style="position: sticky; top: 0; z-index: 1000; background: rgba(18,18,18,0.95); padding: 12px; border-bottom: 2px solid var(--gold); display: flex; gap: 10px; justify-content: center; overflow-x: auto; flex-wrap: nowrap; backdrop-filter: blur(5px); box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 20px;">
        <a href="dashboard.html" style="background:#111; color:gray;">⬅️ Volver al Dashboard</a>
        <span style="border-left:1px solid #444; margin:0 5px;"></span>"""
    
    fases_todas = ["grupos", "dieciseisavos", "octavos", "cuartos", "semifinales", "finales", "premios"]
    
    for f in fases_todas:
        active_style = "background:var(--gold); color:black; border-color:var(--gold);" if f == fase_actual else "background:#333; color:white; border:1px solid #444;"
        nav += f"""\n        <a href="pronostico_{f}.html" style="text-decoration:none; font-size:0.85em; font-weight:bold; white-space:nowrap; padding:8px 15px; border-radius:4px; transition:0.3s; {active_style}">{format_fase(f)}</a>"""
    
    nav += "\n    </div>"
    return nav

def esta_bloqueado(fase):
    """Comprueba si la fase actual tiene un bloqueo de tiempo en settings.json"""
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

def render_bracket_futuro(eliminatorias_dict, fase_inicio):
    """Genera el árbol (bracket) de torneo convergente para la proyección futura."""
    if not eliminatorias_dict: return "<p style='color:gray; text-align:center; padding: 20px;'>No hay predicciones futuras registradas en este archivo.</p>"
    
    idx_inicio = FASES_ORDEN.index(fase_inicio) if fase_inicio in FASES_ORDEN else 0
    fases_dibujar = FASES_ORDEN[idx_inicio+1:]
    
    if not fases_dibujar: return "<p style='color:gray; text-align:center; padding: 20px;'>No hay rondas posteriores en esta proyección.</p>"

    es_fase_temprana = fase_inicio in ["grupos", "dieciseisavos"]
    
    col_min_width = "110px" if es_fase_temprana else "160px"
    gap_cols = "8px" if es_fase_temprana else "20px"
    gap_center = "15px" if es_fase_temprana else "30px"
    box_padding = "6px 8px" if es_fase_temprana else "10px 12px"
    box_margin = "4px 0" if es_fase_temprana else "8px 0"
    font_size = "0.7em" if es_fase_temprana else "0.85em"
    max_chars = 11 if es_fase_temprana else 14

    def get_matches_for_phase(f):
        if f == "finales":
            final_match, third_match = None, None
            if "final" in eliminatorias_dict: final_match = eliminatorias_dict["final"][0] if eliminatorias_dict["final"] else None
            if "tercer_puesto" in eliminatorias_dict: third_match = eliminatorias_dict["tercer_puesto"][0] if eliminatorias_dict["tercer_puesto"] else None
            if not final_match and "finales" in eliminatorias_dict:
                arr = eliminatorias_dict["finales"]
                if len(arr) >= 2:
                    third_match, final_match = arr[0], arr[1]
                elif len(arr) == 1:
                    final_match = arr[0]
            return [third_match, final_match] if third_match and final_match else ([final_match] if final_match else [])
        return eliminatorias_dict.get(f, [])

    def render_match_bracket(p):
        if not p: return "<div></div>"
        loc = p.get('local', 'TBD')
        vis = p.get('visitante', 'TBD')
        pasa = p.get('pasa', '')
        
        c_loc = "color:var(--gold); font-weight:bold;" if pasa and pasa == loc and loc != 'TBD' else "color:#ccc;"
        c_vis = "color:var(--gold); font-weight:bold;" if pasa and pasa == vis and vis != 'TBD' else "color:#ccc;"
        
        loc_str = loc[:max_chars] + '...' if len(loc) > max_chars else loc
        vis_str = vis[:max_chars] + '...' if len(vis) > max_chars else vis
        
        return f"""
        <div style="background:#222; border:1px solid #333; border-radius:6px; padding:{box_padding}; margin:{box_margin}; font-size:{font_size}; box-shadow:0 2px 5px rgba(0,0,0,0.4); text-align:center;">
            <div style="display:flex; justify-content:center; border-bottom:1px solid #333; padding-bottom:4px; margin-bottom:4px;">
                <span style="{c_loc}">{loc_str}</span>
            </div>
            <div style="display:flex; justify-content:center;">
                <span style="{c_vis}">{vis_str}</span>
            </div>
        </div>"""

    html = f"""
    <div style="width:100%; overflow-x:auto;">
        <div style="display:flex; justify-content:center; align-items:stretch; gap:{gap_cols}; padding:20px 10px; min-width:max-content; margin:0 auto;">
    """
    
    mitades_left = []
    mitades_right = []
    center_html = ""

    for f in fases_dibujar:
        partidos = get_matches_for_phase(f)
        
        if f == "finales":
            c_html = f"<div style='flex:1; min-width:{col_min_width}; display:flex; flex-direction:column; justify-content:center; gap:{gap_center};'>"
            if len(partidos) == 2:
                c_html += f"<div style='text-align:center;'><div style='color:var(--gold); font-size:0.75em; margin-bottom:4px; font-weight:bold;'>🏆 FINAL</div>{render_match_bracket(partidos[1])}</div>"
                c_html += f"<div style='text-align:center;'><div style='color:#a9b7c6; font-size:0.75em; margin-bottom:4px; font-weight:bold;'>🥉 3º PUESTO</div>{render_match_bracket(partidos[0])}</div>"
            elif len(partidos) == 1:
                c_html += f"<div style='text-align:center;'><div style='color:var(--gold); font-size:0.75em; margin-bottom:4px; font-weight:bold;'>🏆 FINAL</div>{render_match_bracket(partidos[0])}</div>"
            c_html += "</div>"
            center_html = c_html
        else:
            n = len(partidos)
            if n > 0:
                mitad = n // 2
                left = partidos[:mitad]
                right = partidos[mitad:]
                
                col_l = f"<div style='flex:1; min-width:{col_min_width}; display:flex; flex-direction:column;'>"
                col_l += f"<div style='text-align:center; color:gray; font-size:0.75em; font-weight:bold; border-bottom:1px solid #444; padding-bottom:5px; margin-bottom:10px;'>{format_fase(f)}</div>"
                col_l += "<div style='flex:1; display:flex; flex-direction:column; justify-content:space-around;'>"
                for p in left: col_l += render_match_bracket(p)
                col_l += "</div></div>"
                mitades_left.append(col_l)
                
                col_r = f"<div style='flex:1; min-width:{col_min_width}; display:flex; flex-direction:column;'>"
                col_r += f"<div style='text-align:center; color:gray; font-size:0.75em; font-weight:bold; border-bottom:1px solid #444; padding-bottom:5px; margin-bottom:10px;'>{format_fase(f)}</div>"
                col_r += "<div style='flex:1; display:flex; flex-direction:column; justify-content:space-around;'>"
                for p in right: col_r += render_match_bracket(p)
                col_r += "</div></div>"
                mitades_right.insert(0, col_r)

    for col in mitades_left: html += col
    if center_html: html += center_html
    for col in mitades_right: html += col

    html += "</div></div>"
    return html

def generar_vistas_pronosticos():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    total_jugadores = len(jugadores)
    
    jornadas_dict = html_utils.cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    jornadas_keys = list(jornadas_dict.keys())
    realidad_dict = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    premios_reales = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "premios_oficiales.json") or {}
    
    # -----------------------------------------------------
    # 🔐 EXTRACCIÓN DE CONTRASEÑAS DESDE INSCRIPCION.CSV
    # -----------------------------------------------------
    ruta_csv = ROOT_DIR / "inscripcion.csv"
    claves_usuarios = {}
    if ruta_csv.exists():
        with open(ruta_csv, mode='r', encoding='utf-8') as f:
            lector = csv.DictReader(f)
            for fila in lector:
                nom_limpio = fila.get('Nombre', '').strip().lower().replace(' ', '_')
                clave = fila.get('clave_acceso', '').strip()
                if nom_limpio and clave:
                    claves_usuarios[nom_limpio] = clave

    dict_reales = {}
    for g, partidos in realidad_dict.get("fase_grupos", {}).items():
        for p in partidos: dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    for f, partidos in realidad_dict.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p: dict_reales[f"ID_{p['id_partido']}"] = p

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

    for j_dir in jugadores:
        nombre = j_dir.name.replace('_', ' ').title()
        dir_vistas = j_dir / "vistas"
        dir_vistas.mkdir(parents=True, exist_ok=True)
        
        libro_stats = html_utils.cargar_json(j_dir / "estadisticas" / "historial_puntos.json") or {}
        desglose_j = libro_stats.get("desglose_jornadas", {})
        desglose_p = libro_stats.get("desglose_partidos", {})
        
        clave_usuario = claves_usuarios.get(j_dir.name, "adminporra2026") # Clave por defecto si no se encuentra

        # ==========================================
        # 1. FASES DEL TORNEO (Grupos -> Finales)
        # ==========================================
        for fase in FASES_ORDEN:
            if fase == "grupos":
                ruta_json = j_dir / "pronosticos" / "grupos" / f"{j_dir.name}_base.json"
            else:
                ruta_json = j_dir / "pronosticos" / "eliminatorias" / fase / f"{fase}.json"
            
            pronostico_data = html_utils.cargar_json(ruta_json) or {}
            
            dict_preds = {}
            if fase == "grupos":
                for p_list in pronostico_data.get("fase_grupos", {}).values():
                    for pp in p_list: dict_preds[f"{pp['local']}_vs_{pp['visitante']}"] = pp
            else:
                for f_dest, p_list in pronostico_data.get("predicciones", {}).items():
                    if f_dest == "dieciseisavos":
                        off_matches = jornadas_dict.get("dieciseisavos.1", []) + jornadas_dict.get("dieciseisavos.2", [])
                    elif f_dest in ["finales", "final", "tercer_puesto"]:
                        off_matches = jornadas_dict.get("finales", [])
                    else:
                        off_matches = jornadas_dict.get(f_dest, [])
                        
                    for i, p_off in enumerate(off_matches):
                        if i < len(p_list): dict_preds[f"ID_{p_off['id_partido']}"] = p_list[i]

            html = f"""<!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Pronósticos {format_fase(fase)} | {nombre}</title>
                <link rel="stylesheet" href="../../../theme.css">
                <style>
                    .match-grid-2col {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
                    .group-grid-2col {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
                    @media (max-width: 768px) {{ .match-grid-2col, .group-grid-2col {{ grid-template-columns: 1fr; }} }}
                    .pred-summary {{ margin:0; cursor:pointer; list-style:none; outline:none; }}
                    .pred-summary::-webkit-details-marker {{ display:none; }}
                    .pred-summary::marker {{ display:none; }}
                    .pred-card-details {{ margin:0 auto; width: 100%; max-width: 350px; background: #1a1a1a; padding: 10px; border-radius: 6px; border: 1px solid #333; }}
                    .pred-card-details[open] {{ background: #1f1f1f; }}
                    .jornada-details > summary h3::after, .jornada-details > summary h2::after {{ content: ' ▼'; font-size: 0.7em; color: gray; transition: 0.3s; margin-left: 8px; }}
                    .jornada-details[open] > summary h3::after, .jornada-details[open] > summary h2::after {{ content: ' ▲'; color: var(--gold); }}
                </style>
                <script>
                    function openTab(tabName) {{
                        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                        document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
                        document.getElementById(tabName).classList.add('active');
                        event.currentTarget.classList.add('active');
                    }}
                    
                    // Función para forzar la apertura del candado en el cliente
                    function verificarClaveFase() {{
                        const inputClave = document.getElementById("bypass-pass").value;
                        const claveCorrecta = "{clave_usuario}";
                        if (inputClave === claveCorrecta) {{
                            document.getElementById("lock-screen-container").style.display = "none";
                            document.getElementById("protected-content-container").style.display = "block";
                        }} else {{
                            const errEl = document.getElementById("bypass-error");
                            errEl.style.display = "block";
                            errEl.innerText = "⚠️ Contraseña incorrecta. Pídesela al administrador o al participante.";
                        }}
                    }}
                </script>
            </head>
            <body>
                {html_utils.get_sidebar_html("../../../")}
                {html_utils.get_header_html(f" 📓 Pronósticos : {nombre}", f"Pronóstico enviado en la fase: <strong>{format_fase(fase)}</strong>", "../../../")}
                {get_nav_html(fase)}
                <div class="container">
            """

            bloqueado, fecha_apertura = esta_bloqueado(fase)
            
            # Bloque de interfaz de Candado (Solo visible si 'bloqueado' es True)
            display_candado = "block" if bloqueado else "none"
            html += f"""
                <div id="lock-screen-container" style="display:{display_candado}; background:#111; padding:40px 20px; text-align:center; border:1px solid #333; border-radius:8px; margin-top:20px;">
                    <div style="font-size:3.5em; margin-bottom:15px;">🔒</div>
                    <h2 style="color:var(--gold); margin-top:0;">Pronóstico Protegido</h2>
                    <p style="color:#ddd; font-size:1.1em; margin-bottom:5px;">El pronóstico de <strong>{nombre}</strong> ha sido recibido y está guardado a salvo.</p>
                    <p style="color:gray; font-size:0.95em; margin-bottom:25px;">Se revelará públicamente el <strong>{fecha_apertura}</strong> (Hora Peninsular).</p>
                    
                    <div style="max-width:320px; margin:0 auto; padding-top:20px; border-top:1px dashed #333;">
                        <label style="display:block; font-size:0.85em; color:gray; margin-bottom:8px; font-weight:bold;">🔓 DESBLOQUEO MANUAL CON CONTRASEÑA</label>
                        <input type="password" id="bypass-pass" placeholder="Introduce la clave de acceso" style="width:100%; padding:10px; border-radius:6px; border:1px solid #444; background:#222; color:white; box-sizing:border-box; text-align:center; margin-bottom:10px; font-size:1em;">
                        <button onclick="verificarClaveFase()" style="width:100%; padding:10px; border-radius:6px; background:var(--gold); color:black; font-weight:bold; border:none; cursor:pointer; font-size:0.95em; transition:0.2s;">Desbloquear Vista</button>
                        <p id="bypass-error" style="color:#ff4d4d; font-size:0.85em; margin-top:10px; display:none; font-weight:bold;"></p>
                    </div>
                </div>
            """

            # Contenedor del contenido del pronóstico (Oculto si está bloqueado)
            display_contenido = "none" if bloqueado else "block"
            html += f"""<div id="protected-content-container" style="display:{display_contenido};">"""

            if not pronostico_data:
                html += f"""<div style="background:#111; padding:30px; text-align:center; border:1px solid #333; border-radius:8px; color:gray;">
                    <h3>El archivo de pronóstico para {format_fase(fase)} no existe o no se rellenó.</h3>
                </div>"""
            else:
                # --- SECCIÓN 1: COMPARATIVA DE LA FASE ACTUAL ---
                if fase == "grupos":
                    html += f"""
                    <details class="jornada-details" open style="margin-bottom:20px; background:#151515; padding:15px; border-radius:8px; border:1px solid #333;">
                        <summary style="cursor:pointer; border:none; outline:none;"><h2 style="display:inline-block; margin-top:0; color:var(--gold);">🌍 FASE DE GRUPOS (Comparativa)</h2></summary>
                        <div class="tabs-container">
                            <button class="tab-btn active" onclick="openTab('tab-grupos-jaj')">Jornada a Jornada (JaJ)</button>
                            <button class="tab-btn" onclick="openTab('tab-grupos-gag')">Grupo a Grupo (GaG)</button>
                        </div>
                        <div id="tab-grupos-jaj" class="tab-content active">
                    """
                    jornadas_grupos = [k for k in jornadas_keys if k.startswith("J")]
                    
                    for j_key in jornadas_grupos:
                        html += f"<details class='jornada-details' open style='margin-bottom:20px; background:#111; padding:15px; border-radius:8px; border:1px solid #333;'>"
                        html += f"<summary style='border:none; padding:0; margin:0; outline:none; cursor:pointer;'><h3 style='color:var(--table-header); margin-top:0; text-align:center; border-bottom:1px solid #444; padding-bottom:5px; display:inline-block; width:100%;'>📌 {format_fase(j_key)}</h3></summary>"
                        html += "<div class='match-grid-2col' style='margin-top:15pxFilter;'>"
                        
                        pts_jornada = exactos_j = 0
                        for p in jornadas_dict[j_key]:
                            clave = f"{p['local']}_vs_{p['visitante']}"
                            info_p = desglose_p.get(clave, {})
                            p_real = dict_reales.get(clave, {})
                            p_pred = dict_preds.get(clave, {})
                            
                            loc_r = p_real.get("local") or p.get("local", "TBD")
                            vis_r = p_real.get("visitante") or p.get("visitante", "TBD")
                            pred_txt = f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}" if p_pred else "-"
                            real_txt = f"{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}" if p_real.get("estado") == "finished" else "⏳"
                            
                            ac_ex, ac_1x2 = info_p.get("acierto_exacto", False), info_p.get("acierto_1x2", False)
                            if ac_ex: pred_styled = f"<span class='pred-exact'>{pred_txt} ({PTS_1X2} + {PTS_EX})</span>"
                            elif ac_1x2: pred_styled = f"<span class='pred-1x2'>{pred_txt} ({PTS_1X2})</span>"
                            else: pred_styled = f"<span class='pred-miss'>{pred_txt} (0)</span>"

                            pts = info_p.get("puntos_conseguidos", 0)
                            if ac_ex: exactos_j += 1
                            pts_jornada += pts
                            
                            html += f"""
                            <div style="background:#111; border:1px solid #333; border-radius:4px; padding:10px;">
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
                        rank_j = rankings_jornada.get(j_key, {}).get(j_dir.name, "-")
                        
                        html += f"""
                        <div style="background:#222; padding:10px; margin-top:15px; border-left:4px solid var(--gold); border-radius:4px; font-size:0.9em; line-height:1.4;">
                            Resumen {format_fase(j_key)}: {exactos_j}/{info_dj.get('aciertos_1x2', 0)} (Clavados/Aciertos). Posición {rank_j} de {total_jugadores}.<br>
                            Resultado: {res_bono} ({signo}{res_val} pts)<br>
                            TOTAL JORNADA: {pts_jornada + res_val} pts
                        </div></details>"""
                    html += "</div>"
                    
                    html += """<div id="tab-grupos-gag" class="tab-content"><div class="group-grid-2col">"""
                    for grupo, partidos in sorted(pronostico_data.get("fase_grupos", {}).items()):
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
                                        <tr class="gag-pred-row"><td colspan="3" style="padding-top:2px; padding-bottom:8px; color:gray;">Pronóstico: {pred_styled} <span style="float:right; color:var(--gold); font-weight:bold;">{pts} pts</span></td></tr>"""
                        html += f"""<tr><td colspan="3" class="gag-total-row">Total Grupo: {pts_grupo} pts</td></tr></table></div>"""
                    html += "</div></div></details>"

                else:
                    # FASE ELIMINATORIA ACTUAL
                    html += f"""
                    <details class="jornada-details" open style="margin-bottom:20px; background:#151515; padding:15px; border-radius:8px; border:1px solid #333;">
                        <summary style="cursor:pointer; border:none; outline:none;"><h2 style="display:inline-block; margin-top:0; color:var(--accent);">⚔️ {format_fase(fase).upper()} (Comparativa Real)</h2></summary>
                    """
                    j_keys_fase = [k for k in jornadas_keys if k.lower().startswith(fase.lower())]
                    
                    for j_key in j_keys_fase:
                        fase_limpia = j_key.split(".")[0] if "." in j_key else j_key
                        html += f"<details class='jornada-details' open style='margin-bottom:20px; background:#111; padding:15px; border-radius:8px; border:1px solid #333;'>"
                        html += f"<summary style='border:none; padding:0; margin:0; outline:none; cursor:pointer;'><h3 style='color:var(--accent); margin-top:0; text-align:center; border-bottom:1px solid #444; padding-bottom:5px; display:inline-block; width:100%;'>📌 {format_fase(j_key)}</h3></summary>"
                        html += "<div class='match-grid-2col' style='margin-top:15pxFilter;'>"
                        
                        pts_jornada = exactos_j = 0
                        for p in jornadas_dict[j_key]:
                            clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
                            info_p = desglose_p.get(clave, {})
                            p_real = dict_reales.get(clave, {})
                            p_pred = dict_preds.get(clave, {})
                            
                            loc_r = p_real.get("local") or p.get("local") or p.get("placeholder_local", "TBD")
                            vis_r = p_real.get("visitante") or p.get("visitante") or p.get("placeholder_visitante", "TBD")
                            if loc_r == "TBD" and "id_partido" in p: loc_r, vis_r = f"Eq. {p['id_partido']}A", f"Eq. {p['id_partido']}B"
                            
                            subtitle_html = ""
                            if j_key.lower() == "finales":
                                if "103" in str(p.get("id_partido", "")): subtitle_html = "<div style='text-align:center; color:#a9b7c6; font-size:0.85em; font-weight:bold; margin-bottom:10px;'>🥉 3º Puesto</div>"
                                if "104" in str(p.get("id_partido", "")): subtitle_html = "<div style='text-align:center; color:var(--gold); font-size:0.85em; font-weight:bold; margin-bottom:10px;'>🏆 Final</div>"

                            if p_pred:
                                loc_p, vis_p = p_pred.get("local", ""), p_pred.get("visitante", "")
                                pred_txt = f"{loc_p} {p_pred.get('goles_local','-')}-{p_pred.get('goles_visitante','-')} {vis_p}" if (loc_p != loc_r or vis_p != vis_r) else f"{p_pred.get('goles_local','-')} - {p_pred.get('goles_visitante','-')}"
                            else: pred_txt = "-"
                            
                            real_txt = f"{p_real.get('goles_local','-')} - {p_real.get('goles_visitante','-')}" if p_real.get("estado") == "finished" else "⏳"
                            
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
                            
                            import re
                            mult_html = f"""<div style="margin-top:10px; padding-top:10px; border-top:1px dotted #555; text-align:center;"><div style="margin-bottom:8px;">{desglose_html}</div>"""
                            if mult > 1.0 and p_real.get("estado") == "finished":
                                r_loc = html_utils.obtener_racha_fases(j_dir, p_real.get("local"), fase_limpia)
                                r_vis = html_utils.obtener_racha_fases(j_dir, p_real.get("visitante"), fase_limpia)
                                r_loc_html = "<br>".join([f"<a href='../../../{r[1]}' target='_blank' style='color:#88b04b; text-decoration:none;'>+{html_utils.CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a>" for r in r_loc]) if r_loc else "<span style='color:gray;'>-</span>"
                                r_vis_html = "<br>".join([f"<a href='../../../{r[1]}' target='_blank' style='color:#88b04b; text-decoration:none;'>+{html_utils.CONFIG['multiplicadores']['incremento_racha_por_fase']} ({r[0]})</a>" for r in r_vis]) if r_vis else "<span style='color:gray;'>-</span>"
                                if "base.html" in r_loc_html: r_loc_html = re.sub(r'pronostico_[^"\'\s]+_base\.html', 'pronostico_grupos.html', r_loc_html)
                                if "base.html" in r_vis_html: r_vis_html = re.sub(r'pronostico_[^"\'\s]+_base\.html', 'pronostico_grupos.html', r_vis_html)
                                mult_html += f"""<div style="display:flex; justify-content:space-between; text-align:center; font-size:0.85em;"><div style="flex:1; padding-right:5px;"><strong>{p_real.get('local')}</strong><br>{r_loc_html}</div><div style="flex:1; padding-left:5px; border-left:1px solid #333;"><strong>{p_real.get('visitante')}</strong><br>{r_vis_html}</div></div>"""
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
                        rank_j = rankings_jornada.get(j_key, {}).get(j_dir.name, "-")
                        
                        html += f"""
                        <div style="background:#222; padding:10px; margin-top:15px; border-left:4px solid var(--gold); border-radius:4px; font-size:0.9em; line-height:1.4;">
                            Resumen {format_fase(j_key)}: {exactos_j}/{info_dj.get('aciertos_1x2', 0)} (Clavados/Aciertos). Posición {rank_j} de {total_jugadores}.<br>
                            Resultado: {res_bono} ({signo}{res_val} pts)<br>
                            TOTAL JORNADA: {pts_jornada + res_val} pts
                        </div></details>"""
                    html += "</details>"

                # --- SECCIÓN 2: ÁRBOL FUTURO (PROYECCIÓN) ---
                if fase != "finales":
                    html += f"""
                    <details class="jornada-details" open style="margin-bottom:20px; background:#151515; padding:15px; border-radius:8px; border:1px solid #333;">
                        <summary style="cursor:pointer; border:none; outline:none;"><h2 style="display:inline-block; margin-top:0; color:#4ade80;">🌳 Proyección del Torneo</h2></summary>
                        <p style="color:gray; font-size:0.9em; margin-bottom:15px;">Así veías tú el resto del torneo desde esta fase (Sin comparar con la realidad).</p>
                    """
                    if fase == "grupos": bracket_data = pronostico_data.get("eliminatorias", {})
                    else: bracket_data = pronostico_data.get("predicciones", {})
                    
                    html += render_bracket_futuro(bracket_data, fase)
                    html += "</details>"

            html += "</div>" # Cierre de protected-content-container
            html += "</div></body></html>"
            with open(dir_vistas / f"pronostico_{fase}.html", 'w', encoding='utf-8') as f: f.write(html)

        # ==========================================
        # 2. PREMIOS INDIVIDUALES
        # ==========================================
        ruta_premios = j_dir / "pronosticos" / "premios" / "premios_formulario.json"
        premios_pred = html_utils.cargar_json(ruta_premios) or {}
        
        html = f"""<!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Pronósticos Premios | {nombre}</title>
            <link rel="stylesheet" href="../../../theme.css">
            <script>
                function verificarClavePremios() {{
                    const inputClave = document.getElementById("bypass-pass").value;
                    const claveCorrecta = "{clave_usuario}";
                    if (inputClave === claveCorrecta) {{
                        document.getElementById("lock-screen-container").style.display = "none";
                        document.getElementById("protected-content-container").style.display = "block";
                    }} else {{
                        const errEl = document.getElementById("bypass-error");
                        errEl.style.display = "block";
                        errEl.innerText = "⚠️ Contraseña incorrecta. Pídesela al administrador o al participante.";
                    }}
                }}
            </script>
        </head>
        <body>
            {html_utils.get_sidebar_html("../../../")}
            {html_utils.get_header_html(f"🏆 Premios Individuales: {nombre}", f"Predicción de Galardones", "../../../")}
            {get_nav_html("premios")}
            <div class="container">
        """

        bloqueado_premios, fecha_apertura_premios = esta_bloqueado("premios")
        
        display_candado_p = "block" if bloqueado_premios else "none"
        html += f"""
            <div id="lock-screen-container" style="display:{display_candado_p}; background:#111; padding:40px 20px; text-align:center; border:1px solid #333; border-radius:8px; margin-top:20px;">
                <div style="font-size:3.5em; margin-bottom:15px;">🔒</div>
                <h2 style="color:var(--gold); margin-top:0;">Pronóstico Protegido</h2>
                <p style="color:#ddd; font-size:1.1em; margin-bottom:5px;">El pronóstico de <strong>{nombre}</strong> ha sido recibido y está guardado a salvo.</p>
                <p style="color:gray; font-size:0.95em; margin-bottom:25px;">Se revelará públicamente el <strong>{fecha_apertura_premios}</strong> (Hora Peninsular).</p>
                
                <div style="max-width:320px; margin:0 auto; padding-top:20px; border-top:1px dashed #333;">
                    <label style="display:block; font-size:0.85em; color:gray; margin-bottom:8px; font-weight:bold;">🔓 DESBLOQUEO MANUAL CON CONTRASEÑA</label>
                    <input type="password" id="bypass-pass" placeholder="Introduce la clave de acceso" style="width:100%; padding:10px; border-radius:6px; border:1px solid #444; background:#222; color:white; box-sizing:border-box; text-align:center; margin-bottom:10px; font-size:1em;">
                    <button onclick="verificarClavePremios()" style="width:100%; padding:10px; border-radius:6px; background:var(--gold); color:black; font-weight:bold; border:none; cursor:pointer; font-size:0.95em; transition:0.2s;">Desbloquear Vista</button>
                    <p id="bypass-error" style="color:#ff4d4d; font-size:0.85em; margin-top:10px; display:none; font-weight:bold;"></p>
                </div>
            </div>
        """

        display_contenido_p = "none" if bloqueado_premios else "block"
        html += f"""<div id="protected-content-container" style="display:{display_contenido_p};">"""

        if not premios_pred:
            html += f"""<div style="background:#111; padding:30px; text-align:center; border:1px solid #333; border-radius:8px; color:gray;">
                <h3>Aún no has rellenado el formulario de Premios Individuales.</h3>
            </div>"""
        else:
            html += f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div style="background:#151515; padding:20px; border-radius:8px; border:1px solid #333;">
                    <h2 style="color:var(--gold); border-bottom:1px solid #444; padding-bottom:10px; margin-top:0; text-align:center; width:100%; display:block;">Tu Pronóstico</h2>
                    <div style="display:flex; flex-direction:column; gap:15px; margin-top:15px;">
            """
            for k, v in premios_pred.items():
                if k == "participante": continue
                val_real = premios_reales.get(k, "")
                color_valor = "#4ade80" if val_real and str(v).lower().strip() == str(val_real).lower().strip() else "white"
                
                html += f"""
                    <div style="background:#111; border:1px solid #222; border-radius:4px; padding:10px; text-align:center;">
                        <div style="font-size:0.8em; color:gray; text-transform:uppercase; margin-bottom:5px; font-weight:bold;">{k.replace('_', ' ')}</div>
                        <div style="font-size:1.2em; font-weight:bold; color:{color_valor};">{v}</div>
                    </div>
                """
            html += """
                    </div>
                </div>
                
                <div style="background:#151515; padding:20px; border-radius:8px; border:1px solid #333;">
                    <h2 style="color:var(--accent); border-bottom:1px solid #444; padding-bottom:10px; margin-top:0; text-align:center; width:100%; display:block;">Realidad</h2>
                    <div style="display:flex; flex-direction:column; gap:15px; margin-top:15px; height:100%;">
            """
            if not premios_reales:
                html += """
                    <div style="flex:1; display:flex; flex-direction:column; justify-content:center; align-items:center; background:rgba(218, 165, 32, 0.1); border:1px dashed var(--gold); border-radius:8px; padding:20px; text-align:center;">
                        <div style="font-size:2em; margin-bottom:10px;">🔒</div>
                        <div style="color:var(--gold); font-weight:bold;">Aún no se conocen los premios oficiales</div>
                        <div style="color:gray; font-size:0.85em; margin-top:5px;">Se revelarán al finalizar el torneo.</div>
                    </div>
                """
            else:
                for k, v in premios_reales.items():
                    html += f"""
                        <div style="background:#111; border:1px solid #222; border-radius:4px; padding:10px; text-align:center;">
                            <div style="font-size:0.8em; color:gray; text-transform:uppercase; margin-bottom:5px; font-weight:bold;">{k.replace('_', ' ')}</div>
                            <div style="font-size:1.2em; font-weight:bold; color:var(--accent);">{v}</div>
                        </div>
                    """
            html += """
                    </div>
                </div>
            </div>
            """
            
        html += "</div>" # Cierre de protected-content-container
        html += "</div></body></html>"
        with open(dir_vistas / "pronostico_premios.html", 'w', encoding='utf-8') as f: f.write(html)

if __name__ == "__main__":
    print("=======================================================")
    print(" 🔮 [07B6] GENERANDO VISTAS DE PRONÓSTICOS (CÁPSULA) 🔮")
    print("=======================================================")
    generar_vistas_pronosticos()
    print("✅ Vistas de pronósticos generadas con éxito.")
