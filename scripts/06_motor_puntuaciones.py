import sys
from pathlib import Path

# Conectar con la raíz y utilidades
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from utils.helpers import cargar_configuracion

# Cargamos los "interruptores" y puntos al arrancar el motor
CONFIG = cargar_configuracion()

def calcular_puntos_partido(pronostico_local, pronostico_visitante, 
                            real_local, real_visitante, 
                            fases_previas_acertadas_local=0, 
                            fases_previas_acertadas_visitante=0):
    """
    (MICRO) Calcula los puntos de UN partido para UN jugador.
    """
    puntos_base = 0
    acierto_puro = False # Variable extra para saber si acertó el 1X2 (útil para la jornada)
    
    if CONFIG["habilitadores"]["acierto_1x2"] == 0:
        return 0, False

    signo_pronostico = "1" if pronostico_local > pronostico_visitante else ("2" if pronostico_visitante > pronostico_local else "X")
    signo_real = "1" if real_local > real_visitante else ("2" if real_visitante > real_local else "X")
    
    if signo_pronostico == signo_real:
        puntos_base += CONFIG["puntuaciones"]["partidos"]["acierto_1x2"]
        acierto_puro = True

    if CONFIG["habilitadores"]["acierto_exacto"] == 1 and acierto_puro:
        if pronostico_local == real_local and pronostico_visitante == real_visitante:
            puntos_base += CONFIG["puntuaciones"]["partidos"]["acierto_exacto"]

    multiplicador_total = CONFIG["multiplicadores"]["base"]
    
    if CONFIG["habilitadores"]["racha_eliminatorias"] == 1:
        inc_racha = CONFIG["multiplicadores"]["incremento_racha_por_fase"]
        multiplicador_total += (fases_previas_acertadas_local * inc_racha)
        multiplicador_total += (fases_previas_acertadas_visitante * inc_racha)

    puntos_finales = puntos_base * multiplicador_total
    
    # Devolvemos los puntos totales Y un booleano diciendo si acertó el signo o no
    return puntos_finales, acierto_puro


def evaluar_jornada(diccionario_aciertos_jugadores):
    """
    (MACRO) Recibe un diccionario con los aciertos que ha tenido cada jugador 
    en una jornada y aplica el bono de ganador/perdedor.
    Ejemplo de entrada: {"Juan": 5, "Maria": 5, "Pedro": 5, "Luis": 5}
    """
    # Inicializamos a todos con 0 puntos extra por defecto
    bonos_jornada = {jugador: 0 for jugador in diccionario_aciertos_jugadores}

    if CONFIG["habilitadores"]["ganador_perdedor_jornada"] == 0:
        return bonos_jornada # Si el interruptor está apagado, devolvemos 0 para todos

    # Prevenir que pete si le pasamos una lista vacía por error
    if not diccionario_aciertos_jugadores:
        return bonos_jornada

    # Encontrar el valor máximo y mínimo de aciertos
    max_aciertos = max(diccionario_aciertos_jugadores.values())
    min_aciertos = min(diccionario_aciertos_jugadores.values())
    
    # --- LA REGLA DEL EMPATE MASIVO ---
    if max_aciertos == min_aciertos:
        print(f"🤝 ¡Empate masivo a {max_aciertos} aciertos! No hay ganador ni perdedor en esta jornada.")
        return bonos_jornada
    
    puntos_ganador = CONFIG["puntuaciones"]["jornadas"]["ganador"]
    puntos_perdedor = CONFIG["puntuaciones"]["jornadas"]["perdedor"]
    
    for jugador, aciertos in diccionario_aciertos_jugadores.items():
        if aciertos == max_aciertos:
            bonos_jornada[jugador] += puntos_ganador
            print(f"🥇 {jugador} gana la jornada con {aciertos} aciertos! (+{puntos_ganador} pts)")
            
        if aciertos == min_aciertos:
            bonos_jornada[jugador] += puntos_perdedor
            print(f"📉 {jugador} pierde la jornada con {aciertos} aciertos... ({puntos_perdedor} pts)")
            
    return bonos_jornada

# --- Bloque de prueba ---
if __name__ == "__main__":
    print("--- PRUEBA DE EVALUACIÓN DE JORNADA ---")
    
    # Imaginemos que ya hemos pasado los 10 partidos de la jornada por la micro-calculadora
    # y hemos sumado los "acierto_puro = True" de cada uno:
    resultados_jornada_1 = {
        "Juan": 5,   # Acertó 8 de 10
        "Maria": 5,  # Acertó 5 de 10
        "Pedro": 5,  # Acertó 5 de 10
        "Luis": 5    # Acertó 2 de 10
    }
    
    bonos_aplicar = evaluar_jornada(resultados_jornada_1)
    # Resultado esperado: Juan +2, Luis -2. Maria y Pedro se quedan a 0 extra.