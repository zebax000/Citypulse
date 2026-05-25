# core/simulacion.py
import os
import math
import random
import json
import time
import collections
from core.infraestructura import cargar_escenarios
from core.eventos import GestorEventos
from core.vehiculos import TIPOS_VEHICULO, ESPACIO_SPAWN


# ── debug ──────────────────────────────────────────────────────────────────
DEBUG_ACTIVO            = True
DEBUG_OVERLAY           = True
DEBUG_STRICT            = False
DEBUG_PERIODO           = 60
DEBUG_PREPARANDO_MAX    = 3.0
DEBUG_OFFSET_MAX_FRAMES = 90

_ESTADOS_VALIDOS  = {"LIBRE", "PREPARANDO", "CAMBIANDO"}
_d_frame_actual   = 0
_d_errores_frame  = []
_d_historial      = collections.deque(maxlen=200)
_d_contadores     = collections.defaultdict(int)
_d_tiempos_estado = {}
_d_offset_prev    = {}
_d_update_frame   = {}
_d_perf           = collections.defaultdict(float)


def _d_registrar(msg):
    _d_errores_frame.append(msg)
    _d_historial.append(msg)
    tipo = (msg.split("]")[0] + "]") if "]" in msg else "UNKNOWN"
    _d_contadores[tipo] += 1
    if DEBUG_STRICT:
        raise AssertionError(msg)

def debug_iniciar_frame(frame_n):
    global _d_frame_actual, _d_errores_frame
    _d_frame_actual  = frame_n
    _d_errores_frame = []

def debug_finalizar_frame():
    if _d_errores_frame:
        _d_contadores["frames_con_error"] += 1

def debug_errores_frame():  return list(_d_errores_frame)
def debug_historial(n=20):  return list(_d_historial)[-n:]
def debug_perf():           return dict(_d_perf)
def debug_contadores():     return dict(_d_contadores)


class _PerfTimer:
    __slots__ = ("etiqueta", "_t0")
    def __init__(self, etiqueta): self.etiqueta = etiqueta
    def __enter__(self):
        if DEBUG_ACTIVO: self._t0 = time.perf_counter()
        return self
    def __exit__(self, *_):
        if DEBUG_ACTIVO:
            _d_perf[self.etiqueta] += (time.perf_counter() - self._t0) * 1000.0

def debug_timer(etiqueta): return _PerfTimer(etiqueta)


def debug_marcar_update(v):
    if not DEBUG_ACTIVO: return
    vid = id(v)
    if _d_update_frame.get(vid) == _d_frame_actual:
        _d_registrar(f"[DOBLE_UPDATE] {v.id} frame={_d_frame_actual}")
    _d_update_frame[vid] = _d_frame_actual


