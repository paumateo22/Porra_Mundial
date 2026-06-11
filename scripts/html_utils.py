import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).resolve().parent.parent

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

CONFIG = cargar_json(ROOT_DIR / "config" / "settings.json") or {"multiplicadores": {"incremento_racha_por_fase": 0.5}}

def get_sidebar_html(depth=""):
    return f"""
    <style>
        /* Estilos críticos para asegurar que el menú quede por encima de todo */
        .sidenav {{
            position: fixed; /* Obligatorio para que funcione z-index */
            z-index: 2147483647; /* El z-index máximo posible en navegadores */
        }}
        
        /* Asegura que el botón de hamburguesa flote correctamente debajo del menú desplegado */
        .menu-btn {{
            position: fixed;     
            z-index: 2147483640; 
            cursor: pointer;     
        }}
    </style>

    <div id="mySidenav" class="sidenav">
        <a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>
        <a href="{depth}index.html">🏠 Clasificación Global</a>
        <a href="{depth}calendario.html">📅 Calendario Oficial</a>
        <a href="{depth}jornadas.html">📈 Análisis por Jornadas</a>
        <a href="{depth}participantes.html">👥 Participantes</a>
        <a href="{depth}instrucciones.html" style="color:var(--gold);">📖 Instrucciones & Registro & Reglamento</a>
        <a href="https://www.infobae.com/mundial-2026/simulador/" target="_blank">🔗 Infobae</a>
        {f'<a href="{depth}generador_pronosticos.html" class="participa-btn">🛠️ Pronosticar Eliminatorias</a>' if 'LiveFutbol' in str(depth) else f'<a href="{depth}generador_pronosticos.html" class="participa-btn">🛠️ Pronosticar Eliminatorias</a>'}
        <a href="https://www.sofascore.com/es-la/football/tournament/world/world-championship/16#id:58210" target="_blank">🔗 SofaScore</a>
    </div>
    <div class="menu-btn" onclick="openNav()">☰</div>
    <script>
        function openNav() {{ document.getElementById("mySidenav").style.width = "250px"; }}
        function closeNav() {{ document.getElementById("mySidenav").style.width = "0"; }}
    </script>
    """


