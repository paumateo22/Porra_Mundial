# 🗺️ Hoja de Ruta: Porra Mundial V2.0

## 📍 Fase 1: Cimientos y Preparación de Datos
*Antes de poder hacer temporizadores, necesitamos que el sistema sepa qué hora es en el contexto del mundial.*
* [ ] **Añadir *Timestamps*:** Modificar `jornadas.json` y/o `realidad_oficial.json` para incluir la fecha y hora exacta (ej. formato ISO `2026-06-11T16:00:00Z`) de inicio de cada partido.
* [ ] **Definir *Deadlines*:** Establecer en el `settings.json` las fechas y horas límite exactas en las que se cierra la recepción de pronósticos para cada fase (Fase de Grupos, 1/16, 1/8, etc.).

## 📍 Fase 2: Correcciones Visuales (Quick Wins)
*Limpiar los pequeños detalles que han quedado pendientes de la versión actual.*
* [ ] **Fix Multiplicadores en "Finales":** Solucionar visualmente los enlaces y atajos de las rachas/multiplicadores para la fase de finales (3º Puesto y Final), tanto en el `index.html` (calendario) como en los `dashboard.html` de los participantes.

## 📍 Fase 3: La Gran Vista "Jornadas" (El Hub Comunitario)
*Una nueva página principal para ver el pulso del torneo día a día.*
* [ ] **Estructura Base:** Crear el generador Python para la vista `jornadas.html`.
* [ ] **Navegación Sticky:** Implementar un menú superior fijo para saltar entre J1, J2, J3, 1/16, 1/8... 
* [ ] **Indicador "Jornada Actual":** Destacar visualmente en el menú en qué momento exacto del mundial nos encontramos.
* [ ] **Tarjetas de Partido Multijugador:** Para cada partido de la jornada, diseñar una tarjeta que muestre el resultado real y, debajo, una lista/cuadrícula con **lo que ha puesto cada participante**.
* [ ] **Clasificación de Jornada:** Incluir una tabla específica al final de cada jornada que muestre los puntos ganados *solo* en esa ronda.

## 📍 Fase 4: Interactividad y Temporizadores (Magia Frontend)
*Darle vida a la web con JavaScript en el lado del cliente.*
* [ ] **Motor de Tiempo (JS):** Crear un pequeño script que calcule la diferencia entre la hora actual del usuario y los *timestamps* de la Fase 1.
* [ ] **Cuenta atrás del Mundial:** Un *banner* o widget principal indicando cuánto queda para el partido inaugural.
* [ ] **Widget "Próximo Partido":** Un recuadro dinámico que detecte cuál es el partido más inminente, mostrando las banderas/nombres de los equipos y su cuenta atrás.
* [ ] **Temporizador de Partido Individual:** En las vistas (Calendario o Jornadas), mostrar "Faltan X h Y min" si el partido no ha empezado.
* [ ] **Cuenta atrás de Cierre de Pronósticos:** Un aviso de "Tienes X días/horas para enviar tus pronósticos de [Fase]".

## 📍 Fase 5: El Generador de Pronósticos (Herramienta)
*Facilitar la vida a los participantes para que te manden sus brackets.*
* [ ] **Estructura UI (Generador):** Crear un `generador.html`.
* [ ] **Lógica de Eliminatorias (JS):** Dependiendo de la fase elegida (ej. desde Cuartos), cargar los emparejamientos reales en la primera columna. Añadir *inputs* para meter los goles.
* [ ] **Simulación del Árbol (JS):** Hacer que al hacer clic en un equipo en las siguientes rondas (Semis, Final), este avance automáticamente a la siguiente caja sin necesidad de poner goles.
* [ ] **Compilador JSON (JS):** Recoger todos los datos introducidos en el árbol y darle el formato exacto del motor (`"cuartos": [...]`, `"semifinales": [...]`).
* [ ] **Descarga Directa:** Crear un botón que empaquete ese JSON y fuerce la descarga automática en el móvil/PC del usuario (`nombre_fase.json`) para que te lo manden por WhatsApp.

## 📍 Fase 6: Análisis Avanzado y "Fumadas"
*Remates finales para los muy cafeteros de los datos.*
* [ ] **Comparación de Datos:** Crear una sección o vista donde se crucen datos globales (ej. equipo más apostado para ganar, quién ha puesto la mayor goleada, etc.).
* [ ] **Buscador/Atajo de Países:** En las vistas largas, añadir una botonera rápida de países (las banderas) que haga *scroll* automático (usando anclas HTML `#`) hasta la aparición más lejana de ese equipo en las proyecciones.

## 🛡️ FASE DE ROBUSTEZ Y PLAN B
- [ ] **4. Pruebas de Resiliencia (Casos Extremos):** ¿Qué pasa si un participante se olvida de mandar su captura de octavos y falta su `.json`? Hay que asegurarse de que el motor no crashee y simplemente le asigne 0 puntos en esa jornada.
- [ ] **12. (NUEVA) Configurar el Piloto Automático (Opcional):** Añadir un disparador de tiempo (*schedule*) en el archivo YML de GitHub Actions para que los días de partido el sistema busque datos de SofaScore de forma autónoma.

---

## 🏁 FASE FINAL PRE-MUNDIAL
- [ ] **13. (NUEVA) Redactar el "Manual del Administrador":** Dejar un pequeño `.md` privado con los pasos exactos que tú como admin debes hacer durante el mes: añadir capturas OCR, cómo rellenar `premios_oficiales.json`, etc.
- [ ] **6. Limpieza de Datos de Prueba:** Vaciar las carpetas de los usuarios de prueba, borrar el `realidad_oficial.json` y dejar el sistema completamente limpio para el Día 1.
