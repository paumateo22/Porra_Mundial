import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
import html_utils

def generar_instrucciones_html():
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instrucciones y Registro - Porra Mundial</title>
    <link rel="stylesheet" href="theme.css">
</head>
<body>
    {html_utils.get_sidebar_html("")}
    {html_utils.get_header_html("📖 Instrucciones & Registro", "Todo lo que necesitas saber para participar en la Porra Mundial 2026", "")}
    <div class="container">
        <h2>Registro en 3 Pasos</h2>
        <div class="instrucciones-box">
            <h3>Paso 1: Fase de Grupos (Infobae)</h3>
            <p>Primero, debes pronosticar todos los resultados de la fase de grupos usando el simulador de Infobae.</p>
            <p>🔗 <a href="https://www.infobae.com/mundial-2026/simulador/" target="_blank">Abrir Simulador Infobae</a></p>
            <p><i>Nota: Copia el enlace de tus resultados para el siguiente paso.</i></p>
        </div>
        <div class="instrucciones-box">
            <h3>Paso 2: Registro Oficial y Premios (Google Forms)</h3>
            <p>Rellena el formulario oficial. Aquí deberás pegar el enlace de Infobae con tu pronóstico y votar por los premios extra.</p>
            <p>🔗 <a href="https://docs.google.com/forms/d/e/1FAIpQLSdd_VDG4fUwA3l9eLJa0EmKJ64NeoMYGZv6YvPE_VnrhBTYMg/viewform" target="_blank">Rellenar Formulario Oficial</a></p>
        </div>
        <div class="instrucciones-box">
            <h3>Paso 3: Eliminatorias (LiveFutbol)</h3>
            <p>Finalmente, usa LiveFutbol para pronosticar todas las fases de eliminatoria.</p>
            <p>🔗 <a href="https://www.livefutbol.com/competition/co139/fifa-copa-mundial/standings-calculator/" target="_blank">Abrir Calculadora LiveFutbol</a></p>
        </div>
        <details>
            <summary><h2>📜 Reglamento y Funcionamiento</h2></summary>
            <div style="padding: 10px;">
                <p>El sistema se actualiza en tiempo real de forma automática extrayendo datos de la API oficial.</p>
                <ul>
                    <li><strong>Acierto de Signo (1X2):</strong> Otorga 1 punto base.</li>
                    <li><strong>Acierto Exacto:</strong> Otorga {html_utils.CONFIG.get("puntuacion", {}).get("acierto_exacto", 3)} puntos.</li>
                    <li><strong>Multiplicadores:</strong> En eliminatorias, si un equipo que pusiste que pasaba llega lejos en la vida real, tus puntos se multiplicarán dependiendo de la racha desde donde lo pronosticaste.</li>
                    <li><strong>Bonos de Jornada:</strong> El jugador con más aciertos exactos de cada ronda se lleva el bono "Ganador", y el peor pierde puntos.</li>
                </ul>
            </div>
        </details>
    </div>
</body>
</html>
"""
    with open(ROOT_DIR / "instrucciones.html", 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ instrucciones.html generado.")

if __name__ == "__main__":
    generar_instrucciones_html()