def debug_validar_vehiculo(v, carril_esperado=None):
    if not DEBUG_ACTIVO: return
    vid = id(v)
    for attr in ("progreso", "velocidad_actual", "offset_lateral"):
        val = getattr(v, attr, 0.0)
        if not math.isfinite(val):
            _d_registrar(f"[NAN] {v.id}.{attr}={val}")
    if v.velocidad_actual < -0.1:
        _d_registrar(f"[VEL_NEG] {v.id} vel={v.velocidad_actual:.3f}")
    if v.velocidad_actual > v.velocidad_max * 1.10:
        _d_registrar(f"[VEL_OVER] {v.id} vel={v.velocidad_actual:.1f} max={v.velocidad_max:.1f}")
    estado = getattr(v, "_estado_cambio", None)
    if estado not in _ESTADOS_VALIDOS:
        _d_registrar(f"[FSM_INV] {v.id} estado='{estado}'")
    if carril_esperado is not None and v.carril is not carril_esperado:
        _d_registrar(f"[OWNERSHIP] {v.id} esperado={carril_esperado.id_carril} actual={v.carril.id_carril}")
    if estado == "LIBRE":
        if abs(getattr(v, "offset_lateral", 0.0)) > 0.5:
            _d_registrar(f"[INV2] {v.id} LIBRE offset={v.offset_lateral:.2f}")
        if getattr(v, "_carril_destino", None) is not None:
            _d_registrar(f"[INV2] {v.id} LIBRE _carril_destino!=None")
    elif estado == "PREPARANDO":
        if getattr(v, "_intencion_vecino", None) is None:
            _d_registrar(f"[INV2] {v.id} PREPARANDO _intencion_vecino=None")
        if abs(getattr(v, "offset_lateral", 0.0)) > 0.5:
            _d_registrar(f"[INV2] {v.id} PREPARANDO offset={v.offset_lateral:.2f}")
    if v.velocidad_actual < -0.05:
        _d_registrar(f"[INV3] {v.id} vel={v.velocidad_actual:.4f}")
    if estado == "CAMBIANDO":
        off = getattr(v, "offset_lateral", 0.0)
        prev_off, frames_ig = _d_offset_prev.get(vid, (off + 999.0, 0))
        frames_ig = (frames_ig + 1) if math.isclose(off, prev_off, abs_tol=0.5) else 0
        _d_offset_prev[vid] = (off, frames_ig)
        if frames_ig > DEBUG_OFFSET_MAX_FRAMES:
            _d_registrar(f"[OFFSET_FROZEN] {v.id} offset={off:.1f} por {frames_ig}f")
        if v.progreso > v.carril.longitud_total + v._largo():
            _d_registrar(f"[INV7] {v.id} CAMBIANDO progreso={v.progreso:.1f} > longitud={v.carril.longitud_total}")
    else:
        _d_offset_prev.pop(vid, None)
    prev_e, t_acum = _d_tiempos_estado.get(vid, (estado, 0.0))
    t_acum = (t_acum + 1 / 60.0) if (estado == prev_e == "PREPARANDO") else 0.0
    _d_tiempos_estado[vid] = (estado, t_acum)
    if t_acum > DEBUG_PREPARANDO_MAX:
        _d_registrar(f"[PREP_LOOP] {v.id} PREPARANDO {t_acum:.1f}s")


def debug_validar_escenario(escenario, frame_n):
    if not DEBUG_ACTIVO or frame_n % DEBUG_PERIODO != 0: return
    vistos, todos_veh = {}, []
    for carril in escenario.carriles:
        for v in carril.vehiculos:
            vid = id(v)
            todos_veh.append((v, carril))
            if vid in vistos:
                _d_registrar(f"[DUPLICADO] {v.id} en {vistos[vid].id_carril} y {carril.id_carril}")
            else:
                vistos[vid] = carril
            if v.carril is not carril:
                _d_registrar(f"[OWNERSHIP_ROTO] {v.id} v.carril={v.carril.id_carril} lista={carril.id_carril}")
            if v.salio_del_mapa() and v._estado_cambio != "CAMBIANDO":
                _d_registrar(f"[ZOMBIE] {v.id} salio_del_mapa pero en lista")
    for carril in escenario.carriles:
        ords = sorted(carril.vehiculos, key=lambda v: v.progreso, reverse=True)
        for i in range(len(ords) - 1):
            a, b = ords[i], ords[i + 1]
            if a._estado_cambio == "CAMBIANDO" or b._estado_cambio == "CAMBIANDO": continue
            gap = a.cola_progreso() - b.frente_progreso()
            if gap < -2.0:
                _d_registrar(f"[OVERLAP] {a.id}&{b.id} carril={carril.id_carril} gap={gap:.1f}px")
    _d_contadores["vehiculos_en_listas"] = len(todos_veh)


