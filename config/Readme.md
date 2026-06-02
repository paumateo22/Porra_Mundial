# 📝 Tareas Pendientes - Porra Mundial 2026

## 🚀 Tareas Completadas
- [x] **1. Diseñar las Vistas Individuales (Perfiles de Jugador):** ¡Completado! Transformado en un dashboard con historial y la Matriz Gráfica de Desviaciones con matplotlib.
- [x] **2. Revisar la Extracción de Puntos Extra (Sorpresa/Decepción):** ¡Completado! Motor 06e funcional con varianza global.
- [x] **5. Configurar Triggers Remotos desde el Móvil:** ¡Completado! GitHub Actions configurado e integrado mediante API REST con HTTP Shortcuts.
- [x] **7. Motor de Premios Subjetivos (Google Forms):** ¡Completado!
- [x] **8. Archivo de Dependencias (requirements.txt):** ¡Completado!
- [x] **9. Aplicar Lógica de Desempates:** ¡Completado!
- [x] **10. Blindaje del Scraper de SofaScore:** ¡Completado! El 05 ahora traduce los equipos, gestiona los penaltis y evita los IDs para una búsqueda bidireccional perfecta.

---

## 🌐 FASE WEB Y FRONTEND (NUEVO)
- [ ] **11. (NUEVA) Doble Renderizado en el Script 07:** Modificar el motor `07_generador_vistas.py` para que, además de escupir los `README.md` de siempre para el repo, genere archivos `.html` con etiquetas `<style>` y estructura web real (tanto para el `index.html` del ranking como para los dashboards individuales).
- [ ] **3. Despliegue y Pruebas en GitHub Pages:** Asegurar que los enlaces entre los `.html` de la web fluyen bien y que las rutas de las imágenes de Matplotlib cargan correctamente en el frontend.

---

## 🛡️ FASE DE ROBUSTEZ Y PLAN B
- [ ] **4. Pruebas de Resiliencia (Casos Extremos):** ¿Qué pasa si un participante se olvida de mandar su captura de octavos y falta su `.json`? Hay que asegurarse de que el motor no crashee y simplemente le asigne 0 puntos en esa jornada.
- [ ] **12. (NUEVA) Configurar el Piloto Automático (Opcional):** Añadir un disparador de tiempo (*schedule*) en el archivo YML de GitHub Actions para que los días de partido el sistema busque datos de SofaScore de forma autónoma.

---

## 🏁 FASE FINAL PRE-MUNDIAL
- [ ] **13. (NUEVA) Redactar el "Manual del Administrador":** Dejar un pequeño `.md` privado con los pasos exactos que tú como admin debes hacer durante el mes: añadir capturas OCR, cómo rellenar `premios_oficiales.json`, etc.
- [ ] **6. Limpieza de Datos de Prueba:** Vaciar las carpetas de los usuarios de prueba, borrar el `realidad_oficial.json` y dejar el sistema completamente limpio para el Día 1.
