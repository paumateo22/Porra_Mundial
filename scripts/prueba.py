import sys
import cv2
import easyocr
import os
import glob
from pathlib import Path

# Conectar con la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

print("🤖 Cargando modelo de EasyOCR para depuración...")
reader = easyocr.Reader(['es'], gpu=False)

def guardar_recortes_depuracion(ruta_imagen):
    img_original = cv2.imread(str(ruta_imagen))
    if img_original is None:
        print(f"❌ No se pudo abrir la imagen: {ruta_imagen.name}")
        return
    
    carpeta_prueba = ROOT_DIR / "prueba" / ruta_imagen.stem
    carpeta_prueba.mkdir(parents=True, exist_ok=True)
    
    # 1. Hachazo inicial de 173px (Elimina fecha y hora)
    offset_x = 173
    img_recortada = img_original[:, offset_x:]
    ancho = img_recortada.shape[1]
    
    cv2.imwrite(str(carpeta_prueba / "00_base_recortada.png"), img_recortada)
    print(f"\n🔍 Generando muestras de '{ruta_imagen.name}' en: {carpeta_prueba.relative_to(ROOT_DIR)}")
    
    # Crear una copia para dibujar el mapa visual de cortes
    img_debug = img_recortada.copy()
    
    # Leer texto solo para encontrar las alturas (Y) de las filas
    resultados = reader.readtext(img_recortada)
    
    elementos = []
    palabras_basura = ['calcular', 'reajustar', 'dieciseisavos', 'octavos', 'cuartos', 'semifinales', 'final', 'partido', 'lugar', 'de']
    
    for bbox, texto, conf in resultados:
        y_centro = (bbox[0][1] + bbox[2][1]) / 2
        texto = texto.strip().lower()
        
        if any(basura in texto for basura in palabras_basura):
            continue
        elementos.append({'y': y_centro})
        
    if not elementos: 
        print(f"⚠️ No se detectaron elementos útiles en {ruta_imagen.name}")
        return
        
    elementos.sort(key=lambda item: item['y'])
    filas = []
    fila_actual = []
    y_referencia = None
    
    for el in elementos:
        if y_referencia is None or abs(el['y'] - y_referencia) < 15:
            fila_actual.append(el)
        else:
            filas.append(fila_actual)
            fila_actual = [el]
        y_referencia = fila_actual[0]['y']
    if fila_actual: filas.append(fila_actual)
    
    # --- CONFIGURACIÓN DE COORDENADAS X ---
    # Variables extraídas para facilitar futuros reajustes
    x_loc_ini, x_loc_fin = 0, 170
    x_gol_loc_ini, x_gol_loc_fin = 200, 230
    x_gol_vis_ini, x_gol_vis_fin = 245, 275
    x_vis_ini, x_vis_fin = 300, ancho

    for idx, fila in enumerate(filas, 1):
        y_centro_fila = sum(el['y'] for el in fila) / len(fila)
        y1 = int(max(0, y_centro_fila - 15))
        y2 = int(min(img_recortada.shape[0], y_centro_fila + 15))
        
        # --- LOS 4 SEGMENTOS EXACTOS ---
        recorte_nombre_loc = img_recortada[y1:y2, x_loc_ini:x_loc_fin]
        recorte_gol_loc = img_recortada[y1:y2, x_gol_loc_ini:x_gol_loc_fin]
        recorte_gol_vis = img_recortada[y1:y2, x_gol_vis_ini:x_gol_vis_fin]
        recorte_nombre_vis = img_recortada[y1:y2, x_vis_ini:x_vis_fin]
        
        # Guardar las 4 piezas de la fila
        cv2.imwrite(str(carpeta_prueba / f"fila_{idx:02d}_01_nombre_LOC.png"), recorte_nombre_loc)
        cv2.imwrite(str(carpeta_prueba / f"fila_{idx:02d}_02_gol_LOC.png"), recorte_gol_loc)
        cv2.imwrite(str(carpeta_prueba / f"fila_{idx:02d}_03_gol_VIS.png"), recorte_gol_vis)
        cv2.imwrite(str(carpeta_prueba / f"fila_{idx:02d}_04_nombre_VIS.png"), recorte_nombre_vis)
        
        # --- DIBUJAR EN EL MAPA DE DIAGNÓSTICO ---
        # Nombres en Azul, Goles en Verde
        cv2.rectangle(img_debug, (x_loc_ini, y1), (x_loc_fin, y2), (255, 0, 0), 2)
        cv2.rectangle(img_debug, (x_gol_loc_ini, y1), (x_gol_loc_fin, y2), (0, 255, 0), 2)
        cv2.rectangle(img_debug, (x_gol_vis_ini, y1), (x_gol_vis_fin, y2), (0, 255, 0), 2)
        cv2.rectangle(img_debug, (x_vis_ini, y1), (x_vis_fin, y2), (255, 0, 0), 2)
    
    # Guardar el mapa general
    cv2.imwrite(str(carpeta_prueba / "00_mapa_cortes.png"), img_debug)
    print(f"✅ ¡Archivos y mapa visual de diagnóstico generados!")

def escanear_imagenes_participantes(fase_origen="dieciseisavos"):
    dir_participantes = ROOT_DIR / "participantes"
    if not dir_participantes.exists(): 
        print("❌ No se encontró la carpeta 'participantes'.")
        return
        
    for p_folder in dir_participantes.iterdir():
        if p_folder.is_dir():
            ruta_fase = p_folder / "pronosticos" / "eliminatorias" / fase_origen
            if ruta_fase.exists():
                for img_path in glob.glob(str(ruta_fase / "*.png")):
                    guardar_recortes_depuracion(Path(img_path))

if __name__ == "__main__":
    escanear_imagenes_participantes("dieciseisavos")