# ── sesión reproducible ────────────────────────────────────────────────────
class SesionReproducible:
    STRESS_CONFIGS = {
        "cruce_simultaneo": {"descripcion": "Cruces simultáneos", "seed": 1001, "spawn_intervalo": 0.3, "escala_tiempo": 3.0, "duracion_frames": 600},
        "spawn_denso":      {"descripcion": "Spawn agresivo",     "seed": 2002, "spawn_intervalo": 0.2, "escala_tiempo": 2.0, "duracion_frames": 1200},
        "dt_alto":          {"descripcion": "Escala 4x",          "seed": 3003, "spawn_intervalo": 1.0, "escala_tiempo": 4.0, "duracion_frames": 300},
        "pausa_cambio":     {"descripcion": "Pausa durante CAMBIANDO", "seed": 4004, "spawn_intervalo": 0.8, "escala_tiempo": 1.0, "duracion_frames": 400, "pausas": [(100,110),(200,205),(350,360)]},
    }

    def __init__(self, seed=42):
        self.seed = seed; self.frame = 0; self._log = []; self._activo = False

    def iniciar(self):
        random.seed(self.seed); self._activo = True; self.frame = 0; self._log = []

    def registrar_frame(self, escenario):
        if not self._activo: return
        self._log.append({"frame": self.frame, "vehiculos": [
            {"id": v.id, "carril": v.carril.id_carril, "progreso": round(v.progreso, 2),
             "vel": round(v.velocidad_actual, 2), "estado": v._estado_cambio,
             "offset": round(v.offset_lateral, 2)}
            for c in escenario.carriles for v in c.vehiculos
        ]})
        self.frame += 1

    def exportar(self, ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({"seed": self.seed, "frames": self._log}, f, indent=2)

    def frame_en(self, n): return self._log[n] if n < len(self._log) else {}

    @staticmethod
    def ejecutar_stress(gestor, nombre_config):
        config  = SesionReproducible.STRESS_CONFIGS[nombre_config]
        sesion  = SesionReproducible(config["seed"])
        sesion.iniciar()
        pausas  = {f for ini, fin in config.get("pausas", []) for f in range(ini, fin)}
        errores = []
        escala_orig = gestor.escala_tiempo
        gestor.ajustar_escala(config["escala_tiempo"])
        for frame_n in range(config["duracion_frames"]):
            gestor.pausado = frame_n in pausas
            gestor.actualizar(1 / 60.0)
            sesion.registrar_frame(gestor.escenario)
            errores.extend(debug_errores_frame())
        gestor.pausado = False
        gestor.ajustar_escala(escala_orig)
        por_tipo = {}
        for e in errores:
            tipo = (e.split("]")[0] + "]") if "]" in e else "UNKNOWN"
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        return {"config": nombre_config, "seed": config["seed"],
                "frames": config["duracion_frames"], "total_errores": len(errores),
                "por_tipo": por_tipo, "sesion": sesion}


# ── gestor principal ───────────────────────────────────────────────────────
class GestorSimulacion:

    def __init__(self):
        self.escenarios     = cargar_escenarios(os.path.join("data", "escenarios"))
        self.indice         = 0
        self.escenario      = self.escenarios[self.indice]
        self.pausado        = False
        self.escala_tiempo  = 1.0
        self._id            = 0
        self._frame_n       = 0
        self.gestor_eventos = GestorEventos()
        self.metricas = {
            "activos": 0, "generados": 0, "salidos": 0,
            "velocidad_promedio": 0.0, "cola_total": 0,
            "tiempo_espera_promedio": 0.0, "carriles_congestionados": 0,
            "prioritarios_activos": 0, "prioritarios_bloqueados": 0,
        }

    def pausar_reanudar(self):
        self.pausado = not self.pausado

    def ajustar_escala(self, nueva):
        self.escala_tiempo = max(0.25, min(4.0, nueva))

    def cambiar_escenario(self, indice):
        if 0 <= indice < len(self.escenarios):
            self.indice    = indice
            self.escenario = self.escenarios[indice]
            self.escenario.reiniciar()
            self.metricas = {k: (0 if isinstance(v, int) else 0.0) for k, v in self.metricas.items()}
            self._frame_n = 0
            _d_tiempos_estado.clear()
            _d_offset_prev.clear()
            _d_update_frame.clear()
            self.gestor_eventos.reiniciar(self)

    def recargar_escenarios(self):
        nombre_actual   = self.escenario.nombre
        self.escenarios = cargar_escenarios(os.path.join("data", "escenarios"))
        for i, esc in enumerate(self.escenarios):
            if esc.nombre == nombre_actual:
                self.indice = i; self.escenario = esc; return
        self.indice = 0; self.escenario = self.escenarios[0]

    def actualizar(self, dt_real):
        if self.pausado: return
        self._frame_n += 1
        debug_iniciar_frame(self._frame_n)
        dt = min(dt_real, 0.05) * self.escala_tiempo
        with debug_timer("semaforos"):       self.escenario.actualizar(dt)
        self.gestor_eventos.actualizar(self, dt)
        with debug_timer("spawn"):           self._generar_vehiculos(dt)
        with debug_timer("lane_change_intent"): self._procesar_cambios_carril()
        with debug_timer("fisica"):          self._actualizar_vehiculos(dt)
        with debug_timer("metricas"):        self._calcular_metricas_carriles()
        debug_validar_escenario(self.escenario, self._frame_n)
        debug_finalizar_frame()

    def _elegir_tipo(self, mezcla):
        r, acumulado = random.random(), 0.0
        for tipo, prob in mezcla.items():
            acumulado += prob
            if r <= acumulado: return tipo
        return list(mezcla.keys())[-1]

    def _generar_vehiculos(self, dt):
        for carril in self.escenario.carriles:
            carril.temporizador_spawn += dt
            if carril.temporizador_spawn < carril.spawn_intervalo: continue
            carril.temporizador_spawn = 0.0
            if carril.vehiculos:
                ultimo = min(carril.vehiculos, key=lambda v: v.progreso)
                if ultimo.cola_progreso() < ESPACIO_SPAWN: continue
            entrada_bloqueada = any(
                getattr(v, "_estado_cambio", "LIBRE") in ("PREPARANDO", "CAMBIANDO")
                and getattr(v, "_intencion_vecino", None) is carril
                and getattr(v, "progreso", -999) < ESPACIO_SPAWN * 1.5
                for vecino in carril.vecinos for v in vecino.vehiculos
            )
            if entrada_bloqueada: continue
            tipo     = self._elegir_tipo(carril.mezcla_vehiculos)
            vehiculo = TIPOS_VEHICULO[tipo](f"V{self._id}", carril)
            self._id += 1
            carril.vehiculos.append(vehiculo)
            self.metricas["generados"] += 1

    def _procesar_cambios_carril(self):
        for carril in self.escenario.carriles:
            if not carril.vecinos: continue
            snapshot = sorted(carril.vehiculos, key=lambda v: v.progreso, reverse=True)
            for i, v in enumerate(snapshot):
                if v.carril is not carril: continue
                frente = None
                if i > 0:
                    candidato = snapshot[i - 1]
                    if candidato.carril is carril: frente = candidato
                v.intentar_cambio_carril(frente)

    def _actualizar_vehiculos(self, dt):
        velocidades, cola_total = [], 0
        todos = []
        for carril in self.escenario.carriles:
            estado    = self.escenario.estado_semaforo_para_carril(carril)
            ordenados = sorted(carril.vehiculos, key=lambda v: v.progreso, reverse=True)
            for i, v in enumerate(ordenados):
                todos.append((v, ordenados[i - 1] if i > 0 else None, estado))
        vistos = set()
        for v, frente, estado in todos:
            vid = id(v)
            if vid in vistos:
                if DEBUG_ACTIVO: _d_registrar(f"[DOBLE_UPDATE_SIM] {v.id} frame={self._frame_n}")
                continue
            vistos.add(vid)
            debug_marcar_update(v)
            frente_valido = (
                frente if frente is not None
                and frente.carril is v.carril
                and frente._estado_cambio != "CAMBIANDO"
                else None
            )
            v.actualizar(dt, frente_valido, estado)
            debug_validar_vehiculo(v, carril_esperado=v.carril)
            velocidades.append(v.velocidad_actual)
            if estado == "ROJO" and not v.ya_cruzo_linea_de_pare() and v.velocidad_actual < 1.0:
                cola_total += 1
        for carril in self.escenario.carriles:
            salidos = [v for v in carril.vehiculos if v.salio_del_mapa() and (
                v._estado_cambio != "CAMBIANDO" or abs(getattr(v, "offset_lateral", 0.0)) < 0.5
            )]
            self.metricas["salidos"] += len(salidos)
            carril.vehiculos = [v for v in carril.vehiculos if v not in salidos]
        self.metricas["activos"]            = sum(len(c.vehiculos) for c in self.escenario.carriles)
        self.metricas["cola_total"]         = cola_total
        self.metricas["velocidad_promedio"] = sum(velocidades) / len(velocidades) if velocidades else 0.0

    def _calcular_metricas_carriles(self):
        congestionados, tiempos_espera = 0, []
        prioritarios_activos = prioritarios_bloqueados = 0
        for carril in self.escenario.carriles:
            if carril.nivel_congestion() >= 0.65: congestionados += 1
            for v in carril.vehiculos:
                if v.tiempo_espera > 0: tiempos_espera.append(v.tiempo_espera)
                if getattr(v, "ES_PRIORITARIO", False):
                    prioritarios_activos += 1
                    if v.velocidad_actual < v.velocidad_max * 0.20:
                        prioritarios_bloqueados += 1
        self.metricas["carriles_congestionados"]  = congestionados
        self.metricas["tiempo_espera_promedio"]   = sum(tiempos_espera) / len(tiempos_espera) if tiempos_espera else 0.0
        self.metricas["prioritarios_activos"]     = prioritarios_activos
        self.metricas["prioritarios_bloqueados"]  = prioritarios_bloqueados


# ── modo carrera ───────────────────────────────────────────────────────────
import math as _math, random as _random

_WAYPOINTS = [
    (800, 120), (1100, 200), (1350, 400), (1200, 640),
    (900, 740), (500, 740),  (200, 640),  (100,  400),
    (300, 200), (600,  120),
]
_VUELTAS_GANAR = 5

def _pto(idx, offset):
    wp  = _WAYPOINTS[idx % len(_WAYPOINTS)]
    sig = _WAYPOINTS[(idx + 1) % len(_WAYPOINTS)]
    dx, dy = sig[0] - wp[0], sig[1] - wp[1]
    lng    = _math.hypot(dx, dy) or 1
    nx, ny = -dy / lng, dx / lng
    return wp[0] + nx * offset, wp[1] + ny * offset


class VehiculoCarrera:
    VEL_BASE = 160

    def __init__(self, nombre, color, offset):
        self.nombre    = nombre
        self.color     = color
        self._offset   = offset
        self._wp_idx   = 0
        self.vueltas   = 0
        self.eliminado = False
        self.explosion = []
        self.velocidad = self.VEL_BASE + _random.randint(-20, 20)
        self.x, self.y = _pto(0, offset)
        self.angulo    = 0.0

    def actualizar(self, dt):
        if self.eliminado:
            self._tick_exp(dt); return
        tx, ty = _pto(self._wp_idx, self._offset)
        dx, dy = tx - self.x, ty - self.y
        dist   = _math.hypot(dx, dy)
        self.angulo = _math.degrees(_math.atan2(dy, dx))
        paso = self.velocidad * dt
        if dist < paso + 2:
            self._wp_idx = (self._wp_idx + 1) % len(_WAYPOINTS)
            if self._wp_idx == 0:
                self.vueltas += 1
                if self.vueltas % 3 == 0:
                    self.velocidad = self.VEL_BASE + _random.randint(-60, 90)
        else:
            self.x += dx / dist * paso
            self.y += dy / dist * paso

    def explotar(self):
        self.eliminado = True
        for _ in range(45):
            ang = _random.uniform(0, _math.pi * 2)
            vel = _random.uniform(50, 170)
            self.explosion.append({
                "x": self.x, "y": self.y,
                "vx": _math.cos(ang) * vel, "vy": _math.sin(ang) * vel,
                "vida": 1.0,
                "color": _random.choice([(255,80,0),(255,200,0),(255,255,80),(200,0,0),(255,120,0)]),
                "r": _random.randint(3, 9),
            })

    def _tick_exp(self, dt):
        for p in self.explosion:
            p["x"] += p["vx"] * dt; p["y"] += p["vy"] * dt
            p["vy"] += 140 * dt;    p["vida"] -= dt * 0.8
        self.explosion = [p for p in self.explosion if p["vida"] > 0]


class GestorCarrera:
    VUELTAS_GANAR = _VUELTAS_GANAR
    WAYPOINTS     = _WAYPOINTS

    def __init__(self):
        self.v1       = VehiculoCarrera("TURBO", (255, 60,  60), -20)
        self.v2       = VehiculoCarrera("RAYO",  ( 60, 160, 255),  20)
        self.iniciada  = False
        self.terminada = False
        self.ganador   = None

    def iniciar(self):
        if not self.iniciada: self.iniciada = True

    def actualizar(self, dt):
        if not self.iniciada or self.terminada: return
        self.v1.actualizar(dt)
        self.v2.actualizar(dt)
        for v, otro in [(self.v1, self.v2), (self.v2, self.v1)]:
            if v.vueltas >= self.VUELTAS_GANAR and not self.terminada:
                self.ganador = v; self.terminada = True; otro.explotar()

    def puntos_pista(self, offset):
        return [_pto(i, offset) for i in range(len(_WAYPOINTS))]
