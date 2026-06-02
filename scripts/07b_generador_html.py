import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

# =====================================================================
# ESTILOS CSS GLOBALES (Dorado y Oscuro)
# =====================================================================
CSS_BASE = """
<style>
    :root { --bg-dark: #121212; --bg-card: #1e1e1e; --gold: #ffd700; --text-main: #e0e0e0; --accent: #2b5876; }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg-dark); color: var(--text-main); margin: 0; padding: 0; line-height: 1.6; }
    header { background: linear-gradient(135deg, #1a2a6c, #112240, var(--accent)); padding: 40px 20px; text-align: center; border-bottom: 3px solid var(--gold); box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    h1 { margin: 0; color: var(--gold); font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.6); }
    h2 { color: var(--gold); border-bottom: 1px solid #333; padding-bottom: 10px; margin-top: 40px; }
    .container { width: 95%; max-width: 1100px; margin: 30px auto; }
    
    table { width: 100%; border-collapse: collapse; margin-top: 20px; background-color: var(--bg-card); border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    th, td { padding: 12px 15px; text-align: center; border-bottom: 1px solid #333; }
    th { background-color: #252525; color: var(--gold); text-transform: uppercase; font-size: 0.9em; letter-spacing: 1px; }
    tr:last-child td { border-bottom: none; }
    tr:hover { background-color: #2a2a2a; }
    
    .jugadores-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-top: 30px; }
    .card { background-color: var(--bg-card); border: 1px solid #333; border-radius: 10px; padding: 25px 20px; text-align: center; text-decoration: none; color: white; transition: all 0.3s ease; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .card:hover { transform: translateY(-5px); border-color: var(--gold); box-shadow: 0 8px 20px rgba(255,215,0,0.15); }
    .card h3 { margin: 0 0 10px 0; font-size: 1.5em; color: var(--text-main); }
    
    .btn-back { display: inline-block; margin-bottom: 20px; padding: 10px 20px; background-color: #333; color: #fff; text-decoration: none; border-radius: 5px; font-weight: bold; transition: 0.3s; }
    .btn-back:hover { background-color: var(--gold); color: #000; }
    
    .win { color: var(--gold); font-weight: bold; }
    .lose { color: #ff4d4d; font-weight: bold; }
    .img-fluid { max-width: 100%; height: auto; border-radius: 5px; }
</style>
"""

def cargar_json(ruta):
    if not ruta.exists(): return None
    with open(ruta, 'r', encoding='utf-8') as f: return json.load(f)

def limpiar_nombre_archivo(nombre):
    reemplazos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', ' ': '_'}
    res = nombre.lower()
    for orig, rep in reemplazos.items(): res = res.replace(orig, rep)
    return "".join(c for c in res if c.isalnum() or c == '_') + "_sd.png"

# =====================================================================
# GENERADOR DEL INDEX.HTML (RANKING GLOBAL)
# =====================================================================
def generar_index_html():
    ruta_csv = ROOT_DIR / "data" / "resultados" / "ranking_oficial.csv"
    if not ruta_csv.exists(): return False

    fecha_act = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏆 Porra Mundial 2026</title>
    {CSS_BASE}
</head>
<body>
    <header>
        <h1>🏆 Porra Mundial 2026</h1>
        <p>Panel de Estadísticas Oficiales | Actualizado: {fecha_act}</p>
    </header>
    <div class="container">
        <h2>Clasificación General</h2>
        <div style="overflow-x: auto;">
            <table>
                <tr>
                    <th>Pos</th><th>Jugador</th><th>Totales</th><th>Pts Sorpresa</th><th>Pts Decepción</th>
                </tr>
"""
    jugadores = []
    with open(ruta_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pos = row['Posicion']
            if pos == "1": pos = "🥇 1º"
            elif pos == "2": pos = "🥈 2º"
            elif pos == "3": pos = "🥉 3º"
            else: pos = f"{pos}º"
            
            jug = row['Jugador']
            jug_id = jug.replace(' ', '_').lower()
            jugadores.append({"nombre": jug, "id": jug_id})
            
            # Recolectar datos rápidos del libro
            ruta_libro = ROOT_DIR / "participantes" / jug_id / "estadisticas" / "historial_puntos.json"
            libro = cargar_json(ruta_libro) or {}
            premios = libro.get("premios_finales", {}).get("formularios", {}).get("detalles", {})
            sorp = premios.get("sorpresa", 0)
            dec = premios.get("decepcion", 0)
            
            html += f"""
                <tr>
                    <td>{pos}</td>
                    <td><a href="participantes/{jug_id}/vistas/dashboard.html" style="color:var(--gold); font-weight:bold; text-decoration:none;">{jug}</a></td>
                    <td style="font-weight:bold; font-size:1.1em;">{row['TOTAL']}</td>
                    <td>{sorp}</td>
                    <td>{dec}</td>
                </tr>"""
    
    html += """
            </table>
        </div>
        
        <h2>Dashboards Individuales</h2>
        <div class="jugadores-grid">
