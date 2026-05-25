# CityPulse — Simulador Urbano de Tráfico

Simulador de tráfico urbano orientado a objetos desarrollado en Python + pygame.

## Características
- Múltiples escenarios configurables via JSON
- Semáforos con control de grupos H/V
- Física de tráfico realista con cambio de carriles animado
- Comportamiento humano: agresividad, reacción, tolerancia al amarillo
- Doble intersección con `coord_pare` múltiple
- Vehículos prioritarios (Ambulancia, Policía) con aura visual y luces intermitentes
- Sistema de eventos dinámicos: hora pico, lluvia, niebla, accidente, noche, fiesta
- Métricas en tiempo real: congestión, velocidad promedio, cola, tiempo de espera
- Sistema de debug integrado con overlay, historial de errores y métricas de rendimiento
- Arquitectura desacoplada (core / ui / data) — todo el dibujo centralizado en `renderer.py`

## Requisitos
- Python 3.10+
- pygame 2.5+

## Instalación
```bash
git clone https://github.com/zebax000/CityPulse.git
cd CityPulse
pip install -r requirements.txt
python main.py
```

## Escenarios
| Escenario | Descripción |
|-----------|-------------|
| 1 | Intersección simple — 2 carriles |
| 2 | Intersección ampliada — 6 carriles por sentido |
| 3 | Doble intersección con `coord_pare` múltiple |

## Arquitectura
| Capa | Archivo | Responsabilidad |
|------|---------|-----------------|
| `core/` | `vehiculos.py` | Física, personalidad, FSM de cambio de carril y tipos de vehículo |
| `core/` | `infraestructura.py` | Mundo: vías, carriles, semáforos, escenarios, carga de JSON |
| `core/` | `simulacion.py` | Orquestador de frames: spawn, física, métricas y debug integrado |
| `core/` | `controlador.py` | Ciclo semafórico VERDE → AMARILLO → ROJO con box blocking |
| `core/` | `eventos.py` | Lógica de eventos dinámicos (sin pygame — solo estado y datos) |
| `ui/` | `renderer.py` | Todo el renderizado pygame: escenario, vehículos, overlays de eventos, panel, debug |
| `ui/` | `debug.py` | Overlay de debug: hitboxes, frente/cola, líneas de pare |
| `data/escenarios/` | `escenario_1.json` | Intersección simple |
| `data/escenarios/` | `escenario_2.json` | Intersección con carriles múltiples |
| `data/escenarios/` | `escenario_3.json` | Doble intersección |
| raíz | `main.py` | Punto de entrada: loop pygame + gestor simulación |

## Eventos dinámicos
| Tecla | Evento | Efecto |
|-------|--------|--------|
| `T` | Hora pico | Aumenta spawn y cambia mezcla vehicular |
| `Y` | Lluvia | Overlay de gotas, charcos y velo azul |
| `I` | Niebla | Overlay semitransparente, conductores más cautelosos |
| `U` | Accidente | Bloquea un carril aleatorio |
| `O` | Noche | Oscurece la escena, activa faros de vehículos |

## Teclas generales
| Tecla | Acción |
|-------|--------|
| `1` `2` `3` | Cambiar escenario |
| `Space` | Pausar / reanudar |
| `+` / `-` | Acelerar / reducir velocidad de simulación |
| `R` | Recargar escenario actual |
| `F1` | Activar / desactivar modo debug |
| `ESC` | Salir |

## Autores
- Sebastian Velasquez
- Juan Camilo Holguín
- César Ramírez

Universidad de Medellín  
Programación Orientada a Objetos (POO)