def get_header_html(title, subtitle, depth="", show_participa=False):
    participa_btn = f'<div style="text-align:center; margin-top:20px;"><a href="{depth}instrucciones.html" class="btn-participa" style="display:inline-block; padding:15px 30px; font-size:1.2em; border-radius:30px; background:var(--gold); color:black; font-weight:bold; text-decoration:none; box-shadow:0 0 15px rgba(218,165,32,0.5);">¡PARTICIPA AHORA!</a></div>' if show_participa else ""

    # -----------------------------------------------------
    # EXTRACCION DE DATOS PARA LOS WIDGETS
    # -----------------------------------------------------
    realidad_dict = cargar_json(ROOT_DIR / "data" / "resultados" / "realidad_oficial.json") or {}
    todos_partidos = []

    for g, pts in realidad_dict.get("fase_grupos", {}).items():
        for p in pts:
            if p.get("fecha"):
                p_copy = p.copy()
                p_copy["nombre_fase"] = g
                todos_partidos.append(p_copy)

    for f, pts in realidad_dict.get("eliminatorias", {}).items():
        for p in pts:
            if p.get("fecha"):
                p_copy = p.copy()
                p_copy["nombre_fase"] = "1/16" if f == "dieciseisavos" else ("1/8" if f == "octavos" else ("1/4" if f == "cuartos" else f.capitalize()))
                todos_partidos.append(p_copy)

    todos_partidos.sort(key=lambda x: x.get("fecha", ""))

    last_match = None
    next_match = None
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))

    for p in todos_partidos:
        if p.get("estado") == "finished":
            last_match = p
        elif p.get("estado") == "notstarted" and not next_match:
            # LÓGICA DE FILTRADO TEMPORAL
            # Si el partido no ha empezado oficialmente en SofaScore pero ya ha
            # superado la hora actual, lo saltamos y buscamos el siguiente.
            fecha_p = p.get("fecha", "")
            try:
                dt_p = datetime.fromisoformat(fecha_p).replace(tzinfo=ZoneInfo("Europe/Madrid"))
                if dt_p > ahora:
                    next_match = p
            except Exception:
                # Fallback por si la fecha tiene un formato anómalo
                next_match = p

    # --- Renderizado Ultimo Partido ---
    last_html = "<div style='color:#555; padding-top:20px; font-weight:bold;'>No se ha jugado ningún partido todavía</div>"
    if last_match:
        fase_l = last_match.get("nombre_fase", "")
        loc_l = last_match.get("local", "TBD")
        vis_l = last_match.get("visitante", "TBD")
        gl = last_match.get("goles_local", "-")
        gv = last_match.get("goles_visitante", "-")
        fecha_l = last_match.get("fecha", "")
        try:
            dt_l = datetime.fromisoformat(fecha_l)
            fecha_l_str = dt_l.strftime("%d/%m %H:%M")
        except:
            fecha_l_str = fecha_l

        last_html = f"""
        <div style="font-weight:bold; color:#111; letter-spacing:1px; margin-bottom:10px; font-size:1.1em;">{fase_l.upper()}</div>
        <div style="font-size:1.15em; color:black; font-weight:900; margin-bottom:8px; line-height:1.3;">
            {loc_l} <span style="background:#111; color:white; padding:2px 8px; border-radius:4px; margin:0 5px;">{gl}-{gv}</span> {vis_l}
        </div>
        <div style="font-size:0.85em; color:#333; font-weight:bold; border-top:1px dashed rgba(0,0,0,0.3); padding-top:5px;">
            Finalizado: {fecha_l_str}
        </div>
        """

    # --- Renderizado Proximo Partido ---
    next_match_fecha = ""
    next_html_pre = "<div style='color:#555; padding-top:20px; font-weight:bold;'>TBD</div>"
    if next_match:
        fase_n = next_match.get("nombre_fase", "")
        loc_n = next_match.get("local", "TBD")
        vis_n = next_match.get("visitante", "TBD")
        next_match_fecha = next_match.get("fecha", "")
        try:
            dt_n = datetime.fromisoformat(next_match_fecha)
            fecha_n_str = dt_n.strftime("%d/%m %H:%M")
        except:
            fecha_n_str = next_match_fecha

        next_html_pre = f"""
        <div style="font-weight:bold; color:#111; letter-spacing:1px; margin-bottom:10px; font-size:1.1em;">{fase_n.upper()}</div>
        <div style="font-size:1.15em; color:black; font-weight:900; margin-bottom:8px; line-height:1.3;">
            {loc_n} - {vis_n}
        </div>
        <div style="font-size:1.2em; color:#333; font-weight:500; border-top:1px dashed rgba(0,0,0,0.3); padding-top:5px; margin-bottom:5px;">
            Inicio: {fecha_n_str}
        </div>
        <div id="w-timer-next-match" style="font-size:2em; font-weight:1500; color:#d9381e; font-family:monospace;">--:--:--</div>
        """

    horarios = CONFIG.get("horarios", {})
    fases_js = [
        {"id": "grupos", "name": "Fase de Grupos", "predict": "2000-01-01T00:00:00", "start": horarios.get("apertura_grupos", ""), "link": "https://www.infobae.com/mundial-2026/simulador/"},
        {"id": "dieciseisavos", "name": "Dieciseisavos (1/16)", "predict": horarios.get("apertura_fin_fase_grupos", ""), "start": horarios.get("apertura_dieciseisavos", ""), "link": f"{depth}generador_pronosticos.html"},
        {"id": "octavos", "name": "Octavos (1/8)", "predict": horarios.get("apertura_fin_dieciseisavos", ""), "start": horarios.get("apertura_octavos", ""), "link": f"{depth}generador_pronosticos.html"},
        {"id": "cuartos", "name": "Cuartos (1/4)", "predict": horarios.get("apertura_fin_octavos", ""), "start": horarios.get("apertura_cuartos", ""), "link": f"{depth}generador_pronosticos.html"},
        {"id": "semifinales", "name": "Semifinales", "predict": horarios.get("apertura_fin_cuartos", ""), "start": horarios.get("apertura_semifinales", ""), "link": f"{depth}generador_pronosticos.html"},
        {"id": "finales", "name": "Finales", "predict": horarios.get("apertura_fin_semifinales", ""), "start": horarios.get("apertura_finales", ""), "link": f"{depth}generador_pronosticos.html"}
    ]
    fases_js_str = json.dumps(fases_js)

    return f"""
    <header style="padding: 20px 10px; padding-bottom: 30px;">
        <style>
            .header-main-container {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 1300px;
                margin: 0 auto;
                gap: 15px;
            }}

            .header-center {{
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                min-width: 380px;
            }}

            .blob-widget {{
                background: var(--gold, #DAA520);
                color: black;
                width: 420px;
                padding: 15px 25px;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                justify-content: center;
                border: 2px solid #111;
                box-shadow: -4px 6px 0px rgba(0,0,0,0.4);
                overflow: hidden;
            }}

            .left-blob {{
                border-radius: 40px 15px 50px 20px;
                width: 380px;
                height: 220px;
                min-height: 180px;
            }}

            .right-blob-top {{
                border-radius: 20px 40px 10px 20px;
                min-height: 80px;
            }}

            .right-blob-bottom {{
                border-radius: 10px 20px 40px 15px;
                min-height: 100px;
            }}

            .right-widgets-stack {{
                display: flex;
                flex-direction: column;
                gap: 15px;
                width: 280px;
            }}

            .blob-title {{
                font-family: Arial, sans-serif;
                font-weight: 900;
                font-size: 1.05em;
                margin: 0 0 10px 0;
                text-transform: uppercase;
                letter-spacing: 1px;
                text-align: center;
                border-bottom: 1px dashed rgba(0,0,0,0.35);
                padding-bottom: 6px;
            }}

            .phase-row {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                margin-bottom: 10px;
            }}

            .phase-label {{
                font-size: 0.78em;
                text-transform: uppercase;
                font-weight: bold;
                color: #333;
                margin-bottom: 4px;
                text-align: center;
            }}

            .phase-timer {{
                font-size: 2em;
                font-family: monospace;
                font-weight: 1500;
                background: rgba(0,0,0,0.1);
                padding: 4px 10px;
                border-radius: 8px;
                border: 1px solid rgba(0,0,0,0.2);
                display: inline-block;
            }}

            .btn-pred-now {{
                display: inline-block;
                background: #111;
                color: var(--gold);
                font-size: 0.95em;
                font-weight: 900;
                padding: 8px 16px;
                border-radius: 30px;
                text-decoration: none;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                border: 2px solid #111;
                transition: 0.3s;
                margin: 4px auto;
                text-align: center;
            }}

            .btn-pred-now:hover {{
                background: transparent;
                color: #111;
            }}

            @media (max-width: 950px) {{
                .header-main-container {{
                    flex-direction: column;
                    gap: 25px;
                }}

                .blob-widget,
                .left-blob,
                .right-widgets-stack {{
                    width: 100%;
                    max-width: 380px;
                }}

                .blob-widget {{
                    height: auto;
                    min-height: 100px;
                    box-shadow: 0 5px 10px rgba(0,0,0,0.4);
                    border-radius: 25px !important;
                }}
            }}
        </style>

        <div class="header-main-container">
            <div class="blob-widget left-blob">
                <div class="blob-title" id="w-fase-name">CARGANDO FASE...</div>

                <div id="w-predict-container" style="min-height: 52px; display:flex; flex-direction:column; justify-content:center; align-items:center;">
                    <div class="phase-label">Apertura Pronosticos</div>
                    <div class="phase-timer" id="w-timer-pred">--:--:--</div>
                </div>

                <div class="phase-row" style="margin-top:6px; margin-bottom:0;">
                    <div class="phase-label" style="font-size:1em;">Comienzo de Fase</div>
                    <div class="phase-timer" id="w-timer-start" style="color:#d9381e;">--:--:--</div>
                </div>
            </div>

            <div class="header-center">
                <h1 style="margin-top:0; font-size: 2.2em;">{title}</h1>
                <p style="font-size: 0.9em;">{subtitle}</p>
                <div class="top-nav" style="margin: 10px 0;">
                    <a href="{depth}index.html" class="home-btn">🏠 Inicio</a>
                    <a href="https://www.infobae.com/mundial-2026/simulador/" target="_blank">Infobae</a>
                    <a href="{depth}generador_pronosticos.html" class="participa-btn">🛠️ Pronosticar Eliminatorias</a>
                    <a href="https://www.sofascore.com/es-la/football/tournament/world/world-championship/16#id:58210" target="_blank">SofaScore</a>
                </div>
                {participa_btn}
            </div>

            <div class="right-widgets-stack">

                <div class="blob-widget right-blob-top">
                    <div class="blob-title">ÚLTIMO PARTIDO</div>
                    {last_html}
                </div>

                <div class="blob-widget right-blob-bottom">
                    <div class="blob-title">PRÓXIMO PARTIDO</div>
                    {next_html_pre}
                </div>

            </div>
        </div>

        <script>
            const FASES_TORNEO = {fases_js_str};
            const NEXT_MATCH_ISO = "{next_match_fecha}";

            function formatDiff(ms) {{
                if (ms <= 0) return "00:00:00";
                let d = Math.floor(ms / (1000 * 60 * 60 * 24));
                let h = Math.floor((ms / (1000 * 60 * 60)) % 24);
                let m = Math.floor((ms / 1000 / 60) % 60);
                let s = Math.floor((ms / 1000) % 60);

                let res = "";
                if (d > 0) res += d + "d, ";
                res += h.toString().padStart(2, "0") + ":" + m.toString().padStart(2, "0") + ":" + s.toString().padStart(2, "0");
                return res;
            }}

            function updateWidgets() {{
                const now = new Date();

                // Widget izquierdo
                let currentFase = null;
                for (let i = 0; i < FASES_TORNEO.length; i++) {{
                    if (FASES_TORNEO[i].start && new Date(FASES_TORNEO[i].start) > now) {{
                        currentFase = FASES_TORNEO[i];
                        break;
                    }}
                }}

                if (!currentFase) {{
                    document.getElementById("w-fase-name").innerText = "TORNEO FINALIZADO";
                    document.getElementById("w-predict-container").innerHTML = "<div style='font-size:1em; font-weight:bold; text-align:center;'>Gracias por jugar</div>";
                    document.getElementById("w-timer-start").innerHTML = "CERRADO";
                }} else {{
                    document.getElementById("w-fase-name").innerText = currentFase.name;

                    const startPredict = new Date(currentFase.predict);
                    const endPredict = new Date(currentFase.start);
                    const predContainer = document.getElementById("w-predict-container");

                    if (now < startPredict) {{
                        predContainer.innerHTML = `<div class="phase-label">Apertura Pronosticos</div><div class="phase-timer">${{formatDiff(startPredict - now)}}</div>`;
                    }} else if (now >= startPredict && now < endPredict) {{
                        predContainer.innerHTML = `<a href="${{currentFase.link}}" class="btn-pred-now">¡PRONOSTICAR AHORA!</a>`;
                    }} else {{
                        predContainer.innerHTML = `<div class="phase-label">Pronosticos</div><div class="phase-timer">CERRADOS</div>`;
                    }}

                    document.getElementById("w-timer-start").innerText = formatDiff(endPredict - now);
                }}

                // Widgets derechos - countdown próximo partido
                if (NEXT_MATCH_ISO) {{
                    const matchDate = new Date(NEXT_MATCH_ISO);
                    const timerEl = document.getElementById("w-timer-next-match");

                    if (timerEl) {{
                        if (now < matchDate) {{
                            timerEl.innerText = formatDiff(matchDate - now);
                        }} else {{
                            // Si el usuario deja la pestaña abierta pasada la hora
                            timerEl.innerText = "00:00:00";
                            timerEl.style.color = "#d9381e";
                        }}
                    }}
                }}
            }}

            setInterval(updateWidgets, 1000);
            updateWidgets();
        </script>

        <script data-goatcounter="https://porramundial.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
        
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
            gl = int(p.get('goles_local', 0)) if str(p.get('goles_local', '')).isdigit() else 0
            gv = int(p.get('goles_visitante', 0)) if str(p.get('goles_visitante', '')).isdigit() else 0
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
                        rastros.append(("Grupos", f"participantes/{jugador_dir.name}/pronosticos/grupos/{jugador_dir.name}_base.json"))
                        break
        else:
            ruta_ocr = jugador_dir / "pronosticos" / "eliminatorias" / fase_origen / f"{fase_origen}.json"
            if ruta_ocr.exists():
                ocr_data = cargar_json(ruta_ocr)
                for p in ocr_data.get("predicciones", {}).get(fase_busqueda_ocr, []):
                    if p.get("local") == equipo or p.get("visitante") == equipo:
                        nombres_cortos = {"dieciseisavos": "1/16", "octavos": "1/8", "cuartos": "1/4", "semifinales": "Semis"}
                        rastros.append((nombres_cortos.get(fase_origen, fase_origen), f"participantes/{jugador_dir.name}/pronosticos/eliminatorias/{fase_origen}/{fase_origen}.json"))
                        break
    return rastros