"""
    for j in jugadores:
        html += f"""
            <a href="participantes/{j['id']}/vistas/dashboard.html" class="card">
                <h3>{j['nombre']}</h3>
                <p>Ver estadísticas 📊</p>
            </a>"""
            
    html += """
        </div>
    </div>
</body>
</html>
"""
    with open(ROOT_DIR / "index.html", 'w', encoding='utf-8') as f:
        f.write(html)
    return True

# =====================================================================
# GENERADOR DE DASHBOARDS PERSONALES
# =====================================================================
def generar_dashboards_html():
    dir_participantes = ROOT_DIR / "participantes"
    jugadores = [p for p in dir_participantes.iterdir() if p.is_dir()]
    
    for jugador_dir in jugadores:
        nombre = jugador_dir.name.replace('_', ' ').title()
        libro = cargar_json(jugador_dir / "estadisticas" / "historial_puntos.json")
        if not libro: continue
        
        posicion = libro.get("posicion_final_ranking", "-")
        pts_totales = libro.get("puntos_totales", 0)
        
        # Crear la carpeta de vistas si no existe
        dir_vistas = jugador_dir / "vistas"
        dir_vistas.mkdir(parents=True, exist_ok=True)
        
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfil de {nombre} - Porra Mundial</title>
    {CSS_BASE}
</head>
<body>
    <header>
        <h1>👤 Dashboard: {nombre}</h1>
        <p>Posición: <strong>{posicion}º</strong> | Puntos Totales: <strong style="color:var(--gold); font-size:1.2em;">{pts_totales}</strong></p>
    </header>
    <div class="container">
        <a href="../../../index.html" class="btn-back">⬅️ Volver a la Clasificación</a>
        
        <h2>Matriz de Sorpresas y Decepciones</h2>
        <div style="overflow-x: auto;">
            <table>
                <tr>
                    <th>Selección</th>
                    <th>Gráfico de Rendimiento</th>
                    <th>Datos (P/M/R)</th>
                    <th>Resultado</th>
                </tr>
"""
        matriz_sd = libro.get("matriz_sorpresas_decepciones", {})
        if matriz_sd:
            for eq, datos in sorted(matriz_sd.items()):
                P, M, R = datos["pronostico"], datos["media_grupo"], datos["realidad"]
                puntos, res_txt = datos["puntos"], datos["resultado_calculo"]
                
                estado_html = f"<span style='color:gray;'>Sin Premio</span><br>({puntos} pts)"
                if res_txt == "Sorpresa": estado_html = f"<span class='win'>🔥 +{puntos} Pts<br>¡Sorpresa!</span>"
                elif res_txt == "Decepción": estado_html = f"<span class='lose'>📉 +{puntos} Pts<br>¡Decepción!</span>"
                
                img_name = limpiar_nombre_archivo(eq)
                # Ruta relativa desde /vistas/dashboard.html a /estadisticas/graficos_sd/
                html += f"""
                <tr>
                    <td style="font-weight:bold;">{eq}</td>
                    <td><img src="../estadisticas/graficos_sd/{img_name}" class="img-fluid" alt="Gráfico {eq}" onerror="this.style.display='none'"></td>
                    <td style="font-size:0.9em; text-align:left; padding-left:20px;">
                        Tú: <strong>{P}</strong><br>Media: {M}<br>Real: {R}
                    </td>
                    <td>{estado_html}</td>
                </tr>"""
        else:
            html += "<tr><td colspan='4'>Aún no hay datos de sorpresas y decepciones calculados.</td></tr>"
            
        html += """
            </table>
        </div>
    </div>
</body>
</html>
"""
        with open(dir_vistas / "dashboard.html", 'w', encoding='utf-8') as f:
            f.write(html)

def ejecutar_07b():
    print("=======================================================")
    print(" 🌐 [07B] INICIANDO RENDERIZADO HTML FRONTEND 🌐")
    print("=======================================================")
    if generar_index_html():
        print("✅ index.html global generado con éxito.")
        generar_dashboards_html()
        print("✅ Dashboards individuales HTML generados en las carpetas de 'vistas'.")
    else:
        print("❌ Error: No se encontró el ranking_oficial.csv")

if __name__ == "__main__":
    ejecutar_07b()