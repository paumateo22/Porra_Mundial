import json
from pathlib import Path

# Constante global que apunta SIEMPRE a la raíz del proyecto (PorraMundial)
ROOT_DIR = Path(__file__).resolve().parent.parent

def cargar_configuracion():
    """
    Lee y devuelve el archivo settings.json como un diccionario.
    """
    ruta_config = ROOT_DIR / "config" / "settings.json"
    
    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo de configuración en {ruta_config}")
        return None

def inicializar_estructura():
    """
    Se asegura de que todas las carpetas necesarias para guardar los datos existan.
    Si no existen, las crea automáticamente.
    """
    carpetas_necesarias = [
        ROOT_DIR / "data" / "raw" / "grupos",           # Para los JSON originales de Infobae (Fase Grupos)
        ROOT_DIR / "data" / "raw" / "eliminatorias",    # Para los JSON originales de eliminatorias
        ROOT_DIR / "data" / "processed",                # Para los archivos de fases y rachas ya calculados
        ROOT_DIR / "config"
    ]
    
    for carpeta in carpetas_necesarias:
        carpeta.mkdir(parents=True, exist_ok=True)

def guardar_json(datos, subcarpeta, nombre_archivo):
    """
    Función universal para guardar un JSON en la carpeta correcta de data/
    Ejemplo: guardar_json(mi_porra, "raw/grupos", "juan_perez.json")
    """
    ruta_destino = ROOT_DIR / "data" / subcarpeta / nombre_archivo
    
    with open(ruta_destino, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Archivo guardado con éxito en: {ruta_destino}")
    return ruta_destino