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
