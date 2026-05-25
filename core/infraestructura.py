# core/infraestructura.py
import os
import json


class Via:
    def __init__(self, x, y, ancho, alto, orientacion, lineas_separacion=None, linea_central=True):
        self.x                 = x
        self.y                 = y
        self.ancho             = ancho
        self.alto              = alto
        self.orientacion       = orientacion
        self.lineas_separacion = lineas_separacion or []
        self.linea_central     = linea_central


class Cebra:
    def __init__(self, x, y, ancho, alto):
        self.x = x; self.y = y; self.ancho = ancho; self.alto = alto


class LineaPare:
    def __init__(self, x, y, ancho, alto):
        self.x = x; self.y = y; self.ancho = ancho; self.alto = alto


class Semaforo:
    def __init__(self, id_s, x, y, grupo, lado="centro"):
        self.id_s = id_s; self.x = x; self.y = y
        self.grupo = grupo; self.lado = lado


class Carril:
    def __init__(self, id_carril, eje, coordenada_fija, direccion, inicio, fin,
                 coord_pare, grupo_semaforo, spawn_intervalo=1.5,
                 mezcla_vehiculos=None, margen_detencion=14, indice_carril=0):
        self.indice_carril    = indice_carril
        self.id_carril        = id_carril
        self.eje              = eje
        self.coordenada_fija  = coordenada_fija
        self.direccion        = direccion
        self.inicio           = inicio
        self.fin              = fin
        self.coord_pare       = coord_pare
        self.grupo_semaforo   = grupo_semaforo
        self.spawn_intervalo  = spawn_intervalo
        self.mezcla_vehiculos = mezcla_vehiculos or {
            "automovil": 0.40, "moto": 0.28, "bus": 0.15, "camion": 0.17
        }
        self.vehiculos          = []
        self.temporizador_spawn = 0.0
        self.vecinos            = []
        self.longitud_total     = abs(self.fin - self.inicio)
        coords                  = coord_pare if isinstance(coord_pare, list) else [coord_pare]
        self.progreso_pares     = sorted([abs(c - self.inicio) for c in coords])
        self.progreso_pare      = self.progreso_pares[0]
        self.margen_detencion   = margen_detencion

    def velocidad_promedio(self):
        if not self.vehiculos: return 0.0
        return sum(v.velocidad_actual for v in self.vehiculos) / len(self.vehiculos)

    def nivel_congestion(self):
        if not self.vehiculos: return 0.0
        densidad = min(1.0, len(self.vehiculos) / 8.0)
        vel_norm = 1.0 - min(1.0, self.velocidad_promedio() / 112.0)
        return densidad * 0.4 + vel_norm * 0.6

    def posicion_mundo(self, progreso):
        coord = self.inicio + progreso if self.direccion > 0 else self.inicio - progreso
        if self.eje == "x":
            return int(coord), int(self.coordenada_fija)
        return int(self.coordenada_fija), int(coord)

    def es_vecino_de(self, otro):
        return (
            self.eje == otro.eje
            and self.direccion == otro.direccion
            and self.grupo_semaforo == otro.grupo_semaforo
            and 0 < abs(self.coordenada_fija - otro.coordenada_fija) <= 80
        )


class Escenario:
    def __init__(self, data):
        from core.controlador import ControladorCruce
        self.nombre = data["nombre"]
        self.ancho  = data.get("ancho", 1280)
        self.alto   = data.get("alto",  720)

        c = data["controlador"]
        self.controlador = ControladorCruce(
            c["verde_h"], c["amarillo_h"], c["verde_v"], c["amarillo_v"]
        )
        self.vias = [
            Via(v["x"], v["y"], v["ancho"], v["alto"], v["orientacion"],
                v.get("lineas_separacion", []), v.get("linea_central", True))
            for v in data.get("vias", [])
        ]
        self.cebras = [
            Cebra(z["x"], z["y"], z["ancho"], z["alto"])
            for z in data.get("cebras", [])
        ]
        self.lineas_pare = [
            LineaPare(lp["x"], lp["y"], lp["ancho"], lp["alto"])
            for lp in data.get("lineas_pare", [])
        ]
        self.semaforos = [
            Semaforo(s["id"], s["x"], s["y"], s["grupo"], s.get("lado", "centro"))
            for s in data.get("semaforos", [])
        ]
        self.carriles = [
            Carril(
                id_carril        = c["id_carril"],
                eje              = c["eje"],
                coordenada_fija  = c["coordenada_fija"],
                direccion        = c["direccion"],
                inicio           = c["inicio"],
                fin              = c["fin"],
                coord_pare       = c["coord_pare"],
                grupo_semaforo   = c["grupo_semaforo"],
                spawn_intervalo  = c.get("spawn_intervalo", 1.5),
                mezcla_vehiculos = c.get("mezcla_vehiculos"),
                margen_detencion = c.get("margen_detencion", 14),
            )
            for c in data.get("carriles", [])
        ]
        for carril in self.carriles:
            carril.vecinos = [otro for otro in self.carriles if carril.es_vecino_de(otro)]
        self.controlador._carriles = self.carriles

    def actualizar(self, dt):
        self.controlador.actualizar(dt)

    def estado_semaforo_para_carril(self, carril):
        return self.controlador.estado_grupo(carril.grupo_semaforo)

    def reiniciar(self):
        for carril in self.carriles:
            carril.vehiculos.clear()
            carril.temporizador_spawn = 0.0
        self.controlador.reiniciar()


def cargar_escenarios(carpeta):
    if not os.path.exists(carpeta):
        raise FileNotFoundError(f"No existe la carpeta: {carpeta}")
    archivos = sorted(a for a in os.listdir(carpeta) if a.endswith(".json"))
    if not archivos:
        raise RuntimeError("No se encontraron archivos .json en data/escenarios/")
    return [
        Escenario(json.load(open(os.path.join(carpeta, a), encoding="utf-8")))
        for a in archivos
    ]
