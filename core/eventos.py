# core/eventos.py
import random
import math


class Evento:
    nombre = "evento_base"
    activo = False

    def aplicar(self, gestor):        pass
    def revertir(self, gestor):       pass
    def actualizar(self, gestor, dt): pass


class EventoHoraPico(Evento):
    nombre        = "hora_pico"
    FACTOR_SPAWN  = 0.45
    FACTOR_MEZCLA = {"automovil": 0.35, "moto": 0.20, "bus": 0.25, "camion": 0.20}

    def __init__(self):
        self._spawns_orig  = {}
        self._mezclas_orig = {}

    def aplicar(self, gestor):
        if self.activo: return
        self.activo = True
        for c in gestor.escenario.carriles:
            self._spawns_orig[c.id_carril]  = c.spawn_intervalo
            self._mezclas_orig[c.id_carril] = dict(c.mezcla_vehiculos)
            c.spawn_intervalo  = c.spawn_intervalo * self.FACTOR_SPAWN
            c.mezcla_vehiculos = dict(self.FACTOR_MEZCLA)

    def revertir(self, gestor):
        if not self.activo: return
        self.activo = False
        for c in gestor.escenario.carriles:
            if c.id_carril in self._spawns_orig:
                c.spawn_intervalo  = self._spawns_orig[c.id_carril]
                c.mezcla_vehiculos = self._mezclas_orig[c.id_carril]
        self._spawns_orig.clear()
        self._mezclas_orig.clear()


class EventoLluvia(Evento):
    nombre        = "lluvia"
    N_GOTAS       = 180
    COLOR_GOTA    = (174, 214, 241, 90)
    COLOR_OVERLAY = (20,  35,  55,  38)
    N_CHARCOS     = 18

    def __init__(self):
        self._gotas        = []
        self._charcos      = []
        self._timer_charco = 0.0
        self._inicializar_gotas()

    def _inicializar_gotas(self):
        self._gotas = [
            [random.randint(0, 1280), random.randint(0, 720),
             random.randint(8, 18),   random.uniform(280, 420)]
            for _ in range(self.N_GOTAS)
        ]

    def _spawn_charco(self, ancho_sim, alto):
        vida = random.uniform(8.0, 20.0)
        self._charcos.append([
            random.randint(60, ancho_sim - 60),
            random.randint(60, alto - 60),
            random.randint(18, 45),
            random.randint(8, 20),
            vida, vida,
        ])

    def aplicar(self, gestor):
        if self.activo: return
        self.activo = True

    def revertir(self, gestor):
        if not self.activo: return
        self.activo = False
        self._charcos.clear()

    def actualizar(self, gestor, dt):
        if not self.activo: return
        for g in self._gotas:
            g[1] += g[3] * dt
            g[0] -= g[3] * 0.18 * dt
            if g[1] > 720 + 20:
                g[1] = random.randint(-30, -5)
                g[0] = random.randint(0, 1280)
        self._timer_charco += dt
        if self._timer_charco > 1.2 and len(self._charcos) < self.N_CHARCOS:
            self._timer_charco = 0.0
            self._spawn_charco(1280, 720)
        for ch in self._charcos:
            ch[4] -= dt * 0.08
        self._charcos = [ch for ch in self._charcos if ch[4] > 0]

    def wobble_offset(self, tiempo_total):
        if not self.activo: return 0.0
        return math.sin(tiempo_total * 3.5) * 1.8


class EventoNiebla(Evento):
    nombre            = "niebla"
    ALPHA_MAX         = 155
    VELOCIDAD_ENTRADA = 18.0
    VELOCIDAD_SALIDA  = 25.0

    def __init__(self):
        self._alpha         = 0.0
        self._saliendo      = False
        self._decision_orig = {}

    def alpha(self): return self._alpha

    def aplicar(self, gestor):
        if self.activo: return
        self.activo    = True
        self._saliendo = False
        for c in gestor.escenario.carriles:
            for v in c.vehiculos:
                self._decision_orig[id(v)] = v.tolerancia_amarillo
                v.tolerancia_amarillo = 0.0

    def revertir(self, gestor):
        if not self.activo: return
        self._saliendo = True
        for c in gestor.escenario.carriles:
            for v in c.vehiculos:
                vid = id(v)
                if vid in self._decision_orig:
                    v.tolerancia_amarillo = self._decision_orig[vid]
        self._decision_orig.clear()

    def actualizar(self, gestor, dt):
        if not self.activo and not self._saliendo: return
        if self._saliendo:
            self._alpha -= self.VELOCIDAD_SALIDA * dt
            if self._alpha <= 0.0:
                self._alpha    = 0.0
                self._saliendo = False
                self.activo    = False
            return
        for c in gestor.escenario.carriles:
            for v in c.vehiculos:
                vid = id(v)
                if vid not in self._decision_orig:
                    self._decision_orig[vid] = v.tolerancia_amarillo
                    v.tolerancia_amarillo = 0.0
        vivos = {id(v) for c in gestor.escenario.carriles for v in c.vehiculos}
        for vid in [k for k in self._decision_orig if k not in vivos]:
            del self._decision_orig[vid]
        if self._alpha < self.ALPHA_MAX:
            self._alpha = min(self.ALPHA_MAX, self._alpha + self.VELOCIDAD_ENTRADA * dt)


