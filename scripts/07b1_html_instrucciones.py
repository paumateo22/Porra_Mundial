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
    <style>
        .rules-section {{ background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 25px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
        .rules-section h2 {{ color: var(--gold); border-bottom: 2px dashed #333; padding-bottom: 10px; margin-top: 0; text-transform: uppercase; letter-spacing: 1px; }}
        .rules-section h3 {{ color: #ddd; margin-top: 25px; margin-bottom: 10px; font-size: 1.2em; }}
        .rules-section p {{ line-height: 1.6; color: #bbb; font-size: 1.05em; margin-bottom: 15px; }}
        .rules-section ul {{ color: #bbb; line-height: 1.6; font-size: 1.05em; margin-bottom: 20px; }}
        .rules-section li {{ margin-bottom: 10px; }}
        .highlight {{ color: var(--gold); font-weight: bold; }}
        
        .action-btn {{ display: inline-block; background: var(--gold); color: black; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 5px; margin-bottom: 15px; transition: 0.2s; }}
        .action-btn:hover {{ background: #b8860b; color: white; }}
        .action-btn.secondary {{ background: #333; color: white; border: 1px solid #555; }}
        .action-btn.secondary:hover {{ background: #444; }}
    </style>
</head>
<body>
    {html_utils.get_sidebar_html("")}
    {html_utils.get_header_html("📖 Instrucciones & Registro", "Todo lo que necesitas saber para participar en la Porra Mundial 2026", "")}
    
    <div class="container" style="max-width: 900px;">
        
        <!-- SECCIÓN: INSTRUCCIONES -->
        <div class="rules-section">
            <h2>Instrucciones de Participación</h2>
            
            <p>Para participar en la Porra Mundial se tendrá que hacer una inscripción inicial. Para ello, se tendrá que realizar un primer pronóstico de todo el mundial desde fase de grupos, con resultados exactos en la fase de grupos y marcando quién avanza en las siguientes fases.</p>
            <a href="https://www.infobae.com/mundial-2026/simulador/" target="_blank" class="action-btn">1. Simulador Fase de Grupos (Infobae)</a>
            
            <p>Después se tendrá que realizar la inscripción mediante una encuesta en Google Forms en la cual pondréis vuestro nombre (el que usaréis en el resto de los pronósticos), tendréis que poner el enlace de vuestra porra inicial y contestar a las preguntas sobre premios individuales.</p>
            <a href="https://docs.google.com/forms/d/e/1FAIpQLSdd_VDG4fUwA3l9eLJa0EmKJ64NeoMYGZv6YvPE_VnrhBTYMg/viewform" target="_blank" class="action-btn">2. Formulario Oficial de Inscripción</a>
            
            <p>Una vez realizada la inscripción, se registrará vuestra participación de manera semiautomática, pudiendo ver vuestros pronósticos una vez comience la fase pronosticada.</p>
            
            <h3>Dinámica por Fases</h3>
            <p>Cada vez que concluya una fase, <span class="highlight">se deberá pronosticar de nuevo</span>. Por ejemplo, cuando termine la fase de grupos, se realizará un pronóstico partiendo desde dieciseisavos hasta la final, poniendo resultado con goles en esta primera fase, y en el resto será indicar quién pasa únicamente. Esta dinámica se irá repitiendo al finalizar cada fase hasta el final del torneo.</p>
            
            <p>Los pronósticos de eliminatorias los podréis realizar en nuestro generador interno:</p>
            <a href="generador_pronosticos.html" class="action-btn secondary">🛠️ Pronosticar Eliminatorias</a>
            
            <p>Al realizar el pronóstico, os dará la opción de descargar la porra en un archivo <strong>.json</strong>. Este archivo lo haréis llegar por WhatsApp y lo meteré en vuestras carpetas; el programa gestionará vuestros pronósticos automáticamente. Y una vez más, cuando la fase pronosticada comience, podréis ver vuestros pronósticos.</p>
            
            <h3>Gestión de Retrasos</h3>
            <p>No hay un sistema de gestión de retrasos en los pronósticos como tal. Se confía en la puntualidad de los pronósticos a pesar de tener una corta ventana de tiempo para realizarlos, pues el cambio de fase de grupos a dieciseisavos es de poco más de 12h. <span class="highlight">Si un pronóstico se entrega tarde, manualmente quitaré los partidos comenzados o terminados</span> en la fecha de entrega y no puntuarán ni aplicarán para futuros multiplicadores. Si un caso es reincidente, se estudiará una penalización mayor mediante la sustracción de puntos.</p>
        </div>

        <!-- SECCIÓN: FUNCIONAMIENTO Y PUNTUACIONES -->
        <div class="rules-section">
            <h2>Funcionamiento y Puntuaciones</h2>
            
            <h3>El Sistema de Jornadas y Partidos</h3>
            <p>El torneo se separa en <strong>12 jornadas</strong>; en cada una de ellas habrá un ganador y un perdedor que tendrán <strong>± 2 puntos</strong>. A su vez, en cada partido de la jornada se otorgará <strong>1 punto</strong> por acertar el ganador (1x2) y <strong>3 puntos extra</strong> si se clava el resultado exacto. Esta será la base de puntos en la fase de grupos.</p>
            
            <h3>Multiplicadores de Eliminatorias</h3>
            <p>En las siguientes fases incluiremos un multiplicador:</p>
            <ul>
                <li>De base contamos con un <strong>x1</strong>, pero a medida que avance el torneo, para premiar los buenos pronósticos previos, se otorgarán multiplicadores por selección.</li>
                <li>Por cada pronóstico previo realizado correctamente se otorgará <strong>+0.5</strong> al multiplicador.</li>
                <li><strong>Ejemplo Práctico:</strong> En el mejor de los casos, en la Gran Final, contaremos con pronósticos en: Fase de Grupos, Dieciseisavos, Octavos, Cuartos y Semifinales. Si en cada uno de ellos dijimos que los 2 equipos de la final llegarían a esta, sumaríamos un total de <strong>0.5 (mult.) * 5 (fases) * 2 (equipos) = 5</strong>. Sumado al base tendríamos un multiplicador <strong>x6</strong>. Si clavamos el resultado de la final serían (1 + 3) * 6 = <strong>24 puntos por un solo partido</strong>.</li>
            </ul>
            <p>La fase eliminatoria funciona exactamente igual a las jornadas en fase de grupos, aplicándoles este desglose de multiplicadores.</p>

            <h3>Balances, Premios y Bonificaciones</h3>
            <ul>
                <li><strong>Balance Fase de Grupos:</strong> Al finalizar, se otorgará 1 punto por cada país clasificado acertado y un extra de 2 puntos si se acertó su posición exacta. Pudiendo sumar un máximo de 32*1 + 32*2 = <strong>96 puntos</strong>.</li>
                <li><strong>Podio del Torneo:</strong> Al terminar el Mundial, se otorgará un extra de <strong>15 puntos</strong> por acertar el campeón desde la fase de grupos, <strong>10 puntos</strong> por el subcampeón y <strong>5 puntos</strong> por el tercer puesto.</li>
                <li><strong>Premios Individuales:</strong> Balón de Oro (15p), Guante de Oro (15p), Bota de Oro (15p), Mejor Joven (15p) y Gol del Torneo (50p).</li>
            </ul>

            <h3>Sorpresas y Decepciones (Umbral Matemático)</h3>
            <p>Al concluir el torneo podremos evaluar las sorpresas y decepciones pronosticadas por cada participante en la fase de grupos. Esto no será una definición subjetiva, será <strong>puramente matemática</strong>. Se establecerá un umbral determinado por la desviación de nuestros pronósticos respecto a la media y se comprobará lo siguiente respecto a cada Selección individualmente:</p>
            <ol style="color: #bbb; line-height: 1.6; font-size: 1.05em; margin-bottom: 20px;">
                <li>Que la <strong>Media general</strong> de pronósticos esté alejada de la realidad en una distancia mayor al umbral definido.</li>
                <li>Que el <strong>pronóstico personal</strong> esté alejado de la realidad en una mayor distancia al umbral definido para poder optar a puntuar.</li>
                <li>Que la distancia entre la realidad y tu pronóstico personal esté <strong>como mucho a 1 fase de diferencia</strong>.</li>
            </ol>
            <p>Si se cumplen estos 3 requisitos, puntuarás <strong>+10 puntos</strong> por acertar la sorpresa o la decepción. Esto será más fácil de entender al visualizarlo en tu dashboard personal, aunque no será definitivo hasta la resolución final del campeonato.</p>

            <h3>Sistema de Desempate</h3>
            <p>En el caso de darse un empate a puntos totales entre 2 o más participantes, se resolverá siguiendo este orden estricto:</p>
            <ol style="color: #bbb; line-height: 1.6; font-size: 1.05em; margin-bottom: 20px;">
                <li>Quien tenga más aciertos de signo (1X2).</li>
                <li>Quien tenga más aciertos exactos.</li>
                <li>Quien tenga más jornadas ganadas.</li>
                <li>Si el empate persiste, se otorga el mismo puesto a ambos.</li>
            </ol>
        </div>
        
        <p style="text-align:center; color:gray; font-size:0.9em; margin-top:40px; border-top: 1px solid #333; padding-top: 20px;">
            Desarrollado por Pau Mateo Lillo.
        </p>

    </div>
</body>
</html>
"""
    with open(ROOT_DIR / "instrucciones.html", 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ instrucciones.html generado.")

if __name__ == "__main__":
    generar_instrucciones_html()