# 🚦 CityPulse

**Simulador de Movilidad Urbana basado en POO con visualización en tiempo real**

---

##  Descripción

CityPulse es una herramienta de simulación de tráfico urbano desarrollada en Python utilizando Pygame y Programación Orientada a Objetos (POO).

Permite modelar escenarios de tráfico con múltiples tipos de vehículos, intersecciones controladas por semáforos y métricas en tiempo real, con el objetivo de analizar el comportamiento del flujo vehicular bajo diferentes configuraciones.

---

##  Objetivo del Proyecto

Simular y analizar cómo variables como:

* tiempos de semáforos
* densidad vehicular
* tipo de vehículos
* estructura vial

afectan el flujo de tráfico en una intersección urbana.

 Importante:
Este sistema **no pretende predecir tráfico real**, sino servir como herramienta experimental para estudiar dinámicas de movilidad.

---

##  Enfoque Técnico

El proyecto está construido bajo principios de:

* Programación Orientada a Objetos (POO)
* Separación de responsabilidades
* Simulación por escenarios configurables (JSON)
* Visualización en tiempo real con Pygame

---

##  Arquitectura del Proyecto

```
cityPulse/
├── assets/
│   └── sprites/
├── core/
│   ├── infraestructura.py
│   ├── logica.py
│   └── vehiculos.py
├── data/
│   └── escenarios/
│       ├── escenario_1.json
│       ├── escenario_2.json
│       └── escenario_3.json
├── main.py
└── requirements.txt
```

---

##  Componentes Principales

###  Infraestructura (`infraestructura.py`)

Define el entorno de simulación:

* Vías
* Carriles
* Semáforos
* Cebras
* Líneas de pare
* Controlador de cruce (fases semafóricas)
* Escenarios cargados desde JSON

---

###  Lógica (`logica.py`)

Gestiona la simulación:

* Generación automática de vehículos
* Control del flujo vehicular
* Cambio de escenarios
* Métricas en tiempo real
* Panel de información

---

###  Vehículos (`vehiculos.py`)

Modela el comportamiento dinámico:

* Clase base `Vehiculo`
* Subclases:

  * Automóvil
  * Moto
  * Bus
  * Camión

Incluye:

* Aceleración y frenado
* Distancia de seguridad
* Seguimiento de vehículos
* Respeto de semáforos
* Variación de sprites

---

##  Sistema de Semáforos

El sistema se basa en fases estrictas:

1. HORIZONTAL_VERDE
2. HORIZONTAL_AMARILLO
3. VERTICAL_VERDE
4. VERTICAL_AMARILLO

✔ Nunca hay verde simultáneo
✔ Existe transición con amarillo
✔ Cada grupo tiene su propio contador

---

##  Comportamiento del Tráfico

* En **verde** → los vehículos avanzan
* En **amarillo** → desaceleran
* En **rojo** → se detienen antes de la línea de pare

Regla crítica:

> Si un vehículo ya cruzó la línea de pare, **NO se detiene**, incluso si el semáforo cambia a rojo.

---

##  Escenarios (JSON)

Los escenarios se definen en archivos `.json`, lo que permite:

* modificar la simulación sin tocar el código
* crear nuevos entornos fácilmente
* probar diferentes configuraciones

Cada escenario incluye:

* vías
* carriles
* semáforos
* líneas de pare
* cebras
* configuración del controlador

---

## 📊 Métricas del Sistema

Durante la simulación se muestran:

* Vehículos activos
* Vehículos generados
* Vehículos que salieron
* Velocidad promedio
* Tamaño de cola

---

##  Controles

* `1 / 2 / 3` → cambiar escenario
* `ESPACIO` → pausar / reanudar
* `+ / -` → velocidad de simulación
* `R` → recargar escenarios
* `ESC` → salir

---

##  Ejecución

1. Instalar dependencias:

```bash
pip install pygame
```

2. Ejecutar:

```bash
python main.py
```

---

## 🚀 Posibles Mejoras

* Semáforos inteligentes (adaptativos)
* Eventos: accidentes, clima
* Giros en intersecciones
* Editor gráfico de escenarios
* Métricas avanzadas

---

##  Conclusión

CityPulse permite experimentar con el comportamiento del tráfico urbano en un entorno controlado, facilitando el análisis de variables clave sin depender de datos reales.

Es una herramienta de simulación, no un sistema predictivo.

---