class EventoAccidente(Evento):
    nombre = "accidente"

    def __init__(self):
        self._carril_bloqueado = None
        self._spawn_orig       = None
        self._pos_accidente    = None

    def pos_accidente(self):
        return self._carril_bloqueado, self._pos_accidente

    def aplicar(self, gestor):
        if self.activo: return
        self.activo            = True
        candidatos             = [c for c in gestor.escenario.carriles if c.vehiculos] or gestor.escenario.carriles
        self._carril_bloqueado = random.choice(candidatos)
        c                      = self._carril_bloqueado
        self._spawn_orig       = c.spawn_intervalo
        c.spawn_intervalo      = 9999.0
        c.bloqueado_accidente  = True
        self._pos_accidente    = c.longitud_total * random.uniform(0.25, 0.65)

    def revertir(self, gestor):
        if not self.activo: return
        self.activo = False
        if self._carril_bloqueado:
            self._carril_bloqueado.spawn_intervalo     = self._spawn_orig
            self._carril_bloqueado.bloqueado_accidente = False
        self._carril_bloqueado = None
        self._spawn_orig       = None
        self._pos_accidente    = None


class EventoFiesta(Evento):
    nombre    = "fiesta"
    _COLORES  = [
        (255, 0, 100), (0, 200, 255), (255, 200, 0),
        (180, 0, 255), (0, 255, 120), (255, 80,   0),
    ]

    def __init__(self):
        self.activo        = False
        self._spawns_orig  = {}
        self._mezclas_orig = {}
        self._t_global     = 0.0

    def aplicar(self, gestor):
        if self.activo: return
        self.activo = True
        for c in gestor.escenario.carriles:
            self._spawns_orig[c.id_carril]  = c.spawn_intervalo
            self._mezclas_orig[c.id_carril] = c.mezcla_vehiculos.copy()
            c.spawn_intervalo  = 3.0
            c.mezcla_vehiculos = {"policia": 1.0}

    def revertir(self, gestor):
        if not self.activo: return
        self.activo = False
        for c in gestor.escenario.carriles:
            if c.id_carril in self._spawns_orig:
                c.spawn_intervalo  = self._spawns_orig[c.id_carril]
                c.mezcla_vehiculos = self._mezclas_orig[c.id_carril]
        self._spawns_orig.clear()
        self._mezclas_orig.clear()

    def actualizar(self, gestor, dt):
        if not self.activo: return
        self._t_global += dt
        for carril in gestor.escenario.carriles:
            for v in carril.vehiculos:
                fase = math.sin(self._t_global * 1.8 * math.pi + hash(v.id) % 100)
                v.offset_lateral = fase * 0.7 * getattr(carril, "ancho_carril_px", 40)

    def t_global(self): return self._t_global


class EventoNoche(Evento):
    nombre       = "noche"
    ALPHA_MAX    = 170
    VEL_FADE     = 22.0
    FACTOR_SPAWN = 8

    def __init__(self):
        self._alpha       = 0.0
        self._saliendo    = False
        self._spawns_orig = {}

    def alpha(self): return self._alpha

    def aplicar(self, gestor):
        if self.activo: return
        self.activo    = True
        self._saliendo = False
        for c in gestor.escenario.carriles:
            self._spawns_orig[c.id_carril] = c.spawn_intervalo
            c.spawn_intervalo = c.spawn_intervalo * self.FACTOR_SPAWN

    def revertir(self, gestor):
        if not self.activo: return
        self._saliendo = True
        for c in gestor.escenario.carriles:
            if c.id_carril in self._spawns_orig:
                c.spawn_intervalo = self._spawns_orig[c.id_carril]
        self._spawns_orig.clear()

    def actualizar(self, gestor, dt):
        if self._saliendo:
            self._alpha -= self.VEL_FADE * dt
            if self._alpha <= 0.0:
                self._alpha    = 0.0
                self._saliendo = False
                self.activo    = False
            return
        if self.activo and self._alpha < self.ALPHA_MAX:
            self._alpha = min(self.ALPHA_MAX, self._alpha + self.VEL_FADE * dt)


class GestorEventos:
    def __init__(self):
        self.hora_pico = EventoHoraPico()
        self.lluvia    = EventoLluvia()
        self.niebla    = EventoNiebla()
        self.accidente = EventoAccidente()
        self.noche     = EventoNoche()
        self.fiesta    = EventoFiesta()
        self._todos    = [
            self.hora_pico, self.fiesta, self.lluvia,
            self.niebla, self.accidente, self.noche,
        ]

    def toggle(self, nombre, gestor_sim):
        for evento in self._todos:
            if evento.nombre == nombre:
                if evento.activo: evento.revertir(gestor_sim)
                else:             evento.aplicar(gestor_sim)
                return

    def actualizar(self, gestor_sim, dt):
        for evento in self._todos:
            evento.actualizar(gestor_sim, dt)

    def reiniciar(self, gestor_sim):
        for evento in self._todos:
            if evento.activo:
                evento.revertir(gestor_sim)

    def estado(self):
        return {e.nombre: e.activo for e in self._todos}

    def wobble_lluvia(self, tiempo_total):
        return self.lluvia.wobble_offset(tiempo_total)
