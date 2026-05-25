    class GestorCarrera {
        +VehiculoCarrera v1
        +VehiculoCarrera v2
        +bool iniciada
        +bool terminada
        +VehiculoCarrera ganador
        +iniciar()
        +actualizar(dt)
        +puntos_pista(offset) List
    }

    class VehiculoCarrera {
        +String nombre
        +tuple color
        +float velocidad
        +float x
        +float y
        +int vueltas
        +bool eliminado
        +List explosion
        +actualizar(dt)
        +explotar()
    }

    %% Herencia
    Vehiculo <|-- VehiculoPrioritario
    Vehiculo <|-- Automovil
    Vehiculo <|-- Moto
    Vehiculo <|-- Bus
    Vehiculo <|-- Camion
    VehiculoPrioritario <|-- Ambulancia
    VehiculoPrioritario <|-- Policia

    %% Composición
    Escenario *-- Controlador
    Escenario *-- Via
    GestorSimulacion *-- GestorEventos
    GestorCarrera *-- VehiculoCarrera

    %% Agregación
    Escenario o-- Carril
    Carril o-- Vehiculo

    %% Asociación dirigida
    Vehiculo --> Carril : carril actual
    Carril --> Carril : vecinos
    GestorSimulacion --> Escenario : escenario activo

    %% Dependencia
    GestorSimulacion ..> Vehiculo : instancia via TIPOS_VEHICULO
    GestorSimulacion ..> SesionReproducible : usa en stress test
