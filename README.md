CityPulse — Simulador Urbano de Tráfico

Simulador de tráfico urbano orientado a objetos desarrollado en Python + pygame.

## Características
- Múltiples escenarios configurables via JSON
- Semáforos con control de grupos H/V
- Física de tráfico realista
- Comportamiento humano: agresividad, reacción, tolerancia al amarillo
- Doble intersección con coord_pare múltiple
- Arquitectura desacoplada (core / ui / data)

## Requisitos
- Python 3.10+
- pygame 2.5+

## Instalación
```bash
git clone https://github.com/tuusuario/CityPulse.git
cd CityPulse
pip install -r requirements.txt
python main.py
```

## Escenarios
| Escenario | Descripción |
|-----------|-------------|
| 1 | Intersección simple |
| 2 | Intersección con múltiples carriles |
| 3 | Doble intersección |

## Arquitectura
CityPulse/
├── core/
│   ├── vehiculos.py        # Física, personalidad y comportamiento de vehículos
│   ├── infraestructura.py  # Mundo: vías, carriles, semáforos, escenarios
│   ├── simulacion.py       # Orquestador de frames: spawn, física, métricas
│   └── controlador.py      # Ciclo semafórico VERDE → AMARILLO → ROJO
├── ui/
│   ├── renderer.py         # Renderizado pygame desacoplado
│   └── debug.py            # Overlay de debug: hitboxes, frente/cola, líneas de pare
├── data/
│   └── escenarios/
│       ├── escenario_1.json  # Intersección simple
│       ├── escenario_2.json  # Intersección con carriles múltiples
│       └── escenario_3.json  # Doble intersección con coord_pare múltiple
├── assets/
│   └── sprites/
│       ├── v1.png
│       ├── v2.png
│       ├── v3.png
│       ├── m1.png
│       ├── m2.png
│       ├── m3.png
│       ├── b1.png
│       ├── c1.png
│       └── c2.png
├── main.py                 # Punto de entrada: loop pygame + gestor simulación
├── .gitignore
├── README.md
└── requirements.txt


## Autores
- Sebastian Velasquez
- juan camilo holguin
- Cesar ramirez

Universidadd de medellin
Programacion Orientada a Objetos (POO)
  
