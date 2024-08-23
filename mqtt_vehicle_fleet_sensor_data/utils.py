import math


def calculate_temperature_from_voltage(voltage):
    # Steinhart-Hart coefficients for the thermistor (example values)
    A = 1.009249522e-03
    B = 2.378405444e-04
    C = 2.019202697e-07

    V_ref = 5.0  # Reference voltage from the ECU in volts
    R_pull_up = 10000  # Pull-up resistor value in ohms

    # Calculate the resistance of the thermistor from the voltage
    if voltage == V_ref:  # Prevent division by zero
        return float("inf")  # Indicating an open circuit or infinite temperature

    R_thermistor = R_pull_up * (voltage / (V_ref - voltage))

    # Apply Steinhart-Hart equation to calculate the temperature in Kelvin
    lnR = math.log(R_thermistor)
    inv_T = A + B * lnR + C * (lnR**3)
    T_kelvin = 1 / inv_T

    # Convert Kelvin to Celsius
    T_celsius = T_kelvin - 273.15
    return T_celsius
