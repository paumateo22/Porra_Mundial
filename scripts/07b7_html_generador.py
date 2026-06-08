import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def cargar_json(ruta):
    if not ruta.exists(): return {}
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

def generar_herramienta_pronosticos():
    print("=======================================================")
    print(" 🛠️ [07B7] GENERANDO HERRAMIENTA DE PRONÓSTICOS LIBRE 🛠️")
    print("=======================================================")
    
    jornadas = cargar_json(ROOT_DIR / "config" / "jornadas.json")
    realidad = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json")
    
    # Preparamos los datos de todas las fases cruzando jornadas (estructura) y realidad (equipos conocidos)
    todas_fases_data = {}
    fases_keys = ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"]
    
    for f in fases_keys:
        matches = []
        # Obtener estructura base de jornadas.json
        if f == "dieciseisavos":
            j_matches = jornadas.get("dieciseisavos.1", []) + jornadas.get("dieciseisavos.2", [])
        elif f == "finales":
            j_matches = jornadas.get("finales", [])
            if not j_matches:  # Por si estuvieran separados
                j_matches = jornadas.get("tercer_puesto", []) + jornadas.get("final", [])
        else:
            j_matches = jornadas.get(f, [])
            
        # Obtener datos reales de realidad_oficial.json
        r_matches = []
        if f == "finales":
            r_matches = realidad.get("eliminatorias", {}).get("tercer_puesto", []) + realidad.get("eliminatorias", {}).get("final", [])
        else:
            r_matches = realidad.get("eliminatorias", {}).get(f, [])
            
        # Cruzar datos
        for jm in j_matches:
            rm = next((m for m in r_matches if str(m.get("id_partido")) == str(jm.get("id_partido"))), None)
            if rm:
                matches.append(rm)
            else:
                matches.append({
                    "id_partido": jm.get("id_partido"),
                    "local": jm.get("local", "TBD"),
                    "visitante": jm.get("visitante", "TBD")
                })
        
        todas_fases_data[f] = matches

    todas_fases_json = json.dumps(todas_fases_data)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generador de Pronósticos</title>
    <link rel="stylesheet" href="theme.css">
    <style>
        body {{ background-color: #0d0d0d; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; }}
        .container {{ max-width: 1300px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: var(--gold, #d4af37); text-align: center; }}
        .card {{ background: #151515; border: 1px solid #333; border-radius: 8px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }}
        
        /* CSS Grid Dinámico para Paso 1 */
        .match-input-grid {{ display: grid; gap: 15px; }}
        .grid-4-col {{ grid-template-columns: repeat(4, 1fr); }}
        .grid-2-col {{ grid-template-columns: repeat(2, 1fr); }}
        @media (max-width: 1100px) {{ .grid-4-col {{ grid-template-columns: repeat(2, 1fr); }} }}
        @media (max-width: 650px) {{ .grid-4-col, .grid-2-col {{ grid-template-columns: 1fr; }} }}

        .match-box {{ background: #1a1a1a; border: 1px solid #333; border-radius: 6px; padding: 15px; text-align: center; position: relative; transition: 0.3s; }}
        .match-box:hover {{ border-color: #555; }}
        .team-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-weight: bold; font-size: 0.95em; }}
        .goal-input {{ width: 45px; background: #111; color: var(--gold, #d4af37); border: 1px solid #444; border-radius: 4px; padding: 6px; text-align: center; font-size: 1.1em; font-weight: bold; outline: none; }}
        .goal-input:focus {{ border-color: var(--gold, #d4af37); background: #000; }}
        
        .tie-breaker {{ margin-top: 10px; padding-top: 10px; border-top: 1px dashed #555; display: none; }}
        .tie-breaker label {{ font-size: 0.85em; color: #aaa; cursor: pointer; margin: 0 10px; padding: 5px; border-radius: 4px; transition:0.2s; }}
        .tie-breaker label:hover {{ background: #333; color: white; }}
        
        .btn-gen {{ display: block; width: 100%; max-width: 350px; margin: 30px auto; background: var(--gold, #d4af37); color: black; border: none; padding: 15px; font-size: 1.2em; font-weight: bold; border-radius: 8px; cursor: pointer; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; }}
        .btn-gen:hover {{ background: #ebd575; transform: scale(1.03); box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4); }}
        
        /* Bracket Styles Convergente */
        .bracket-container {{ display: flex; justify-content: center; gap: 20px; overflow-x: auto; padding: 20px 0; min-width: max-content; margin: 0 auto; }}
        .bracket-col {{ display: flex; flex-direction: column; justify-content: space-around; min-width: 140px; }}
        .bracket-match {{ background: #222; border: 1px solid #444; border-radius: 6px; padding: 8px 12px; margin: 8px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.4); text-align: center; }}
        .bracket-team {{ padding: 6px; cursor: pointer; transition: 0.2s; border-radius: 4px; margin-bottom: 3px; font-size: 0.85em; }}
        .bracket-team:hover {{ background: #333; border-color: #555; }}
        .bracket-team.winner {{ color: var(--gold, #d4af37); font-weight: bold; background: rgba(212, 175, 55, 0.1); border-left: 3px solid var(--gold, #d4af37); }}
        .bracket-team.loser {{ color: #555; text-decoration: line-through; }}
        .tbd {{ color: #666; font-style: italic; pointer-events: none; }}
    </style>
</head>
<body>
    {html_utils.get_sidebar_html("")}
    {html_utils.get_header_html("🛠️ Simulador y Generador", "Crea, experimenta y descarga tus pronósticos oficiales.", "")}
    
    <div class="sticky-nav" style="position: sticky; top: 0; z-index: 100; background: rgba(18,18,18,0.95); padding: 12px; border-bottom: 2px solid var(--gold); display: flex; gap: 10px; justify-content: center; overflow-x: auto; flex-wrap: nowrap; backdrop-filter: blur(5px); box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 20px;">
        <a href="index.html" style="background:#111; color:white; text-decoration:none; padding:8px 15px; border-radius:4px; font-weight:bold; border:1px solid #444; transition:0.3s;">⬅️ Volver al Inicio</a>
    </div>

    <div class="container">
        
        <!-- SELECTOR DE FASE -->
        <div class="card" style="text-align:center; padding:15px;">
            <label style="color:var(--gold, #d4af37); font-size:1.2em; font-weight:bold; margin-right:15px; display:inline-block; margin-bottom:10px;">Elige la fase desde la que arrancar:</label>
            <select id="fase_selector" onchange="init(this.value)" style="padding:10px 20px; font-size:1.1em; background:#222; color:white; border:1px solid var(--gold, #d4af37); border-radius:6px; outline:none; cursor:pointer;">
                <option value="dieciseisavos">1/16 de Final</option>
                <option value="octavos">Octavos de Final</option>
                <option value="cuartos">Cuartos de Final</option>
                <option value="semifinales">Semifinales</option>
                <option value="finales">Finales (3º Puesto y Final)</option>
            </select>
        </div>
        
        <!-- PASO 1: GOLES DE LA FASE ACTUAL -->
        <div id="step1" class="card">
            <h3>1. Introduce los goles de los partidos</h3>
            <p style="text-align:center; color:gray; font-size:0.9em; margin-bottom:20px;">Los empates forzarán la elección de un ganador por penaltis.</p>
            <div class="match-input-grid" id="grid-container"></div>
            <button class="btn-gen" onclick="generarBracket()">Paso 2: Construir Árbol 🌳</button>
        </div>

        <!-- PASO 2: BRACKET INTERACTIVO -->
        <div id="step2" class="card" style="display:none; padding: 25px 10px;">
            <h3>2. Completa el Árbol hacia el Centro</h3>
            <p style="text-align:center; color:gray; font-size:0.9em; margin-bottom:30px;">Haz clic en los equipos para avanzar de ronda hasta coronar un campeón.</p>
            
            <div style="width:100%; overflow-x:auto;">
                <div class="bracket-container" id="bracket-ui"></div>
            </div>
            
            <div style="margin-top: 50px; text-align:center; border-top: 1px dashed #444; padding-top: 30px;">
                <h3 style="color:white; margin-bottom:10px;">3. Exportar tu Pronóstico</h3>
                <p style="color:gray; font-size:0.85em; margin-bottom:20px;">Rellena tu nombre tal y como aparece en el sistema para descargar el JSON oficial.</p>
                <input type="text" id="participante_name" placeholder="Tu Nombre (ej. paco_perez)" style="padding:12px; width:100%; max-width:350px; border-radius:4px; border:1px solid #555; background:#111; color:white; font-size:1.1em; text-align:center; margin-bottom:15px; outline:none;">
                <br>
                <button class="btn-gen" style="background:#4ade80; color:black; max-width:400px;" onclick="descargarJSON()">💾 Descargar JSON Oficial</button>
                <button onclick="document.getElementById('step1').style.display='block'; document.getElementById('step2').style.display='none';" style="margin-top:15px; background:transparent; color:gray; border:none; cursor:pointer; text-decoration:underline; font-size:1em;">⬅️ Volver y editar goles iniciales</button>
            </div>
        </div>
    </div>

    <script>
        const TODAS_FASES = {todas_fases_json};
        const FASES_ORDEN = ["dieciseisavos", "octavos", "cuartos", "semifinales", "finales"];
        
        let FASE_TARGET = "dieciseisavos";
        let PARTIDOS_INICIALES = [];
        let myFases = [];
        let tree = {{}};

        function init(faseElegida) {{
            FASE_TARGET = faseElegida;
            PARTIDOS_INICIALES = TODAS_FASES[FASE_TARGET];
            let startIndex = FASES_ORDEN.indexOf(FASE_TARGET);
            myFases = FASES_ORDEN.slice(startIndex);
            tree = {{}};

            // Inicializar Estado del Árbol
            myFases.forEach((f, idx) => {{
                if(f === "finales") {{
                    tree[f] = [
                        {{ local: "TBD", visitante: "TBD", pasa: null, type: "tercer_puesto", goles_local: 0, goles_visitante: 0 }},
                        {{ local: "TBD", visitante: "TBD", pasa: null, type: "final", goles_local: 0, goles_visitante: 0 }}
                    ];
                }} else {{
                    let numMatches = PARTIDOS_INICIALES.length / Math.pow(2, idx);
                    tree[f] = [];
                    for(let i=0; i<numMatches; i++) tree[f].push({{ local: "TBD", visitante: "TBD", pasa: null, goles_local: 0, goles_visitante: 0 }});
                }}
            }});

            document.getElementById('step1').style.display = 'block';
            document.getElementById('step2').style.display = 'none';
            renderStep1();
        }}

        function formatName(name) {{
            return name.length > 15 ? name.substring(0, 13) + '...' : name;
        }}

        // Cargar Partidos Iniciales en Step 1
        function renderStep1() {{
            let container = document.getElementById('grid-container');
            
            // Asignar Layout de columnas basado en la fase
            container.className = "match-input-grid";
            if(FASE_TARGET === "dieciseisavos" || FASE_TARGET === "octavos") {{
                container.classList.add("grid-4-col");
            }} else {{
                container.classList.add("grid-2-col");
            }}

            let html = "";
            PARTIDOS_INICIALES.forEach((m, i) => {{
                let title = FASE_TARGET === "finales" ? (i === 0 ? "🥉 3º Puesto" : "🏆 Final") : `Partido ${{i+1}}`;
                
                html += `
                <div class="match-box">
                    <div style="color:gray; font-size:0.75em; margin-bottom:12px; text-transform:uppercase; letter-spacing:1px;">${{title}}</div>
                    <div class="team-row">
                        <span style="flex:1; text-align:right; margin-right:8px;" title="${{m.local}}">${{formatName(m.local)}}</span>
                        <input type="number" id="gl_${{i}}" class="goal-input" min="0" oninput="checkTie(${{i}})">
                        <span style="margin:0 4px; color:#555;">-</span>
                        <input type="number" id="gv_${{i}}" class="goal-input" min="0" oninput="checkTie(${{i}})">
                        <span style="flex:1; text-align:left; margin-left:8px;" title="${{m.visitante}}">${{formatName(m.visitante)}}</span>
                    </div>
                    <div id="tb_${{i}}" class="tie-breaker">
                        <span style="color:var(--gold); display:block; margin-bottom:8px;">⚖️ ¿Quién gana en penaltis?</span>
                        <div style="display:flex; justify-content:center; gap:10px;">
                            <label><input type="radio" name="tb_rad_${{i}}" value="local"> ${{formatName(m.local)}}</label>
                            <label><input type="radio" name="tb_rad_${{i}}" value="visitante"> ${{formatName(m.visitante)}}</label>
                        </div>
                    </div>
                </div>`;
            }});
            container.innerHTML = html;
        }}

        function checkTie(idx) {{
            let gl = document.getElementById(`gl_${{idx}}`).value;
            let gv = document.getElementById(`gv_${{idx}}`).value;
            let tb = document.getElementById(`tb_${{idx}}`);
            if(gl !== "" && gv !== "" && parseInt(gl) === parseInt(gv)) {{
                tb.style.display = "block";
            }} else {{
                tb.style.display = "none";
                let radios = document.getElementsByName(`tb_rad_${{idx}}`);
                radios.forEach(r => r.checked = false);
            }}
        }}

        function generarBracket() {{
            let ok = true;
            PARTIDOS_INICIALES.forEach((m, i) => {{
                let gl = document.getElementById(`gl_${{i}}`).value;
                let gv = document.getElementById(`gv_${{i}}`).value;
                
                if(gl === "" || gv === "") {{ ok = false; return; }}
                
                gl = parseInt(gl); gv = parseInt(gv);
                tree[FASE_TARGET][i].local = m.local;
                tree[FASE_TARGET][i].visitante = m.visitante;
                tree[FASE_TARGET][i].goles_local = gl;
                tree[FASE_TARGET][i].goles_visitante = gv;
                
                if(gl > gv) {{
                    tree[FASE_TARGET][i].pasa = m.local;
                    tree[FASE_TARGET][i].pierde = m.visitante;
                }} else if(gv > gl) {{
                    tree[FASE_TARGET][i].pasa = m.visitante;
                    tree[FASE_TARGET][i].pierde = m.local;
                }} else {{
                    let rads = document.getElementsByName(`tb_rad_${{i}}`);
                    let selected = Array.from(rads).find(r => r.checked);
                    if(!selected) {{ ok = false; return; }}
                    tree[FASE_TARGET][i].pasa = selected.value === 'local' ? m.local : m.visitante;
                    tree[FASE_TARGET][i].pierde = selected.value === 'local' ? m.visitante : m.local;
                }}
            }});

            if(!ok) {{ alert("Por favor, rellena todos los goles. Si hay empate, selecciona quién pasa."); return; }}

            document.getElementById('step1').style.display = 'none';
            document.getElementById('step2').style.display = 'block';
            
            cascadeBracket(0);
            renderBracketUI();
        }}

        function cascadeBracket(phaseIdx) {{
            if(phaseIdx >= myFases.length - 1) return;
            let currentFase = myFases[phaseIdx];
            let nextFase = myFases[phaseIdx+1];

            if(nextFase === "finales") {{
                let m0 = tree[currentFase][0];
                let m1 = tree[currentFase][1];
                // 3º Puesto
                tree[nextFase][0].local = m0.pierde || "TBD";
                tree[nextFase][0].visitante = m1.pierde || "TBD";
                tree[nextFase][0].pasa = null;
                tree[nextFase][0].pierde = null;
                // Final
                tree[nextFase][1].local = m0.pasa || "TBD";
                tree[nextFase][1].visitante = m1.pasa || "TBD";
                tree[nextFase][1].pasa = null;
                tree[nextFase][1].pierde = null;
            }} else {{
                for(let i=0; i<tree[currentFase].length; i+=2) {{
                    let m1 = tree[currentFase][i];
                    let m2 = tree[currentFase][i+1];
                    let nextMatchIdx = Math.floor(i/2);
                    tree[nextFase][nextMatchIdx].local = m1.pasa || "TBD";
                    tree[nextFase][nextMatchIdx].visitante = m2.pasa || "TBD";
                    tree[nextFase][nextMatchIdx].pasa = null;
                    tree[nextFase][nextMatchIdx].pierde = null;
                }}
            }}
            cascadeBracket(phaseIdx+1); 
        }}

        function selectWinner(fase, matchIdx, isLocal) {{
            if(fase === FASE_TARGET) return; 
            
            let m = tree[fase][matchIdx];
            let winner = isLocal ? m.local : m.visitante;
            let loser = isLocal ? m.visitante : m.local;
            
            if(winner === "TBD") return;

            m.pasa = winner;
            m.pierde = loser;
            
            let faseIdx = myFases.indexOf(fase);
            cascadeBracket(faseIdx);
            renderBracketUI();
        }}

        // Renderiza el árbol desde los lados hacia el centro
        function renderBracketUI() {{
            let container = document.getElementById('bracket-ui');
            let mitades_left = [];
            let mitades_right = [];
            let center_html = "";

            myFases.forEach(f => {{
                let isLocked = f === FASE_TARGET;
                let opacity = isLocked ? "opacity:0.6; pointer-events:none;" : "";
                
                if (f === "finales") {{
                    let m3rd = tree[f][0];
                    let mFin = tree[f][1];
                    
                    let cLocFin = mFin.local === "TBD" ? "tbd" : (mFin.pasa === mFin.local ? "winner" : (mFin.pasa ? "loser" : ""));
                    let cVisFin = mFin.visitante === "TBD" ? "tbd" : (mFin.pasa === mFin.visitante ? "winner" : (mFin.pasa ? "loser" : ""));
                    
                    let cLoc3rd = m3rd.local === "TBD" ? "tbd" : (m3rd.pasa === m3rd.local ? "winner" : (m3rd.pasa ? "loser" : ""));
                    let cVis3rd = m3rd.visitante === "TBD" ? "tbd" : (m3rd.pasa === m3rd.visitante ? "winner" : (m3rd.pasa ? "loser" : ""));

                    center_html = `<div class="bracket-col" style="${{opacity}} min-width:170px; justify-content:center; gap:50px;">
                        <div class="bracket-match">
                            <div style="font-size:0.8em; color:var(--gold); margin-bottom:8px; font-weight:bold; letter-spacing:1px;">🏆 FINAL</div>
                            <div class="bracket-team ${{cLocFin}}" onclick="selectWinner('${{f}}', 1, true)" title="${{mFin.local}}">${{formatName(mFin.local)}}</div>
                            <div class="bracket-team ${{cVisFin}}" onclick="selectWinner('${{f}}', 1, false)" title="${{mFin.visitante}}">${{formatName(mFin.visitante)}}</div>
                        </div>
                        <div class="bracket-match">
                            <div style="font-size:0.8em; color:#a9b7c6; margin-bottom:8px; font-weight:bold; letter-spacing:1px;">🥉 3º PUESTO</div>
                            <div class="bracket-team ${{cLoc3rd}}" onclick="selectWinner('${{f}}', 0, true)" title="${{m3rd.local}}">${{formatName(m3rd.local)}}</div>
                            <div class="bracket-team ${{cVis3rd}}" onclick="selectWinner('${{f}}', 0, false)" title="${{m3rd.visitante}}">${{formatName(m3rd.visitante)}}</div>
                        </div>
                    </div>`;
                }} else {{
                    let n = tree[f].length;
                    let half = Math.ceil(n / 2);
                    let leftMatches = tree[f].slice(0, half);
                    let rightMatches = tree[f].slice(half);

                    const renderMatch = (m, idx) => {{
                        let cLoc = m.local === "TBD" ? "tbd" : (m.pasa === m.local ? "winner" : (m.pasa ? "loser" : ""));
                        let cVis = m.visitante === "TBD" ? "tbd" : (m.pasa === m.visitante ? "winner" : (m.pasa ? "loser" : ""));
                        return `<div class="bracket-match">
                            <div class="bracket-team ${{cLoc}}" onclick="selectWinner('${{f}}', ${{idx}}, true)" title="${{m.local}}">${{formatName(m.local)}}</div>
                            <div class="bracket-team ${{cVis}}" onclick="selectWinner('${{f}}', ${{idx}}, false)" title="${{m.visitante}}">${{formatName(m.visitante)}}</div>
                        </div>`;
                    }};

                    let colL = `<div class="bracket-col" style="${{opacity}} min-width:140px;">
                        <div style="text-align:center; color:gray; font-size:0.8em; font-weight:bold; border-bottom:1px solid #444; padding-bottom:6px; margin-bottom:12px; text-transform:uppercase;">${{f.replace('_', ' ')}}</div>
                        <div style="flex:1; display:flex; flex-direction:column; justify-content:space-around;">
                            ${{leftMatches.map((m, i) => renderMatch(m, i)).join('')}}
                        </div>
                    </div>`;
                    mitades_left.push(colL);

                    if (rightMatches.length > 0) {{
                        let colR = `<div class="bracket-col" style="${{opacity}} min-width:140px;">
                            <div style="text-align:center; color:gray; font-size:0.8em; font-weight:bold; border-bottom:1px solid #444; padding-bottom:6px; margin-bottom:12px; text-transform:uppercase;">${{f.replace('_', ' ')}}</div>
                            <div style="flex:1; display:flex; flex-direction:column; justify-content:space-around;">
                                ${{rightMatches.map((m, i) => renderMatch(m, i + half)).join('')}}
                            </div>
                        </div>`;
                        mitades_right.unshift(colR); // Se insertan al principio para invertir el orden hacia el centro
                    }}
                }}
            }});

            container.innerHTML = mitades_left.join('') + center_html + mitades_right.join('');
        }}

        function descargarJSON() {{
            let part = document.getElementById('participante_name').value.trim();
            if(!part) {{ alert("Introduce un nombre identificativo para descargar el archivo."); return; }}

            let full = true;
            myFases.forEach(f => {{
                tree[f].forEach(m => {{ if(!m.pasa) full = false; }});
            }});
            if(!full) {{ alert("Debes hacer clic y seleccionar a los ganadores hasta completar la Final y el 3º Puesto."); return; }}

            let out = {{
                participante: part,
                fase_origen: FASE_TARGET,
                predicciones: {{}}
            }};

            myFases.forEach(f => {{
                if(f === "finales") {{
                    let m3rd = tree[f][0];
                    let mFin = tree[f][1];
                    out.predicciones["finales"] = [
                        {{ local: m3rd.local, visitante: m3rd.visitante, goles_local: m3rd.goles_local || 0, goles_visitante: m3rd.goles_visitante || 0, pasa: m3rd.pasa }},
                        {{ local: mFin.local, visitante: mFin.visitante, goles_local: mFin.goles_local || 0, goles_visitante: mFin.goles_visitante || 0, pasa: mFin.pasa }}
                    ];
                }} else {{
                    out.predicciones[f] = tree[f].map(m => ({{
                        local: m.local, visitante: m.visitante,
                        goles_local: m.goles_local, goles_visitante: m.goles_visitante, pasa: m.pasa
                    }}));
                }}
            }});

            const blob = new Blob([JSON.stringify(out, null, 4)], {{type: "application/json"}});
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `${{FASE_TARGET}}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }}

        // Inicializar por defecto
        window.onload = () => init("dieciseisavos");
    </script>
</body>
</html>
"""

    ruta_salida = ROOT_DIR / "generador_pronosticos.html"
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"✅ Generador Web creado en: {ruta_salida.relative_to(ROOT_DIR)}")

if __name__ == "__main__":
    generar_herramienta_pronosticos()