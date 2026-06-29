import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def calcular_posiciones_grupo_hasta_momento(partidos_jugados):
    tabla = {}
    for p in partidos_jugados:
        loc, vis = p['local'], p['visitante']
        if loc not in tabla: tabla[loc] = {"pts": 0, "dg": 0, "gf": 0, "nombre": loc}
        if vis not in tabla: tabla[vis] = {"pts": 0, "dg": 0, "gf": 0, "nombre": vis}

    for p in partidos_jugados:
        loc, vis = p['local'], p['visitante']
        gl = int(p.get('goles_local', 0)) if str(p.get('goles_local', '')).isdigit() else 0
        gv = int(p.get('goles_visitante', 0)) if str(p.get('goles_visitante', '')).isdigit() else 0
        
        tabla[loc]["dg"] += (gl - gv)
        tabla[vis]["dg"] += (gv - gl)
        tabla[loc]["gf"] += gl
        tabla[vis]["gf"] += gv
        
        if gl > gv: tabla[loc]["pts"] += 3
        elif gv > gl: tabla[vis]["pts"] += 3
        else:
            tabla[loc]["pts"] += 1
            tabla[vis]["pts"] += 1

    equipos = list(tabla.values())

    def ordenar_key(eq1, eq2):
        if p1 := (eq1["pts"] - eq2["pts"]): return p1
        enfrentamiento = [p for p in partidos_jugados if (p['local'] == eq1['nombre'] and p['visitante'] == eq2['nombre']) or (p['local'] == eq2['nombre'] and p['visitante'] == eq1['nombre'])]
        if enfrentamiento:
            p = enfrentamiento[0]
            gl = int(p.get('goles_local', 0)) if str(p.get('goles_local', '')).isdigit() else 0
            gv = int(p.get('goles_visitante', 0)) if str(p.get('goles_visitante', '')).isdigit() else 0
            if p['local'] == eq1['nombre']:
                if gl > gv: return 1
                if gv > gl: return -1
            else:
                if gv > gl: return 1
                if gl > gv: return -1
        if dg := (eq1["dg"] - eq2["dg"]): return dg
        if gf := (eq1["gf"] - eq2["gf"]): return gf
        return 0

    for i in range(len(equipos)):
        for j in range(i + 1, len(equipos)):
            if ordenar_key(equipos[i], equipos[j]) < 0:
                equipos[i], equipos[j] = equipos[j], equipos[i]

    return {eq["nombre"]: idx + 1 for idx, eq in enumerate(equipos)}

def get_fase_name(j_key):
    if "J" in j_key: return "Fase de Grupos"
    if "dieciseisavos" in j_key: return "Dieciseisavos"
    if "octavos" in j_key: return "Octavos de Final"
    if "cuartos" in j_key: return "Cuartos de Final"
    if "semifinales" in j_key: return "Semifinales"
    if "finales" in j_key: return "Final"
    return j_key

