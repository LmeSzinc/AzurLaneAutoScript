**| [English](README_en.md) | [简体中文](README.md) | Español |**

# StarRailCopilot
Star Rail Copilot, un bot para Honkai: Star Rail, basado en la siguiente generación del framework ALAS.

![gui](/doc/README.assets/gui_es.png)

## Características

- **Mazmorras**: Mazmorras, y mazmorras en eventos de doble recompensa (materiales de XP de personaje, de conos de luz, rastros, ascensión, artefactos...)
- **Recompensas diarias**: Se completan las misiones de actividad diarias, la misión diaria, las misiones de Honor Anónimo...
- **Farmeo automático AFK**: El bot lo hace todo de manera automática, abre los emuladores, completa las misiones y realiza las tareas diarias.

## Instalación [![](https://img.shields.io/github/downloads/LmeSzinc/StarRailCopilot/total?color=4e4c97)](https://github.com/LmeSzinc/StarRailCopilot/releases)
Dirígete a la [Guía de Instalación](https://github.com/LmeSzinc/StarRailCopilot/wiki/Installation_cn) para consultar cómo hacer la instalación automática, el manual de uso, etc.

> **¿Por qué usar un emulador?** Si ejecutas el bot en la versión de escritorio, la ventana debe de estar al frente. Imagino que no quieres quedarte esperando sin poder mover el ratón y teclado mientras el bot se ejecuta. Por esto se usa emulador.
> **¿Cómo es el rendimiento?** Con un 8700k + 1080 Ti y usando el emulador MuMu12 con los gráficos en Muy Alto, se obtienen 40 FPS. No debería ser un problema ejecutar el juego en gráficos al máximo y tener 60 FPS si tienes un PC más nuevo.


## Desarrollo
Discord: https://discord.gg/aJkt3mKDEr | Grupo de QQ: 752620927

- [Seguimiento del Minimapa](https://github.com/LmeSzinc/StarRailCopilot/wiki/MinimapTracking)
- Documentación para desarrolladores (el menú está en la barra lateral): [Wiki de ALAS](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/1.-Start) (en Chino). Sin embargo, hay un montón de código nuevo, por lo que es recomendado leer el código fuente y el historial de commits.
- Roadmap del desarrollo: [#10](https://github.com/LmeSzinc/StarRailCopilot/issues/10). Los pull requests son bienvenidos. Simplemente, elige la parte en la que estás interesado trabajar.

> **¿Cómo añadir nuevos idiomas o servidores?** Si necesitas actualizar los recursos del bot, échale un vistazo a ["Añadiendo un Botón" en la documentación para desarrolladores](https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/4.1.-Detection-objects#%E6%B7%BB%E5%8A%A0%E4%B8%80%E4%B8%AA-button).

## Acerca de ALAS
SRC está basado en un bot de Azur Lane ([AzurLaneAutoScript](https://github.com/LmeSzinc/AzurLaneAutoScript)). Tras 3 años de desarrollo, se ha alcanzado un alto grado de completitud en ALAS, pero también se ha acumulado una gran cantidad de código basura que es difícil cambiar. Esperamos arreglar dichos problemas en este nuevo proyecto.

- Actualizar el OCR. ALAS ha entrenado múltiples modelos en cnocr==1.2.2, pero la dependencia [mxnet](https://github.com/apache/mxnet) ya no está activa. El aprendizaje automático se está desarrollando muy rápido, y la velocidad y precisión de los nuevos modelos destroza a los antiguos.
- Se han convertido los ficheros de configuración en modelos [pydantic](https://github.com/pydantic/pydantic). Desde que el concepto de tarea y planificador fueron añadidos, el número de ajustes de usuario se ha incrementado enormemente. ALAS ha construido un generador de código para implementar la lectura y actualización de ajustes. Pydantic permitirá hacer esto de forma más elegante.
- Mejor gestión de los recursos: button_extract ayuda a ALAS a mantener fácilmente +4000 imágenes de plantilla, pero tiene serios problemas de rendimiento, y el resultado de soportar varios servidores también ha provocado una gran cantidad de logs sin significado.
- Se ha reducido el acoplamiento a Azur Lane. El framework ALAS y ALAS GUI tienen capacidad de tener interfaz con otros juegos pero el acabado plugin [MAA](https://github.com/MaaAssistantArknights/MaaAssistantArknights) para Arknights y el plugin en desarrollo [fgo-py](https: //github.com/hgjazhgj/FGO-py) han encontrado serios problemas de acoplamiento entre ALAS y el juego Azur Lane.
