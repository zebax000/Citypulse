import os
import random
from core.infraestructura import cargar_escenarios
from core.vehiculos import TIPOS_VEHICULO, ESPACIO_SPAWN


class GestorSimulacion:
    """
    Orquestador puro. No dibuja nada.
    Coordina: escenarios, semáforos, spawn, física, métricas.
    """

    def __init__(self):
        self.escenarios = cargar_escenarios(os.path.join("data", "escenarios"))
        self.indice     = 0
        self.escenario  = self.escenarios[self.indice]

        self.pausado       = False
        self.escala_tiempo = 1.0
        self._id           = 0   # contador global de IDs de vehículos

        self.metricas = {
            "activos":            0,
            "generados":          0,
            "salidos":            0,
            "velocidad_promedio": 0.0,
            "cola_total":         0,
        }

    # ── controles de usuario ───────────────────────────────────────────────

    def pausar_reanudar(self):
        self.pausado = not self.pausado

    def ajustar_escala(self, nueva):
        self.escala_tiempo = max(0.25, min(4.0, nueva))

    def cambiar_escenario(self, indice):
        if 0 <= indice < len(self.escenarios):
            self.indice    = indice
            self.escenario = self.escenarios[indice]
            self.escenario.reiniciar()
            # Resetear métricas al cambiar escenario
            self.metricas = {k: (0 if isinstance(v, int) else 0.0)
                             for k, v in self.metricas.items()}

    def recargar_escenarios(self):
        nombre_actual  = self.escenario.nombre
        self.escenarios = cargar_escenarios(os.path.join("data", "escenarios"))
        for i, esc in enumerate(self.escenarios):
            if esc.nombre == nombre_actual:
                self.indice    = i
                self.escenario = esc
                return
        self.indice    = 0
        self.escenario = self.escenarios[0]

    # ── loop principal ─────────────────────────────────────────────────────

    def actualizar(self, dt_real):
        if self.pausado:
            return
        dt = min(dt_real, 0.05) * self.escala_tiempo
        self.escenario.actualizar(dt)       # avanza el controlador semafórico
        self._generar_vehiculos(dt)
        self._actualizar_vehiculos(dt)

    # ── spawn ──────────────────────────────────────────────────────────────

    def _elegir_tipo(self, mezcla):
        """Selección aleatoria ponderada por probabilidades del carril."""
        r, acumulado = random.random(), 0.0
        for tipo, prob in mezcla.items():
            acumulado += prob
            if r <= acumulado:
                return tipo
        return list(mezcla.keys())[-1]

    def _generar_vehiculos(self, dt):
        for carril in self.escenario.carriles:
            carril.temporizador_spawn += dt
            if carril.temporizador_spawn < carril.spawn_intervalo:
                continue

            carril.temporizador_spawn = 0.0

            # Verificar espacio: el vehículo con menor progreso debe haber avanzado
            if carril.vehiculos:
                ultimo = min(carril.vehiculos, key=lambda v: v.progreso)
                if ultimo.cola_progreso() < ESPACIO_SPAWN:
                    continue   # no hay espacio, skip este ciclo

            tipo     = self._elegir_tipo(carril.mezcla_vehiculos)
            vehiculo = TIPOS_VEHICULO[tipo](f"V{self._id}", carril)
            self._id += 1
            carril.vehiculos.append(vehiculo)
            self.metricas["generados"] += 1

    # ── actualización de vehículos ─────────────────────────────────────────

    def _actualizar_vehiculos(self, dt):
        velocidades = []
        cola_total  = 0

        for carril in self.escenario.carriles:
            estado = self.escenario.estado_semaforo_para_carril(carril)

            # Ordenar: mayor progreso primero (índice 0 = vehículo más adelantado)
            carril.vehiculos.sort(key=lambda v: v.progreso, reverse=True)

            for i, v in enumerate(carril.vehiculos):
                frente = carril.vehiculos[i - 1] if i > 0 else None
                v.actualizar(dt, frente, estado)
                velocidades.append(v.velocidad_actual)

                # Contabilizar en cola: detenido en rojo antes de la línea
                if (estado == "ROJO"
                        and not v.ya_cruzo_linea_de_pare()
                        and v.velocidad_actual < 1.0):
                    cola_total += 1

            # Separar salidos ANTES de filtrar para contarlos correctamente
            salidos = [v for v in carril.vehiculos if v.salio_del_mapa()]
            self.metricas["salidos"] += len(salidos)
            carril.vehiculos = [v for v in carril.vehiculos if not v.salio_del_mapa()]

        # Actualizar métricas globales
        self.metricas["activos"]            = sum(len(c.vehiculos) for c in self.escenario.carriles)
        self.metricas["cola_total"]         = cola_total
        self.metricas["velocidad_promedio"] = (
            sum(velocidades) / len(velocidades) if velocidades else 0.0
        )
