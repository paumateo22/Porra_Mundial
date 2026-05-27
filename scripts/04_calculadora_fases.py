import sys
import json
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

def calcular_fases_numericas(nombre_jugador):
    """
    Lee el pronóstico de un jugador y genera un diccionario estructurado 
    con el nivel máximo alcanzado por cada selección (del 0 al 6).
    """
    print(f"🧮 Calculando fases numéricas para: {nombre_jugador.upper()}")
    
    # Adaptado a la nueva estructura de carpetas
    ruta_pronostico = ROOT_DIR / "participantes" / nombre_jugador / "pronosticos" / "grupos.json"
    
    # (Si en tu caso tienes las eliminatorias en un archivo separado como dieciseisavos.json, 
    # tendrías que cargar ambos y fusionarlos aquí. Asumimos que están en grupos.json como en tu código original).
    if not ruta_pronostico.exists():
        print(f"  ❌ Error: No se encontró pronóstico para {nombre_jugador} en {ruta_pronostico}")
        return False
        
    with open(ruta_pronostico, 'r', encoding='utf-8') as f:
        datos_porra = json.load(f)
        
    fases_numericas = {}
    
    # 0. Nivel 0: Todos los equipos de la Fase de Grupos
    for grupo, partidos in datos_porra.get("fase_grupos", {}).items():
        for partido in partidos:
            fases_numericas[partido["local"]] = 0
            fases_numericas[partido["visitante"]] = 0
            
    # 1. Nivel 1: Los clasificados a Dieciseisavos
    for equipo in datos_porra.get("clasificados_a_dieciseisavos", []):
        fases_numericas[equipo] = 1
        
    # 2. Nivel 2: Los que pasan a Octavos
    for partido in datos_porra.get("eliminatorias", {}).get("dieciseisavos", []):
        if partido.get("pasa") in fases_numericas:
            fases_numericas[partido.get("pasa")] = 2
            
    # 3. Nivel 3: Los que pasan a Cuartos
    for partido in datos_porra.get("eliminatorias", {}).get("octavos", []):
        if partido.get("pasa") in fases_numericas:
            fases_numericas[partido.get("pasa")] = 3
            
    # 4. Nivel 4: Los que pasan a Semifinales 
    for partido in datos_porra.get("eliminatorias", {}).get("cuartos", []):
        if partido.get("pasa") in fases_numericas:
            fases_numericas[partido.get("pasa")] = 4
            
    # 5. Nivel 5: Los finalistas (1º y 2º)
    final_partidos = datos_porra.get("eliminatorias", {}).get("final", [])
    if final_partidos:
        partido_final = final_partidos[0]
        if partido_final["local"] in fases_numericas:
            fases_numericas[partido_final["local"]] = 5
        if partido_final["visitante"] in fases_numericas:
            fases_numericas[partido_final["visitante"]] = 5
            
        # 6. Nivel 6: EL CAMPEÓN DEL MUNDO
        ganador_final = partido_final.get("pasa")
        if ganador_final and ganador_final in fases_numericas:
            fases_numericas[ganador_final] = 6

    # Estructuramos el archivo de salida
    datos_procesados = {
        "jugador": nombre_jugador,
        "niveles_equipos": fases_numericas
    }
    
    # Guardamos en la propia carpeta del jugador
    ruta_guardado = ROOT_DIR / "participantes" / nombre_jugador / "pronosticos" / "niveles.json"
    
    with open(ruta_guardado, 'w', encoding='utf-8') as f:
        json.dump(datos_procesados, f, ensure_ascii=False, indent=4)
        
    print(f"  ✅ Niveles guardados en: niveles.json")
    return True

if __name__ == "__main__":
    print("--- ⚙️ INICIANDO CÁLCULO DE NIVELES MASIVO ---")
    
    dir_participantes = ROOT_DIR / "participantes"
    if not dir_participantes.exists():
        print("❌ No existe la carpeta de participantes.")
        sys.exit()
        
    # Bucle automático para todos los jugadores
    jugadores = [p.name for p in dir_participantes.iterdir() if p.is_dir()]
    
    for jugador in jugadores:
        calcular_fases_numericas(jugador)
        
    print("\n🏁 Proceso completado para todos los participantes.")