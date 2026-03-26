class GestorSimulacion:
    def __init__(self):
        carpeta_escenarios = os.path.join("data", "escenarios")
        self.escenarios = cargar_escenarios(carpeta_escenarios)
        self.indice_escenario = 0
        self.escenario = self.escenarios[self.indice_escenario]

        self.pausado = False
        self.escala_tiempo = 1.0
        self.contador_ids = 0

        self.metricas = {
            "activos": 0,
            "generados": 0,
            "salidos": 0,
            "velocidad_promedio": 0.0,
            "cola_total": 0
        }

    def cambiar_escenario(self, nuevo_indice):
        if 0 <= nuevo_indice < len(self.escenarios):
            self.indice_escenario = nuevo_indice
            self.escenario = self.escenarios[nuevo_indice]

    def recargar_escenarios(self):
        carpeta_escenarios = os.path.join("data", "escenarios")
        nombre_actual = self.escenario.nombre
        self.escenarios = cargar_escenarios(carpeta_escenarios)

        for i, esc in enumerate(self.escenarios):
            if esc.nombre == nombre_actual:
                self.indice_escenario = i
                self.escenario = esc
                return

        self.indice_escenario = 0
        self.escenario = self.escenarios[0]

    def pausar_reanudar(self):
        self.pausado = not self.pausado

    def ajustar_escala(self, nueva_escala):
        self.escala_tiempo = max(0.25, min(4.0, nueva_escala))

    def _elegir_tipo_vehiculo(self, mezcla):
        r = random.random()
        acumulado = 0.0
        ultimo = "automovil"

        for tipo, prob in mezcla.items():
            acumulado += prob
            ultimo = tipo
            if r <= acumulado:
                return tipo
        return ultimo

    def _siguiente_id(self):
        self.contador_ids += 1
        return f"V{self.contador_ids}"

    def _cabe_otro_en_spawn(self, carril):
        if not carril.vehiculos:
            return True

        vehiculo_mas_cercano_al_inicio = min(carril.vehiculos, key=lambda v: v.progreso)
        return vehiculo_mas_cercano_al_inicio.cola_progreso() > 110

    def _generar_vehiculos(self, dt):
        for carril in self.escenario.carriles:
            carril.temporizador_spawn += dt

            if carril.temporizador_spawn >= carril.spawn_intervalo:
                carril.temporizador_spawn = 0.0

                if self._cabe_otro_en_spawn(carril):
                    tipo = self._elegir_tipo_vehiculo(carril.mezcla_vehiculos)
                    clase_vehiculo = TIPOS_VEHICULO[tipo]
                    vehiculo = clase_vehiculo(self._siguiente_id(), carril)
                    carril.vehiculos.append(vehiculo)
                    self.metricas["generados"] += 1

    def _actualizar_vehiculos(self, dt):
        velocidades = []
        cola_total = 0

        for carril in self.escenario.carriles:
            estado_semaforo = self.escenario.estado_semaforo_para_carril(carril)

            carril.vehiculos.sort(key=lambda v: v.progreso, reverse=True)

            for i, vehiculo in enumerate(carril.vehiculos):
                vehiculo_frente = carril.vehiculos[i - 1] if i > 0 else None
                vehiculo.actualizar(dt, vehiculo_frente, estado_semaforo)
                velocidades.append(vehiculo.velocidad_actual)

                if estado_semaforo == "ROJO":
                    if (not vehiculo.ya_cruzo_linea_de_pare()) and vehiculo.velocidad_actual < 1.0:
                        if vehiculo.frente_progreso() <= carril.progreso_pare + 20:
                            cola_total += 1

            sobrevivientes = []
            for vehiculo in carril.vehiculos:
                if vehiculo.salio_del_mapa():
                    self.metricas["salidos"] += 1
                else:
                    sobrevivientes.append(vehiculo)

            carril.vehiculos = sobrevivientes

        self.metricas["activos"] = sum(len(c.vehiculos) for c in self.escenario.carriles)
        self.metricas["cola_total"] = cola_total
        self.metricas["velocidad_promedio"] = (sum(velocidades) / len(velocidades)) if velocidades else 0.0

    def actualizar(self, dt_real):
        if self.pausado:
            return

        dt = dt_real * self.escala_tiempo
        self.escenario.actualizar(dt)
        self._generar_vehiculos(dt)
        self._actualizar_vehiculos(dt)

    def dibujar(self, superficie_simulacion):
        self.escenario.dibujar(superficie_simulacion)

        for carril in self.escenario.carriles:
            for vehiculo in carril.vehiculos:
                superficie_simulacion.blit(vehiculo.image, vehiculo.rect)

    def dibujar_panel(self, pantalla, x_inicio, ancho_panel, alto_total, fuente_titulo, fuente_texto):
        panel_rect = pygame.Rect(x_inicio, 0, ancho_panel, alto_total)
        pygame.draw.rect(pantalla, (25, 25, 30), panel_rect)

        x = x_inicio + 18
        y = 18

        titulo = fuente_titulo.render("CityPulse", True, (255, 255, 255))
        pantalla.blit(titulo, (x, y))
        y += 40

        estado_h = self.escenario.controlador.estado_grupo("H")
        estado_v = self.escenario.controlador.estado_grupo("V")
        restante_h = self.escenario.controlador.tiempo_restante_grupo("H")
        restante_v = self.escenario.controlador.tiempo_restante_grupo("V")

        lineas = [
            f"Escenario: {self.escenario.nombre}",
            f"Pausado: {'Sí' if self.pausado else 'No'}",
            f"Escala tiempo: {self.escala_tiempo:.2f}x",
            "",
            f"Vehículos activos: {self.metricas['activos']}",
            f"Vehículos generados: {self.metricas['generados']}",
            f"Vehículos salidos: {self.metricas['salidos']}",
            f"Vel. promedio: {self.metricas['velocidad_promedio']:.1f}",
            f"Cola total: {self.metricas['cola_total']}",
            "",
            f"Grupo H: {estado_h} ({restante_h:.1f}s)",
            f"Grupo V: {estado_v} ({restante_v:.1f}s)",
            "",
            "Controles:",
            "1 / 2 / 3 -> escenarios",
            "ESPACIO -> pausar",
            "+ / - -> velocidad",
            "R -> recargar escenarios",
            "ESC -> salir"
        ]

        for linea in lineas:
            surf = fuente_texto.render(linea, True, (235, 235, 235))
            pantalla.blit(surf, (x, y))
            y += 24
