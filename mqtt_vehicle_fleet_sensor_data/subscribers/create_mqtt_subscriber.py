from mqtt_vehicle_fleet_sensor_data.subscribers.mqtt_subscriber import MQTTSubscriber
import typer


def main(mqtt_topic: str, mqtt_broker: str, port: int) -> None:
    
    subscriber = MQTTSubscriber(mqtt_broker, port, mqtt_topic)
    subscriber.start()


if __name__ == "__main__":
    typer.run(main)