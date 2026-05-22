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
| Capa | Archivo | Responsabilidad |
|------|---------|-----------------|
| `core/` | `vehiculos.py` | Física, personalidad y comportamiento de vehículos |
| `core/` | `infraestructura.py` | Mundo: vías, carriles, semáforos, escenarios |
| `core/` | `simulacion.py` | Orquestador de frames: spawn, física, métricas |
| `core/` | `controlador.py` | Ciclo semafórico VERDE → AMARILLO → ROJO |
| `ui/` | `renderer.py` | Renderizado pygame desacoplado |
| `ui/` | `debug.py` | Overlay de debug: hitboxes, frente/cola, líneas de pare |
| `data/` | `escenario_1.json` | Intersección simple |
| `data/` | `escenario_2.json` | Intersección con carriles múltiples |
| `data/` | `escenario_3.json` | Doble intersección con coord_pare múltiple |
| raíz | `main.py` | Punto de entrada: loop pygame + gestor simulación |


| Tecla | Acción |
|-------|--------|
| `1` `2` `3` | Cambiar escenario |
| `Space` | Pausar / reanudar |
| `+` / `-` | Acelerar / reducir velocidad de simulación |
| `R` | Recargar escenario actual |
| `D` | Activar / desactivar modo debug |
| `ESC` | Salir 

## Autores
- Sebastian Velasquez
- juan camilo holguin
- Cesar ramirez

Universidadd de medellin
Programacion Orientada a Objetos (POO)
  
