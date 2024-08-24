from abc import ABC, abstractmethod
import math
from random import uniform
from mqtt_vehicle_fleet_sensor_data.iot.sensors import (
    GPS,
    FuelPressure,
    ManifoldAbsolutePressure,
    O2Sensor,
    VehicleSpeedSensor,
    VoltageDivider,
)
from mqtt_vehicle_fleet_sensor_data.publishers.telematic_control_unit import (
    TelematicConstrolUnit,
)
from mqtt_vehicle_fleet_sensor_data.utils import calculate_temperature_from_voltage


class PIDController:
    """PID controller for maintaining the air-fuel ratio."""

    def __init__(self, kp, ki, kd):
        self.kp = kp  # Proportional gain
        self.ki = ki  # Integral gain
        self.kd = kd  # Derivative gain
        self.integral = 0.0
        self.previous_error = 0.0

    def compute(self, setpoint, measured_value):
        """
        Compute the PID output based on setpoint and measured value.
        :param setpoint: Desired value (stoichiometric ratio)
        :param measured_value: Current measured value (AFR)
        :return: Adjustment needed for air-fuel ratio
        """
        error = setpoint - measured_value
        self.integral += error
        derivative = error - self.previous_error
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        self.previous_error = error
        return output


class EngineControlUnit:
    """Vehicle's ECU. Collects and processes data to be read by the Central Device."""

    def __init__(self, vss_pulses_per_rotation, vss_wheel_circumference) -> None:

        self.voltage_divider = VoltageDivider()
        self.map = ManifoldAbsolutePressure()
        self.fuel_pressure = FuelPressure()

        self.o2_sensor = O2Sensor()
        self.air_fuel_ratio = 14.7 + uniform(-0.5, 0.5)
        self.oxygen_voltage = self._get_oxygen()
        self.pid_controller = PIDController(kp=0.1, ki=0.01, kd=0.05)

        # self.vss = vss
        self.vehicle_speed = 0  # in m/s
        # self.pulse_frequency = pulse_frequency
        self.vss_pulses_per_rotation = vss_pulses_per_rotation
        self.vss_wheel_circumference = vss_wheel_circumference

    def read_data(self, vss_pulse_frequency):
        self._get_vehicle_speed(vss_pulse_frequency)

        data = {
            "ect": self._get_engine_coolant_temperature(),
            "iat": self._get_intake_air_temperature(),
            "map": self._get_manifold_absolute_pressure(),
            "fuel-press": self._get_fuel_pressure(),
            "oxygen": self.oxygen_voltage,
            "vss": self.vehicle_speed,
        }

        self._adjust_fuel_injection()
        return data

    def _get_engine_coolant_temperature(self) -> float:
        # TODO Temperature values based on system
        voltage = self.voltage_divider.get_voltage(uniform(10.0, 40.0))
        temperature = calculate_temperature_from_voltage(voltage)
        return temperature

    def _get_intake_air_temperature(self) -> float:
        # TODO Temperature values based on system
        voltage = self.voltage_divider.get_voltage(uniform(10.0, 40.0))
        temperature = calculate_temperature_from_voltage(voltage)
        return temperature

    def _get_manifold_absolute_pressure(self) -> float:
        # TODO Values based on normal and non-normal situations
        return self.map.get_voltage(uniform(10.0, 110.0))

    def _get_fuel_pressure(self) -> float:
        # TODO Values based on normal and non-normal situations
        return self.fuel_pressure.get_voltage(uniform(200.0, 700.0))

    def _get_oxygen(self):
        return self.o2_sensor.measure_exhaust_gas(self.air_fuel_ratio)

    def _get_vehicle_speed(self, vss_pulse_frequency):
        # self.pulse_frequency = self._get_pulse_frequency()
        self._process_vss_signal(vss_pulse_frequency)

    # def _get_pulse_frequency(self):
    #     return self.vss.generate_signal(uniform(100, 120))

    def _process_vss_signal(self, vss_pulse_frequency):
        """Process the signal from the VSS to calculate vehicle speed."""

        # Calculate wheel rotational speed in rotations per second (RPS)
        wheel_rotational_speed = vss_pulse_frequency / self.vss_pulses_per_rotation

        # Calculate vehicle speed in m/s
        self.vehicle_speed = wheel_rotational_speed * self.vss_wheel_circumference

    def _adjust_fuel_injection(self):
        """Adjust the air-fuel ratio based on the O2 sensor reading and PID control."""
        self.oxygen_voltage = self._get_oxygen()

        if self.oxygen_voltage < 0.45:
            measured_afr = 14.7 + (
                (0.45 - self.oxygen_voltage) * 10.0
            )  # Lean condition
        elif self.oxygen_voltage > 0.45:
            measured_afr = 14.7 - (
                (self.oxygen_voltage - 0.45) * 10.0
            )  # Rich condition
        else:
            measured_afr = 14.7  # Stoichiometric

        pid_adjustment = self.pid_controller.compute(
            setpoint=14.7, measured_value=measured_afr
        )

        self.air_fuel_ratio += pid_adjustment


class Vehicle(ABC):
    def __init__(self, id: str, route: str) -> None:
        self.id = id
        self.voltage_divider = VoltageDivider()
        self.gps = GPS(route)
        self.vss = VehicleSpeedSensor()
        self.vss_pulse_frequency = 0
        self.ecu = EngineControlUnit(
            self.vss.pulses_per_rotation,
            self.vss.wheel_circumference,
        )
        self.tcu = self.create_tcu()

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def create_tcu(self) -> "TelematicConstrolUnit":
        pass

    def collect_data(self):
        # Update VSS pulse frequency to be used by ECU
        self._get_vss_pulse_frequency()

        return {
            "id": self.id,
            "gps": self._collect_gps_data(),
            "ecu": self._collect_ecu_data(),
            "cabin-temp": self._get_cabin_temperature(),
        }

    def _collect_gps_data(self) -> dict:
        return self.gps.read()

    def _collect_ecu_data(self) -> dict:
        return self.ecu.read_data(self.vss_pulse_frequency)

    def _get_cabin_temperature(self) -> float:
        # TODO Temperature values based on system
        voltage = self.voltage_divider.get_voltage(uniform(0.0, 60.0))
        temperature = calculate_temperature_from_voltage(voltage)
        return temperature

    def _get_vss_pulse_frequency(self):
        self.vss_pulse_frequency = self.vss.generate_signal(uniform(100, 120))
