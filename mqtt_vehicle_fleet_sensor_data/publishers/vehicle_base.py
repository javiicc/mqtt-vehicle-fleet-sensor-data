from mqtt_vehicle_fleet_sensor_data.iot.sensors import GPS, Thermistor


class Engine:
    def __init__(self) -> None:
        self.thermistor = Thermistor("engine")

    def read_data(self):
        return self.thermistor.read()


class Vehicle:
    def __init__(self, id: str, route: str) -> None:
        self.id = id
        self.mqtt_topic_data = "fleet/data"
        self.mqtt_topic_gps = "fleet/gps"
        self.gps = GPS(route)
        self.engine = Engine() # TODO provide different engines based on the type of vehicle - EngineProvider

    def collect_gps_data(self) -> dict:
        return self.gps.read()
    
    def collect_engine_data(self) -> dict:
        return self.engine.read_data()
    
    