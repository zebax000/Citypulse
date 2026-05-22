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
├── core/ # Lógica pura — sin pygame
│ ├── vehiculos.py # Física, personalidad y comportamiento
│ ├── infraestructura.py # Mundo: vías, carriles, semáforos
│ ├── simulacion.py # Orquestador de frames
│ └── controlador.py # Ciclo semafórico
├── ui/
│ └── renderer.py # Renderizado pygame desacoplado
├── data/
│ └── escenarios/ # Escenarios JSON configurables
├── assets/
│ └── sprites/ # Imágenes de vehículos
└── main.py # Punto de entrada


## Autores
- Sebastian Velasquez
- juan camilo holguin
- Cesar ramirez

Universidadd de medellin
Programacion Orientada a Objetos (POO)
  
