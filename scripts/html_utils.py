import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

CONFIG = cargar_json(ROOT_DIR / "config" / "settings.json") or {"multiplicadores": {"incremento_racha_por_fase": 0.5}}

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

def get_header_html(title, subtitle, depth="", show_participa=False):
    participa_btn = f'<br><a href="{depth}instrucciones.html" class="btn-participa">¡PARTICIPA AHORA!</a>' if show_participa else ""
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
        {participa_btn}
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