def generar_timeline():
    print("=======================================================")
    print(" 📈 [07B9] CRONOLOGÍA DE PUNTOS TOTALES (REAL TIME) 📈")
    print("=======================================================")

    jornadas_dict = html_utils.cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    realidad = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    global_sd = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "global_sd.json") or {}
    
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p.name for p in dir_participantes.iterdir() if p.is_dir()]
    
    historiales = {}
    for jug in jugadores:
        hist = html_utils.cargar_json(dir_participantes / jug / "estadisticas" / "historial_puntos.json") or {}
        historiales[jug] = hist

    dict_reales = {}
    for g, partidos in realidad.get("fase_grupos", {}).items():
        for p in partidos: dict_reales[f"{p['local']}_vs_{p['visitante']}"] = p
    for f, partidos in realidad.get("eliminatorias", {}).items():
        for p in partidos:
            if "id_partido" in p: dict_reales[f"ID_{p['id_partido']}"] = p

    settings = html_utils.cargar_json(ROOT_DIR / "config" / "settings.json") or {}
    pts_clasificado = settings.get("puntuaciones", {}).get("fase_grupos", {}).get("acierto_clasificado", 1)
    pts_posicion = settings.get("puntuaciones", {}).get("fase_grupos", {}).get("acierto_posicion_exacta", 2)

    frames = []
    current_scores = {jug: 0.0 for jug in jugadores}
    
    def clone_scores():
        return {k: v for k, v in current_scores.items()}

    frames.append({
        "type": "start", "jornada": "Pre-Torneo", "title": "ARRANQUE", "subtitle": "¡Comienza el Torneo!", "marker_text": "INICIO",
        "scores": clone_scores(), "diffs": {j: 0 for j in jugadores}, "exactos": {j: False for j in jugadores}
    })

    equipos_ya_caidos_sd = set()
    grupos_ya_procesados = set()
    partidos_acumulados_grupos = []

    for j_key, partidos in jornadas_dict.items():
        fase_actual = get_fase_name(j_key)
        partidos_jugados_en_jornada = 0
        partidos_ordenados = sorted(partidos, key=lambda x: dict_reales.get(f"ID_{x['id_partido']}" if "id_partido" in x else f"{x['local']}_vs_{x['visitante']}", {}).get("fecha", ""))
        
        for p in partidos_ordenados:
            if "id_partido" in p:
                clave_p = f"ID_{p['id_partido']}"
                clave_sec = clave_p
            else:
                clave_p = f"{p['local']}_vs_{p['visitante']}"
                clave_sec = f"{p['visitante']}_vs_{p['local']}"
                
            p_real = dict_reales.get(clave_p) or dict_reales.get(clave_sec)
            clave_activa = clave_p if dict_reales.get(clave_p) else clave_sec
            
            if not p_real or p_real.get("estado") not in ["finished", "jugandose"]:
                continue
            
            partidos_jugados_en_jornada += 1
            loc_r = p_real.get("local", "TBD")
            vis_r = p_real.get("visitante", "TBD")
            gl = p_real.get("goles_local", "-")
            gv = p_real.get("goles_visitante", "-")
            
            # 1. PUNTOS DEL PARTIDO NORMAL
            diffs = {}
            exactos = {}
            for jug in jugadores:
                info_p = historiales[jug].get("desglose_partidos", {}).get(clave_activa, {})
                pts = info_p.get("puntos_conseguidos", 0)
                current_scores[jug] += pts
                diffs[jug] = pts
                exactos[jug] = info_p.get("acierto_exacto", False)
            
            frames.append({
                "type": "match", "jornada": j_key, 
                "title": f"{loc_r[:3].upper()} {gl}-{gv} {vis_r[:3].upper()}", "subtitle": f"{loc_r} vs {vis_r}",
                "marker_text": f"{loc_r[:3].upper()} {gl}-{gv} {vis_r[:3].upper()}",
                "scores": clone_scores(), "diffs": diffs, "exactos": exactos
            })

            # 2. RESOLUCIÓN DE GRUPO (CUANDO LLEGA AL 6º PARTIDO JUGADO)
            if "J" in j_key:
                partidos_acumulados_grupos.append(p_real)
                grupo_actual = None
                for g_n, g_p in realidad.get("fase_grupos", {}).items():
                    if any(x['local'] == loc_r and x['visitante'] == vis_r for x in g_p):
                        grupo_actual = g_n
                        break
                
                if grupo_actual:
                    partidos_del_grupo = [x for x in partidos_acumulados_grupos if any(y['local'] == x['local'] for y in realidad["fase_grupos"][grupo_actual])]
                    
                    if len(partidos_del_grupo) == 6 and grupo_actual not in grupos_ya_procesados:
                        grupos_ya_procesados.add(grupo_actual)
                        
                        pos_finales_reales = html_utils.calcular_clasificacion_grupos(realidad.get("fase_grupos", {}))
                        pasan_reales_final = realidad.get("clasificados_a_dieciseisavos", [])
                        
                        # Extraer los 4 equipos del grupo y ordenarlos
                        equipos_grupo = set()
                        for pg in realidad["fase_grupos"][grupo_actual]:
                            equipos_grupo.add(pg["local"])
                            equipos_grupo.add(pg["visitante"])
                        
                        equipos_ordenados = sorted(list(equipos_grupo), key=lambda x: pos_finales_reales.get(x, 99))
                        
                        for eq_name in equipos_ordenados:
                            pos_act = pos_finales_reales.get(eq_name)
                            
                            diffs_pos = {}
                            exactos_pos = {}
                            for jug in jugadores:
                                pts_g = 0
                                es_exacto = False
                                
                                ruta_b = dir_participantes / jug / "pronosticos" / "grupos" / f"{jug}_base.json"
                                base_pred = html_utils.cargar_json(ruta_b) or {}
                                pasan_pred = base_pred.get("clasificados_a_dieciseisavos", [])
                                pos_pred = html_utils.calcular_clasificacion_grupos(base_pred.get("fase_grupos", {}))
                                
                                # REGLA ESTRICTA: Solo suman puntos (de clasificación o posición) SI pasan de fase de grupos
                                if eq_name in pasan_reales_final:
                                    if eq_name in pasan_pred:
                                        pts_g += pts_clasificado
                                    if pos_act == pos_pred.get(eq_name):
                                        pts_g += pts_posicion
                                        es_exacto = True
                                        
                                current_scores[jug] += pts_g
                                diffs_pos[jug] = pts_g
                                exactos_pos[jug] = es_exacto
                                
                            txt_pos = f"{pos_act}º Puesto" if pos_act != 1 else "1º de Grupo"
                            txt_repesca = ""
                            if pos_act == 3:
                                txt_repesca = " (Pasa en Repesca)" if eq_name in pasan_reales_final else " (Eliminado)"
                                
                            frames.append({
                                "type": "grupos_end", "jornada": j_key,
                                "title": f"🔒 RESOLUCIÓN {grupo_actual[-1]}", "subtitle": f"{eq_name} - {txt_pos}{txt_repesca}",
                                "marker_text": f"{eq_name[:3].upper()} {pos_act}º",
                                "scores": clone_scores(), "diffs": diffs_pos, "exactos": exactos_pos
                            })

                            # Si queda eliminado, aplicamos la Sorpresa/Decepción de inmediato
                            if eq_name not in pasan_reales_final:
                                if eq_name not in equipos_ya_caidos_sd and eq_name in global_sd:
                                    equipos_ya_caidos_sd.add(eq_name)
                                    diffs_sd = {}
                                    for jug in jugadores:
                                        predicciones_eq = global_sd[eq_name].get("predicciones", [])
                                        puntos_encontrados = 0
                                        for pred in predicciones_eq:
                                            if pred["jugador_id"] == jug:
                                                puntos_encontrados = pred.get("puntos", 0)
                                                break
                                        
                                        puntos_finales_sd = 10.0 if puntos_encontrados > 0 else 0.0
                                        current_scores[jug] += puntos_finales_sd
                                        diffs_sd[jug] = puntos_finales_sd
                                        
                                    frames.append({
                                        "type": "premios", "jornada": j_key,
                                        "title": f"ELIMINADOS EN GRUPOS", "subtitle": "Resolución de Sorpresas y Decepciones",
                                        "marker_text": eq_name.upper()[:10],
                                        "scores": clone_scores(), "diffs": diffs_sd, "exactos": {j: (diffs_sd[j] == 10.0) for j in jugadores}
                                    })

            # 3. DETECTAR ELIMINACIÓN OFICIAL EN ELIMINATORIAS (SORPRESAS / DECEPCIONES)
            if p_real.get("estado") == "finished" and "ID_" in clave_activa:
                ganador = p_real.get("pasa")
                perdedor = p_real["visitante"] if p_real["local"] == ganador else p_real["local"]
                
                if perdedor not in equipos_ya_caidos_sd and perdedor in global_sd:
                    equipos_ya_caidos_sd.add(perdedor)
                    
                    diffs_sd = {}
                    for jug in jugadores:
                        predicciones_eq = global_sd[perdedor].get("predicciones", [])
                        puntos_encontrados = 0
                        for pred in predicciones_eq:
                            if pred["jugador_id"] == jug:
                                puntos_encontrados = pred.get("puntos", 0)
                                break
                        
                        puntos_finales_sd = 10.0 if puntos_encontrados > 0 else 0.0
                        current_scores[jug] += puntos_finales_sd
                        diffs_sd[jug] = puntos_finales_sd
                        
                    frames.append({
                        "type": "premios", "jornada": j_key,
                        "title": f"ELIMINADOS EN {fase_actual.upper()}", "subtitle": "Resolución de Sorpresas y Decepciones",
                        "marker_text": perdedor.upper()[:10],
                        "scores": clone_scores(), "diffs": diffs_sd, "exactos": {j: (diffs_sd[j] == 10.0) for j in jugadores}
                    })

        # 4. BONOS FIN DE JORNADA
        if partidos_jugados_en_jornada > 0:
            diffs_bono = {}
            ganadores = []
            perdedores = []
            for jug in jugadores:
                bono = historiales[jug].get("desglose_jornadas", {}).get(j_key, {}).get("puntos_bono", 0)
                res = historiales[jug].get("desglose_jornadas", {}).get(j_key, {}).get("resultado", "")
                current_scores[jug] += bono
                diffs_bono[jug] = bono
                if res == "Ganador": ganadores.append(jug.replace('_', ' ').title())
                if res == "Perdedor": perdedores.append(jug.replace('_', ' ').title())
            
            if any(v != 0 for v in diffs_bono.values()):
                frames.append({
                    "type": "jornada", "jornada": j_key, 
                    "title": f"FIN {j_key.upper()}", "subtitle": f"👑 GANA: {', '.join(ganadores)} | 🐢 PIERDE: {', '.join(perdedores)}",
                    "marker_text": f"CIERRE {j_key.upper()}",
                    "scores": clone_scores(), "diffs": diffs_bono, "exactos": {j: False for j in jugadores}
                })

    # --- FOTOGRAMA FINAL: EL PODIO ---
    diffs_final = {}
    for jug in jugadores:
        reporte_06f = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06f_premios.json") or {}
        pts_podio = reporte_06f.get(jug, {}).get("puntos_podio", 0)
        pts_forms = reporte_06f.get(jug, {}).get("puntos_formulario", 0)
        
        total_extra = pts_podio + pts_forms
        current_scores[jug] += total_extra
        diffs_final[jug] = total_extra
        
    if any(v != 0 for v in diffs_final.values()):
        frames.append({
            "type": "premios", "jornada": "Fin Torneo", 
            "title": "👑 REY DEL MUNDIAL", "subtitle": "Suma de Campeón, Podio y Formularios Finales",
            "marker_text": "PODIO",
            "scores": clone_scores(), "diffs": diffs_final, "exactos": {j: False for j in jugadores}
        })

    frames_json = json.dumps(frames)
    altura_marcador = len(jugadores) * 46 + 20

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timeline | Animación RealTime</title>
    <link rel="stylesheet" href="theme.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ overflow-x: hidden; background-color: var(--bg-dark); }}
        #fullscreen-zone {{ background-color: var(--bg-dark); padding: 10px; min-height: 100vh; overflow-y: auto; box-sizing: border-box; }}
        .timeline-layout {{ display: flex; gap: 20px; margin-top: 10px; align-items: flex-start; height: 100%; }}
        @media (max-width: 1000px) {{ .timeline-layout {{ flex-direction: column; }} .chart-wrapper, .scoreboard-wrapper {{ width: 100% !important; }} }}
        
        .big-present-banner {{
            background: linear-gradient(180deg, #111, #1a1a1a); border: 2px solid var(--gold); border-radius: 12px;
            padding: 15px 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.8);
        }}
        .big-subtitle {{ font-size: 1.1em; color: #a9b7c6; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; }}
        .big-title {{ font-size: 3em; font-weight: 900; color: white; text-shadow: 0 0 15px rgba(255,255,255,0.3); margin: 0; line-height: 1.1; }}
        
        .chart-wrapper {{ flex: 7; background: #111; border: 1px solid #333; border-radius: 8px; padding: 15px; height: 650px; position: relative; }}
        .scoreboard-wrapper {{ flex: 3; background: #111; border: 1px solid #333; border-radius: 8px; padding: 15px; display: flex; flex-direction: column; }}
        #scoreboard {{ position: relative; min-height: {altura_marcador}px; width: 100%; }}
        
        .player-row {{
            position: absolute; left: 0; right: 0; height: 40px; background: #1a1a1a; border: 1px solid #333; border-radius: 6px;
            display: flex; align-items: center; padding: 0 10px; transition: top 0.4s ease-out, background 0.3s, opacity 0.3s; cursor: pointer; box-sizing: border-box;
        }}
        .player-row:hover {{ border-color: #666; background: #222; }}
        .p-color-dot {{ width: 10px; height: 10px; border-radius: 50%; margin-right: 10px; flex-shrink: 0; }}
        .p-name {{ flex: 1; font-weight: 900; color: #eee; text-transform: uppercase; font-size: 0.9em; }}
        .p-score {{ font-weight: 900; font-size: 1.1em; color: white; width: 45px; text-align: right; }}
        .p-diff {{ width: 45px; text-align: right; font-weight: 900; font-size: 1em; margin-left: 5px; }}

        .controls-container {{ background: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }}
        .btn-control {{ background: #252525; color: white; border: 1px solid #444; padding: 8px 15px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.2s; font-size: 0.9em; }}
        .btn-control:hover {{ background: var(--gold); color: black; border-color: var(--gold); }}
        .btn-play {{ background: var(--gold); color: black; border-color: var(--gold); min-width: 100px; }}
        #timeline-progress {{ flex: 1; min-width: 150px; margin: 0 10px; cursor: pointer; accent-color: var(--gold); height: 8px; }}
        .hint-text {{ text-align: center; color: #888; font-size: 0.8em; margin-top: 15px; font-style: italic; }}

        @media (max-width: 1000px) and (orientation: portrait) {{
            .timeline-layout {{ flex-direction: column; }}
            .chart-wrapper {{ height: 350px; }}
            .big-title {{ font-size: 1.8em !important; }}
        }}
        @media (max-width: 1000px) and (orientation: landscape) {{
            .timeline-layout {{ flex-direction: row; height: calc(100vh - 120px); }}
            .chart-wrapper {{ width: 65% !important; }}
            .scoreboard-wrapper {{ width: 35% !important; overflow-y: auto; }}
            .big-title {{ font-size: 1.4em !important; }}
        }}
    </style>
</head>
<body>
    {html_utils.get_sidebar_html("")}
    {html_utils.get_header_html("🎬 Carrera en Tiempo Real", "Cronología Absoluta del Campeonato", "")}
    
    <div id="fullscreen-zone">
        <div class="big-present-banner">
            <div class="big-subtitle" id="pm-subtitle">SINCRONIZANDO...</div>
            <div class="big-title" id="pm-title">RECOPILANDO HISTORIAL</div>
        </div>

        <div class="controls-container">
            <button class="btn-control" onclick="toggleFullScreen()">📺 Pantalla Completa</button>
            <button class="btn-control" onclick="seekRelative(-1)">⏮️ Ant.</button>
            <button class="btn-control btn-play" id="btn-play" onclick="togglePlay()">▶️ PLAY</button>
            <input type="range" id="timeline-progress" min="0" step="0.001" value="0" oninput="seekManual(this.value)">
            <button class="btn-control" onclick="seekRelative(1)">⏭️ Sig.</button>
            <select id="speed-selector" class="btn-control">
                <option value="0.25">0.25x</option>
                <option value="0.5">0.5x</option>
                <option value="1" selected>1x (Normal)</option>
                <option value="1.5">1.5x</option>
                <option value="2">2x (Rápido)</option>
                <option value="4">4x (Turbo)</option>
            </select>
        </div>

        <div class="timeline-layout">
            <div class="chart-wrapper">
                <canvas id="progressionChart"></canvas>
            </div>
            <div class="scoreboard-wrapper">
                <div id="scoreboard"></div>
                <div class="hint-text">💡 Filtra la gráfica haciendo clic sobre los nombres.</div>
            </div>
        </div>
    </div>

    <script>
        const frames = {frames_json};
        const jugadores = {json.dumps(jugadores)};
        const VIEW_RADIUS = 4;
        
        const palette = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#00FA9A", "#DC143C", "#00BFFF", "#FFD700", "#FF1493", "#00FF7F"];
        const playerColors = {{}};
        jugadores.forEach((j, i) => playerColors[j] = palette[i % palette.length]);

        let progress = 0; let isPlaying = false; let lastTime = 0; let animationReq;
        let smoothedYMax = 10; let smoothedYMin = 0;

        function toggleFullScreen() {{
            const zone = document.getElementById("fullscreen-zone");
            if (!document.fullscreenElement) {{
                zone.requestFullscreen().then(() => {{
                    if (screen.orientation && screen.orientation.lock) screen.orientation.lock('landscape').catch(() => {{}});
                }});
            }} else {{
                if (document.exitFullscreen) document.exitFullscreen();
            }}
        }}

        function togglePlayer(jug) {{
            const idx = progressionChart.data.datasets.findIndex(ds => ds.jugador_id === jug);
            const meta = progressionChart.getDatasetMeta(idx);
            meta.hidden = !meta.hidden;
            const row = document.getElementById("row-" + jug);
            row.style.opacity = meta.hidden ? "0.3" : "1";
            row.style.filter = meta.hidden ? "grayscale(100%)" : "none";
            progressionChart.update('none');
        }}

        const scoreboard = document.getElementById("scoreboard");
        jugadores.forEach(jug => {{
            const row = document.createElement("div");
            row.className = "player-row active-player"; row.id = "row-" + jug; row.onclick = () => togglePlayer(jug);
            row.innerHTML = `<div class="p-color-dot" style="background:${{playerColors[jug]}}"></div><div class="p-name">${{jug.replace('_',' ')}}</div><div class="p-score" id="score-${{jug}}">0.0</div><div class="p-diff" id="diff-${{jug}}">+0.0</div>`;
            scoreboard.appendChild(row);
        }});

        const backgroundPlugin = {{
            id: 'backgroundMarks',
            beforeDraw(chart) {{
                const ctx = chart.ctx; const xAxis = chart.scales.x; const yAxis = chart.scales.y;
                
                const uniqueJornadas = [...new Set(frames.map(f => f.jornada))];
                const minIdx = Math.max(0, Math.floor(xAxis.min));
                const maxIdx = Math.min(frames.length - 1, Math.ceil(xAxis.max));

                for(let i = minIdx; i <= maxIdx; i++) {{
                    const f = frames[i];
                    const jIndex = uniqueJornadas.indexOf(f.jornada);
                    const bgColor = (jIndex % 2 === 0) ? 'rgba(17, 17, 17, 1)' : 'rgba(26, 29, 36, 1)'; 

                    const xStart = xAxis.getPixelForValue(i - 0.5);
                    const xEnd = xAxis.getPixelForValue(i + 0.5);
                    
                    ctx.fillStyle = bgColor;
                    ctx.fillRect(xStart, yAxis.top, xEnd - xStart, yAxis.bottom - yAxis.top);
                }}

                const currentFrame = frames[Math.min(frames.length - 1, Math.floor(progress))];
                const currentJornada = currentFrame.jornada || "";
                if (currentJornada) {{
                    ctx.save();
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
                    const isMobile = window.innerWidth <= 1000;
                    ctx.font = isMobile ? '900 30px Arial' : '900 60px Arial';
                    ctx.textAlign = 'center';
                    
                    let jName = currentJornada.toUpperCase();
                    if (jName.startsWith("J")) jName = jName.replace("J", "JORNADA ");
                    else jName = jName.replace("DIECISEISAVOS", "1/16");
                    
                    ctx.fillText(jName, (xAxis.left + xAxis.right) / 2, yAxis.top + (isMobile ? 40 : 60));
                    ctx.restore();
                }}

                frames.forEach((f, index) => {{
                    if (index >= xAxis.min && index <= xAxis.max) {{
                        const x = xAxis.getPixelForValue(index);
                        ctx.save();
                        
                        const markerText = f.marker_text || f.title;

                        if (f.type === 'match') {{
                            // Línea de partido más gruesa y visible
                            ctx.beginPath(); ctx.moveTo(x, yAxis.top); ctx.lineTo(x, yAxis.bottom); ctx.lineWidth = 1;
                            ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.stroke();
                            
                            const isMobile = window.innerWidth <= 1000;
                            
                            // Texto en blanco puro (opacity 1) y algo más grande
                            ctx.fillStyle = 'rgba(255, 255, 255, 1)'; 
                            ctx.textAlign = 'center'; 
                            ctx.font = isMobile ? 'bold 10px Arial' : 'bold 12px Arial';
                            
                            const zigzagOffset = (index % 3) * (isMobile ? 15 : 22);
                            ctx.fillText(markerText, x, yAxis.bottom - 12 - zigzagOffset);
                            
                        }} else if (f.type !== 'start') {{
                            ctx.beginPath(); ctx.moveTo(x, yAxis.top + 20); ctx.lineTo(x, yAxis.bottom); ctx.lineWidth = 2;
                            
                            let lineColor = 'rgba(218, 165, 32, 0.4)';
                            let textColor = 'rgba(218, 165, 32, 0.9)';
                            
                            if (f.type === 'premios') {{
                                lineColor = 'rgba(239, 68, 68, 0.4)'; 
                                textColor = 'rgba(239, 68, 68, 0.9)';
                            }} else if (f.type === 'grupos_end') {{
                                lineColor = 'rgba(74, 222, 128, 0.4)'; 
                                textColor = 'rgba(74, 222, 128, 0.9)';
                            }}
                            
                            ctx.strokeStyle = lineColor; ctx.setLineDash([5,5]); ctx.stroke();
                            ctx.fillStyle = textColor; ctx.textAlign = 'center'; ctx.font = 'bold 11px Arial';
                            ctx.fillText(markerText, x, yAxis.top + 12);
                        }}
                        ctx.restore();
                    }}
                }});
            }}
        }};

        const drawHeadPlugin = {{
            id: 'drawHeads',
            afterDatasetsDraw(chart) {{
                const ctx = chart.ctx; const baseIdx = Math.floor(progress); const nextIdx = Math.min(baseIdx + 1, frames.length - 1);
                let points = [];
                chart.data.datasets.forEach((ds, i) => {{
                    const meta = chart.getDatasetMeta(i);
                    if (!meta.hidden && meta.data.length > 0) {{
                        const lastPoint = meta.data[meta.data.length - 1];
                        points.push({{ dsIndex: i, jug: ds.jugador_id, actualY: lastPoint.y, drawY: lastPoint.y, x: lastPoint.x, color: ds.borderColor }});
                    }}
                }});
                points.sort((a, b) => a.actualY - b.actualY);
                const LABEL_HEIGHT = 26;
                for(let iter=0; iter<10; iter++){{
                    for(let j=0; j<points.length - 1; j++){{
                        let p1 = points[j]; let p2 = points[j+1];
                        if ((p2.drawY - p1.drawY) < LABEL_HEIGHT) {{
                            let overlap = LABEL_HEIGHT - (p2.drawY - p1.drawY);
                            p1.drawY -= overlap / 2; p2.drawY += overlap / 2;
                        }}
                    }}
                }}
                points.forEach(p => {{
                    if (Math.abs(p.drawY - p.actualY) > 4) {{
                        ctx.save(); ctx.beginPath(); ctx.moveTo(p.x, p.actualY); ctx.lineTo(p.x + 10, p.drawY);
                        ctx.strokeStyle = p.color; ctx.lineWidth = 1; ctx.setLineDash([2,2]); ctx.stroke(); ctx.restore();
                    }}
                    const diff = frames[nextIdx].diffs[p.jug] || 0;
                    const isExact = frames[nextIdx].exactos && frames[nextIdx].exactos[p.jug];
                    let dTxt = "+0.0", dColor = "#666";
                    
                    if(diff > 0) {{
                        dTxt = "+" + diff.toFixed(1);
                        dColor = (diff === 10.0 || isExact) ? "#4ade80" : "#3b82f6";
                    }} else if (diff < 0) {{ dTxt = diff.toFixed(1); dColor = "#ef4444"; }}
                    
                    ctx.save(); ctx.textAlign = 'left';
                    const valNum = chart.scales.y.getValueForPixel(p.actualY);
                    ctx.font = 'bold 11px Arial'; ctx.fillStyle = p.color;
                    ctx.fillText(`${{p.jug.toUpperCase().slice(0,4)}} ${{valNum.toFixed(1)}}`, p.x + 12, p.drawY - 4);
                    ctx.fillStyle = dColor; ctx.fillText(dTxt, p.x + 12, p.drawY + 8); ctx.restore();
                }});
            }}
        }};

        const datasetsInit = jugadores.map(jug => ({{
            jugador_id: jug, label: jug.replace('_',' ').toUpperCase(), data: [],
            borderColor: playerColors[jug], backgroundColor: playerColors[jug], borderWidth: 2.5, pointRadius: 0, tension: 0.1
        }}));

        const ctx = document.getElementById('progressionChart').getContext('2d');
        const progressionChart = new Chart(ctx, {{
            type: 'line', data: {{ datasets: datasetsInit }},
            options: {{
                responsive: true, maintainAspectRatio: false, animation: false,
                layout: {{ padding: {{ right: 65, bottom: 20 }} }},
                scales: {{
                    x: {{ type: 'linear', grid: {{ display: false }}, ticks: {{ display: false }} }},
                    y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#aaa', font: {{ weight:'bold', size:10 }} }}, suggestedMin: 0 }}
                }}
            }},
            plugins: [backgroundPlugin, drawHeadPlugin]
        }});

        function renderAtProgress(p) {{
            const baseIdx = Math.floor(p); const nextIdx = Math.min(baseIdx + 1, frames.length - 1); const fraction = p - baseIdx;
            const targetFrame = frames[nextIdx];
            document.getElementById("pm-title").innerText = targetFrame.title;
            document.getElementById("pm-subtitle").innerText = targetFrame.subtitle;

            progressionChart.options.scales.x.min = p - VIEW_RADIUS;
            progressionChart.options.scales.x.max = p + VIEW_RADIUS;

            const currentScores = {{}}; let maxV = 5, minV = Infinity;

            progressionChart.data.datasets.forEach(ds => {{
                const jug = ds.jugador_id; let dataPoints = [];
                for (let j = 0; j <= baseIdx; j++) dataPoints.push({{ x: j, y: frames[j].scores[jug] }});
                if (fraction > 0 && nextIdx > baseIdx) {{
                    const currentY = frames[baseIdx].scores[jug] + (frames[nextIdx].scores[jug] - frames[baseIdx].scores[jug]) * fraction;
                    dataPoints.push({{ x: p, y: currentY }}); currentScores[jug] = currentY;
                }} else {{ currentScores[jug] = frames[baseIdx].scores[jug]; }}
                ds.data = dataPoints;
                
                const rowObj = document.getElementById("row-" + jug);
                if (rowObj.style.opacity !== "0.3") {{
                    if (currentScores[jug] > maxV) maxV = currentScores[jug];
                    if (currentScores[jug] < minV) minV = currentScores[jug];
                }}
            }});
            if (minV === Infinity) minV = 0;

            smoothedYMax += ((maxV + Math.max(5, (maxV - minV)*0.15)) - smoothedYMax) * 0.08;
            smoothedYMin += ((Math.max(0, minV - 5)) - smoothedYMin) * 0.08;
            progressionChart.options.scales.y.max = smoothedYMax;
            progressionChart.options.scales.y.min = smoothedYMin;
            progressionChart.update();

            const sortedPlayers = [...jugadores].sort((a, b) => currentScores[b] - currentScores[a]);
            sortedPlayers.forEach((jug, rank) => {{
                const row = document.getElementById("row-" + jug); row.style.top = (rank * 46 + 5) + "px";
                row.style.borderColor = rank === 0 ? "var(--gold)" : "#333";
                document.getElementById("score-" + jug).innerText = currentScores[jug].toFixed(1);
                
                const diffEl = document.getElementById("diff-" + jug); const pts = targetFrame.diffs[jug] || 0;
                if (pts > 0) {{
                    diffEl.innerText = "+" + pts.toFixed(1);
                    diffEl.style.color = (pts === 10.0 || (targetFrame.exactos && targetFrame.exactos[jug])) ? "#4ade80" : "#3b82f6";
                }} else if (pts < 0) {{ diffEl.innerText = pts.toFixed(1); diffEl.style.color = "#ef4444"; }}
                else {{ diffEl.innerText = "+0.0"; diffEl.style.color = "#666"; }}
            }});
        }}

        function animateLoop(time) {{
            if (!lastTime) lastTime = time; const delta = time - lastTime; lastTime = time;
            if (isPlaying) {{
                const speedMult = parseFloat(document.getElementById("speed-selector").value);
                const nextIdx = Math.min(Math.floor(progress) + 1, frames.length - 1);
                
                // --- VELOCIDAD RETOCADA ---
                // Matches normales = 0.00045, Hitos/Pausas = 0.00028 (antes 0.00015, ahora son mucho más dinámicos)
                const speedFactor = frames[nextIdx].type !== 'match' ? 0.00028 : 0.00045;
                
                progress += (delta * speedFactor) * speedMult;
                if (progress >= frames.length - 1) {{ progress = frames.length - 1; isPlaying = false; document.getElementById("btn-play").innerText = "▶️ PLAY"; }}
                document.getElementById("timeline-progress").value = progress; renderAtProgress(progress);
            }}
            animationReq = requestAnimationFrame(animateLoop);
        }}

        function togglePlay() {{
            isPlaying = !isPlaying; const btn = document.getElementById("btn-play");
            if (isPlaying) {{ if (progress >= frames.length - 1) progress = 0; lastTime = performance.now(); btn.innerText = "⏸️ PAUSA"; }}
            else btn.innerText = "▶️ PLAY";
        }}
        function seekManual(val) {{ progress = parseFloat(val); renderAtProgress(progress); }}
        function seekRelative(step) {{ progress = Math.max(0, Math.min(frames.length - 1, progress + step)); document.getElementById("timeline-progress").value = progress; renderAtProgress(progress); }}
        window.addEventListener('resize', () => {{ if (!isPlaying) renderAtProgress(progress); }});
        renderAtProgress(0); animationReq = requestAnimationFrame(animateLoop);
    </script>
</body>
</html>
    """
    
    ruta_salida = ROOT_DIR / "timeline.html"
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"✅ ¡Película RealTime con Fondos Dinámicos generada en: {ruta_salida}")

if __name__ == "__main__":
    generar_timeline()