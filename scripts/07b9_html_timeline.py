import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def generar_timeline():
    print("=======================================================")
    print(" 🚀 [07B9] GENERANDO MOTOR GRÁFICO (CÁMARA INTELIGENTE) 🚀")
    print("=======================================================")

    jornadas_dict = html_utils.cargar_json(ROOT_DIR / "config" / "jornadas.json") or {}
    realidad = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    
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

    frames = []
    current_scores = {jug: 0.0 for jug in jugadores}
    
    def clone_scores():
        return {k: v for k, v in current_scores.items()}

    frames.append({
        "type": "start",
        "title": "ARRANQUE",
        "subtitle": "¡Comienza el Mundial!",
        "scores": clone_scores(),
        "diffs": {j: 0 for j in jugadores},
        "exactos": {j: False for j in jugadores}
    })

    for j_key, partidos in jornadas_dict.items():
        partidos_jugados_en_jornada = 0
        partidos_ordenados = sorted(partidos, key=lambda x: dict_reales.get(f"ID_{x['id_partido']}" if "id_partido" in x else f"{x['local']}_vs_{x['visitante']}", {}).get("fecha", ""))
        
        for p in partidos_ordenados:
            clave = f"ID_{p['id_partido']}" if "id_partido" in p else f"{p['local']}_vs_{p['visitante']}"
            p_real = dict_reales.get(clave, {})
            
            if p_real.get("estado") != "finished":
                continue
            
            partidos_jugados_en_jornada += 1
            
            loc_r = p_real.get("local", "TBD")
            vis_r = p_real.get("visitante", "TBD")
            gl = p_real.get("goles_local", "-")
            gv = p_real.get("goles_visitante", "-")
            
            diffs = {}
            exactos = {}
            for jug in jugadores:
                info_p = historiales[jug].get("desglose_partidos", {}).get(clave, {})
                pts = info_p.get("puntos_conseguidos", 0)
                is_exact = info_p.get("acierto_exacto", False)
                
                current_scores[jug] += pts
                diffs[jug] = pts
                exactos[jug] = is_exact
            
            frames.append({
                "type": "match",
                "title": f"{loc_r[:3].upper()} {gl}-{gv} {vis_r[:3].upper()}", 
                "subtitle": f"{loc_r} vs {vis_r}",
                "scores": clone_scores(),
                "diffs": diffs,
                "exactos": exactos
            })
        
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
                    "type": "jornada",
                    "title": f"FIN {j_key.upper()}",
                    "subtitle": f"Ganador: {', '.join(ganadores)} | Perdedor: {', '.join(perdedores)}",
                    "scores": clone_scores(),
                    "diffs": diffs_bono,
                    "exactos": {j: False for j in jugadores}
                })
        
        if j_key == "J3.2" and partidos_jugados_en_jornada > 0:
            diffs_grupos = {}
            for jug in jugadores:
                pts_g = historiales[jug].get("resolucion_fase_grupos", {}).get("puntos_conseguidos", 0)
                current_scores[jug] += pts_g
                diffs_grupos[jug] = pts_g
            if any(v != 0 for v in diffs_grupos.values()):
                frames.append({
                    "type": "grupos_end",
                    "title": "FIN GRUPOS",
                    "subtitle": "Resolución Pases y Posiciones",
                    "scores": clone_scores(),
                    "diffs": diffs_grupos,
                    "exactos": {j: False for j in jugadores}
                })

    diffs_final = {}
    for jug in jugadores:
        sd_details = historiales[jug].get("premios_finales", {}).get("formularios", {}).get("detalles", {})
        pts_sd = sd_details.get("sorpresa", 0) + sd_details.get("decepcion", 0)
        reporte_06f = html_utils.cargar_json(ROOT_DIR / "data" / "resultados" / "reporte_06f_premios.json") or {}
        pts_podio = reporte_06f.get(jug, {}).get("puntos_podio", 0)
        pts_forms = reporte_06f.get(jug, {}).get("puntos_formulario", 0)
        
        total_extra = pts_sd + pts_podio + pts_forms
        current_scores[jug] += total_extra
        diffs_final[jug] = total_extra
        
    if any(v != 0 for v in diffs_final.values()):
        frames.append({
            "type": "premios",
            "title": "PREMIOS FINALES",
            "subtitle": "Sorpresas, Decepciones y Campeones",
            "scores": clone_scores(),
            "diffs": diffs_final,
            "exactos": {j: False for j in jugadores}
        })

    frames_json = json.dumps(frames)
    altura_marcador = max(400, len(jugadores) * 55)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timeline | Anti-Colisión y Cámara Dinámica</title>
    <link rel="stylesheet" href="theme.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ overflow-x: hidden; background-color: var(--bg-dark); }}
        
        /* Contenedor principal que se hará pantalla completa */
        #fullscreen-zone {{
            background-color: var(--bg-dark);
            padding: 10px;
            min-height: 100vh;
        }}
        
        .timeline-layout {{ display: flex; gap: 20px; margin-top: 10px; align-items: flex-start; height: 100%; }}
        @media (max-width: 1000px) {{ .timeline-layout {{ flex-direction: column; }} .chart-wrapper, .scoreboard-wrapper {{ width: 100% !important; }} }}
        
        .big-present-banner {{
            background: linear-gradient(180deg, #111, #1a1a1a);
            border: 2px solid var(--gold);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8), inset 0 0 20px rgba(218, 165, 32, 0.2);
            position: relative;
            overflow: hidden;
        }}
        .big-subtitle {{ font-size: 1.2em; color: #a9b7c6; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; }}
        .big-title {{ font-size: 3.5em; font-weight: 900; color: white; text-shadow: 0 0 15px rgba(255,255,255,0.3); margin: 0; line-height: 1.1; }}
        
        .chart-wrapper {{
            flex: 7; background: #111; border: 1px solid #333; border-radius: 8px;
            padding: 15px; box-shadow: inset 0 0 15px rgba(0,0,0,0.5); height: 750px;
        }}
        
        .scoreboard-wrapper {{
            flex: 3; background: #111; border: 1px solid #333; border-radius: 8px;
            padding: 15px; position: relative; height: {altura_marcador}px;
            overflow: hidden; box-shadow: inset 0 0 15px rgba(0,0,0,0.5);
        }}
        
        .player-row {{
            position: absolute; left: 15px; right: 15px; height: 45px;
            background: #1a1a1a; border: 1px solid #333; border-radius: 6px;
            display: flex; align-items: center; padding: 0 15px;
            transition: top 0.4s ease-out, background 0.3s, opacity 0.3s, filter 0.3s;
            cursor: pointer;
        }}
        .player-row:hover {{ border-color: #666; background: #222; }}
        
        .p-color-dot {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 15px; box-shadow: 0 0 5px rgba(255,255,255,0.3); }}
        .p-name {{ flex: 1; font-weight: 900; color: #eee; text-transform: uppercase; font-size: 0.95em; }}
        .p-score {{ font-weight: 900; font-size: 1.2em; color: white; width: 60px; text-align: right; }}
        .p-diff {{ width: 50px; text-align: right; font-weight: 900; font-size: 1.1em; margin-left: 10px; }}

        .controls-container {{
            background: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #333;
            margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
        }}
        .btn-control {{ background: #252525; color: white; border: 1px solid #444; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; transition: 0.2s; }}
        .btn-control:hover {{ background: var(--gold); color: black; border-color: var(--gold); }}
        .btn-play {{ background: var(--gold); color: black; border-color: var(--gold); min-width: 120px; font-size: 1.1em; }}
        .btn-play:hover {{ background: #b8860b; }}
        .btn-fs {{ background: #2b5876; color: white; border-color: #1a2a6c; }}
        .btn-fs:hover {{ background: #1a2a6c; border-color: var(--gold); color: white; }}

        #timeline-progress {{ flex: 1; min-width: 200px; margin: 0 10px; cursor: pointer; accent-color: var(--gold); height: 8px; }}
        .hint-text {{ text-align: center; color: #888; font-size: 0.85em; margin-top: 5px; font-style: italic; }}
    </style>
</head>
<body>
    {html_utils.get_sidebar_html("")}
    {html_utils.get_header_html("🎬 Rendering en Tiempo Real", "Cámara Inteligente y FullScreen Dinámico", "")}
    
    <div id="fullscreen-zone">
        <div class="big-present-banner">
            <div class="big-subtitle" id="pm-subtitle">PREPARANDO TORNEO...</div>
            <div class="big-title" id="pm-title">CARGANDO DATOS</div>
        </div>

        <div class="controls-container">
            <button class="btn-control btn-fs" onclick="toggleFullScreen()">📺 Pantalla Completa</button>
            <button class="btn-control" onclick="seekRelative(-1)">⏮️ Ant.</button>
            <button class="btn-control btn-play" id="btn-play" onclick="togglePlay()">▶️ PLAY</button>
            <input type="range" id="timeline-progress" min="0" step="0.001" value="0" oninput="seekManual(this.value)">
            <button class="btn-control" onclick="seekRelative(1)">⏭️ Sig.</button>
            <select id="speed-selector" class="btn-control">
                <option value="0.25">0.25x (Lento)</option>
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
                <div class="hint-text">💡 Clic en un jugador para ocultar/mostrar su línea.</div>
            </div>
        </div>
    </div>

    <script>
        const frames = {frames_json};
        const jugadores = {json.dumps(jugadores)};
        
        const VIEW_RADIUS = 4; // 4 atrás, 4 adelante
        
        const palette = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#00FA9A", "#DC143C", "#00BFFF", "#FFD700", "#FF1493", "#00FF7F"];
        const playerColors = {{}};
        jugadores.forEach((j, i) => playerColors[j] = palette[i % palette.length]);

        let progress = 0; 
        let isPlaying = false;
        let lastTime = 0;
        let animationReq;
        
        // CÁMARA DINÁMICA (Suelo y Techo Suavizados)
        let smoothedYMax = 10;
        let smoothedYMin = 0;

        // PANTALLA COMPLETA
        function toggleFullScreen() {{
            const zone = document.getElementById("fullscreen-zone");
            if (!document.fullscreenElement) {{
                zone.requestFullscreen().then(() => {{
                    // Si estamos en móvil, forzar giro a horizontal
                    if (screen.orientation && screen.orientation.lock) {{
                        screen.orientation.lock('landscape').catch((e) => console.log("Giro automático no soportado:", e));
                    }}
                }}).catch(err => {{
                    console.log(`Error al abrir pantalla completa: ${{err.message}}`);
                }});
            }} else {{
                if (document.exitFullscreen) document.exitFullscreen();
            }}
        }}

        // TOGGLE JUGADORES
        function togglePlayer(jug) {{
            const dsIndex = progressionChart.data.datasets.findIndex(ds => ds.jugador_id === jug);
            const meta = progressionChart.getDatasetMeta(dsIndex);
            
            meta.hidden = !meta.hidden;
            
            const row = document.getElementById("row-" + jug);
            if (meta.hidden) {{
                row.style.opacity = "0.3";
                row.style.filter = "grayscale(100%)";
                row.classList.remove("active-player");
            }} else {{
                row.style.opacity = "1";
                row.style.filter = "none";
                row.classList.add("active-player");
            }}
            progressionChart.update('none'); 
        }}

        const scoreboard = document.getElementById("scoreboard");
        jugadores.forEach(jug => {{
            const row = document.createElement("div");
            row.className = "player-row active-player"; 
            row.id = "row-" + jug;
            row.onclick = () => togglePlayer(jug);
            
            row.innerHTML = `
                <div class="p-color-dot" style="background: ${{playerColors[jug]}}"></div>
                <div class="p-name">${{jug.replace('_', ' ')}}</div>
                <div class="p-score" id="score-${{jug}}">0.0</div>
                <div class="p-diff" id="diff-${{jug}}">+0.0</div>
            `;
            scoreboard.appendChild(row);
        }});

        // --- PLUGIN 1: MARCAS DE FONDO CON ZIG-ZAG ---
        const backgroundPlugin = {{
            id: 'backgroundMarks',
            beforeDraw(chart) {{
                const ctx = chart.ctx;
                const xAxis = chart.scales.x;
                const yAxis = chart.scales.y;
                
                frames.forEach((f, index) => {{
                    if (index >= xAxis.min && index <= xAxis.max) {{
                        const x = xAxis.getPixelForValue(index);
                        ctx.save();
                        
                        if (f.type === 'match') {{
                            // Línea fina del partido
                            ctx.beginPath();
                            ctx.moveTo(x, yAxis.top);
                            ctx.lineTo(x, yAxis.bottom);
                            ctx.lineWidth = 1;
                            ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
                            ctx.stroke();
                            
                            // Textos de partidos horizontales en blanco
                            // Para evitar superposiciones, alternamos su altura en Zig-Zag
                            const zigzagOffset = (index % 3) * 20; // Crea 3 niveles distintos
                            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                            ctx.textAlign = 'center';
                            ctx.font = 'bold 10px Arial';
                            ctx.fillText(f.title, x, yAxis.bottom - 20 - zigzagOffset);
                            
                        }} else if (f.type !== 'start') {{
                            // Hitos
                            ctx.beginPath();
                            ctx.moveTo(x, yAxis.top + 20);
                            ctx.lineTo(x, yAxis.bottom);
                            ctx.lineWidth = 2;
                            ctx.strokeStyle = 'rgba(218, 165, 32, 0.4)';
                            ctx.setLineDash([5, 5]);
                            ctx.stroke();
                            
                            ctx.fillStyle = 'rgba(218, 165, 32, 0.9)';
                            ctx.textAlign = 'center';
                            ctx.font = 'bold 12px Arial';
                            ctx.fillText(f.title, x, yAxis.top + 10);
                        }}
                        ctx.restore();
                    }}
                }});
            }}
        }};

        // --- PLUGIN 2: TEXTOS Y ANTI-COLISIÓN ---
        const drawHeadPlugin = {{
            id: 'drawHeads',
            afterDatasetsDraw(chart) {{
                const ctx = chart.ctx;
                const baseIdx = Math.floor(progress);
                const nextIdx = Math.min(baseIdx + 1, frames.length - 1);
                
                let points = [];
                chart.data.datasets.forEach((ds, i) => {{
                    const meta = chart.getDatasetMeta(i);
                    if (!meta.hidden && meta.data.length > 0) {{
                        const lastPoint = meta.data[meta.data.length - 1];
                        points.push({{
                            dsIndex: i,
                            jug: ds.jugador_id,
                            actualY: lastPoint.y,
                            drawY: lastPoint.y,
                            x: lastPoint.x,
                            color: ds.borderColor
                        }});
                    }}
                }});

                // Algoritmo Anti-Colisión (Stacking)
                points.sort((a, b) => a.actualY - b.actualY);
                const LABEL_HEIGHT = 30; 
                for(let iter=0; iter<10; iter++){{
                    for(let j=0; j<points.length - 1; j++){{
                        let p1 = points[j];
                        let p2 = points[j+1];
                        let diff = p2.drawY - p1.drawY;
                        if (diff < LABEL_HEIGHT) {{
                            let overlap = LABEL_HEIGHT - diff;
                            p1.drawY -= overlap / 2;
                            p2.drawY += overlap / 2;
                        }}
                    }}
                }}

                points.forEach(p => {{
                    if (Math.abs(p.drawY - p.actualY) > 5) {{
                        ctx.save();
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.actualY);
                        ctx.lineTo(p.x + 10, p.drawY);
                        ctx.strokeStyle = p.color;
                        ctx.lineWidth = 1;
                        ctx.setLineDash([2, 2]);
                        ctx.stroke();
                        ctx.restore();
                    }}

                    const diff = frames[nextIdx].diffs[p.jug] || 0;
                    const isExact = frames[nextIdx].exactos && frames[nextIdx].exactos[p.jug];
                    let dTxt = "+0.0";
                    let dColor = "#666";
                    if(diff > 0) {{
                        dTxt = "+" + diff.toFixed(1);
                        dColor = isExact ? "#4ade80" : "#3b82f6";
                    }} else if (diff < 0) {{
                        dTxt = diff.toFixed(1);
                        dColor = "#ef4444";
                    }}

                    ctx.save();
                    ctx.textAlign = 'left';
                    const valNum = chart.scales.y.getValueForPixel(p.actualY);
                    
                    ctx.font = 'bold 12px Arial';
                    ctx.fillStyle = p.color;
                    ctx.fillText(`${{p.jug.toUpperCase()}} ${{valNum.toFixed(1)}}`, p.x + 12, p.drawY - 4);
                    
                    ctx.font = 'bold 12px Arial';
                    ctx.fillStyle = dColor;
                    ctx.fillText(dTxt, p.x + 12, p.drawY + 10);
                    ctx.restore();
                }});
            }}
        }};

        const datasetsInit = jugadores.map(jug => ({{
            jugador_id: jug,
            label: jug.replace('_', ' ').toUpperCase(),
            data: [], 
            borderColor: playerColors[jug],
            backgroundColor: playerColors[jug],
            borderWidth: 3,
            pointRadius: 0, 
            tension: 0.1
        }}));

        const ctx = document.getElementById('progressionChart').getContext('2d');
        const progressionChart = new Chart(ctx, {{
            type: 'line',
            data: {{ datasets: datasetsInit }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                animation: false, 
                interaction: {{ mode: 'nearest', intersect: false }},
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{ enabled: false }}
                }},
                layout: {{
                    padding: {{ right: 80, bottom: 20 }} // Espacio para textos extra
                }},
                scales: {{
                    x: {{
                        type: 'linear',
                        grid: {{ display: false }},
                        ticks: {{ display: false }} 
                    }},
                    y: {{
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        ticks: {{ color: '#aaa', font: {{ weight: 'bold', size: 12 }} }},
                        suggestedMin: 0
                    }}
                }}
            }},
            plugins: [backgroundPlugin, drawHeadPlugin]
        }});

        document.getElementById("timeline-progress").max = frames.length - 1;

        // --- CEREBRO: CÁMARA Y MARCADOR ---
        function renderAtProgress(p) {{
            const baseIdx = Math.floor(p);
            const nextIdx = Math.min(baseIdx + 1, frames.length - 1);
            const fraction = p - baseIdx;
            
            const targetFrame = frames[nextIdx];
            document.getElementById("pm-title").innerText = targetFrame.title;
            document.getElementById("pm-subtitle").innerText = targetFrame.subtitle;

            progressionChart.options.scales.x.min = p - VIEW_RADIUS;
            progressionChart.options.scales.x.max = p + VIEW_RADIUS;

            const currentScores = {{}};
            let maxVisibleScore = 5;
            let minVisibleScore = Infinity;

            progressionChart.data.datasets.forEach(ds => {{
                const jug = ds.jugador_id;
                let dataPoints = [];
                
                for (let j = 0; j <= baseIdx; j++) {{
                    dataPoints.push({{ x: j, y: frames[j].scores[jug] }});
                }}
                
                if (fraction > 0 && nextIdx > baseIdx) {{
                    const y0 = frames[baseIdx].scores[jug];
                    const y1 = frames[nextIdx].scores[jug];
                    const currentY = y0 + (y1 - y0) * fraction;
                    dataPoints.push({{ x: p, y: currentY }});
                    currentScores[jug] = currentY;
                }} else {{
                    currentScores[jug] = frames[baseIdx].scores[jug];
                }}
                
                ds.data = dataPoints;

                const rowObj = document.getElementById("row-" + jug);
                if (rowObj.classList.contains("active-player")) {{
                    if (currentScores[jug] > maxVisibleScore) maxVisibleScore = currentScores[jug];
                    if (currentScores[jug] < minVisibleScore) minVisibleScore = currentScores[jug];
                }}
            }});

            if (minVisibleScore === Infinity) minVisibleScore = 0;

            // Escala Y Dinámica (Suelo y Techo Suaves)
            const targetYMax = maxVisibleScore + Math.max(5, (maxVisibleScore - minVisibleScore) * 0.15); 
            smoothedYMax += (targetYMax - smoothedYMax) * 0.08; 
            progressionChart.options.scales.y.max = smoothedYMax;

            // El margen inferior sube dinámicamente persiguiendo al último
            const targetYMin = Math.max(0, minVisibleScore - 5); 
            smoothedYMin += (targetYMin - smoothedYMin) * 0.08;
            progressionChart.options.scales.y.min = smoothedYMin;

            progressionChart.update();

            const sortedPlayers = [...jugadores].sort((a, b) => currentScores[b] - currentScores[a]);
            sortedPlayers.forEach((jug, rank) => {{
                const row = document.getElementById("row-" + jug);
                row.style.top = (rank * 55 + 10) + "px"; 
                
                if(rank === 0) {{
                    row.style.borderColor = "var(--gold)";
                    row.style.boxShadow = "0 0 10px rgba(218, 165, 32, 0.2)";
                }} else {{
                    row.style.borderColor = "#333";
                    row.style.boxShadow = "none";
                }}
                
                document.getElementById("score-" + jug).innerText = currentScores[jug].toFixed(1);
                
                const diffEl = document.getElementById("diff-" + jug);
                const pts = frames[nextIdx].diffs[jug] || 0;
                const isExact = frames[nextIdx].exactos && frames[nextIdx].exactos[jug];
                
                if (pts > 0) {{
                    diffEl.innerText = "+" + pts.toFixed(1);
                    diffEl.style.color = isExact ? "#4ade80" : "#3b82f6"; 
                }} else if (pts < 0) {{
                    diffEl.innerText = pts.toFixed(1);
                    diffEl.style.color = "#ef4444"; 
                }} else {{
                    diffEl.innerText = "+0.0";
                    diffEl.style.color = "#666"; 
                }}
            }});
        }}

        function animateLoop(time) {{
            if (!lastTime) lastTime = time;
            const delta = time - lastTime;
            lastTime = time;

            if (isPlaying) {{
                const speedMult = parseFloat(document.getElementById("speed-selector").value);
                const baseIdx = Math.floor(progress);
                const nextIdx = Math.min(baseIdx + 1, frames.length - 1);
                const isMilestone = (frames[nextIdx].type !== 'match' && frames[nextIdx].type !== 'start');
                
                const speedFactor = isMilestone ? 0.00015 : 0.0004; 
                progress += (delta * speedFactor) * speedMult;
                
                if (progress >= frames.length - 1) {{
                    progress = frames.length - 1;
                    isPlaying = false;
                    document.getElementById("btn-play").innerText = "▶️ PLAY";
                    document.getElementById("btn-play").classList.remove("active");
                }}
                
                document.getElementById("timeline-progress").value = progress;
                renderAtProgress(progress);
            }}
            
            animationReq = requestAnimationFrame(animateLoop);
        }}

        function togglePlay() {{
            const btn = document.getElementById("btn-play");
            if (isPlaying) {{
                isPlaying = false;
                btn.innerText = "▶️ PLAY";
                btn.classList.remove("active");
            }} else {{
                if (progress >= frames.length - 1) progress = 0;
                isPlaying = true;
                lastTime = performance.now(); 
                btn.innerText = "⏸️ PAUSA";
                btn.classList.add("active");
            }}
        }}

        function seekManual(val) {{
            progress = parseFloat(val);
            renderAtProgress(progress);
        }}
        
        function seekRelative(step) {{
            progress = Math.max(0, Math.min(frames.length - 1, progress + step));
            document.getElementById("timeline-progress").value = progress;
            renderAtProgress(progress);
        }}

        renderAtProgress(0);
        animationReq = requestAnimationFrame(animateLoop);
    </script>
</body>
</html>
    """
    
    ruta_salida = ROOT_DIR / "timeline.html"
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print(f"✅ ¡Motor de Pantalla Completa + Dinámica Y listo en: {ruta_salida}")

if __name__ == "__main__":
    generar_timeline()