from concurrent.futures import ProcessPoolExecutor
from enum import Enum
from multiprocessing import active_children, current_process
import sys

from mqtt_vehicle_fleet_sensor_data.publishers.vehicles import Van
import typer


class VehicleType(Enum):
    VAN = 'van'
    TRUCK = 'truck'
    

def start_vehicle(id: str, vehicle_type: VehicleType, route: str) -> None:
    try:
        Van(id, route).run()
    except KeyboardInterrupt:
        print(f"Worker {current_process().name} interrupted")


def terminate_active_children():
    for p in active_children():
        print(f"Terminating child process {p.pid}")
        p.terminate()
        p.join()  # Ensure the child process has fully terminated


def cleanup(executor):
    print("Main process interrupted. Shutting down...")
    executor.shutdown(wait=False)

    print("ACTIVE CHILDRENS:\n", active_children())
    terminate_active_children()
    print("ACTIVE CHILDRENS:\n", active_children())


def main():
    # TODO environment variable
    n_vans = 4
    n_trucks = 0

    try:
        with ProcessPoolExecutor(max_workers=4) as executor:

            futures = [
                # TODO automate routes probabilistically
                executor.submit(start_vehicle, f"van-{i}", VehicleType.VAN, "dublin-limerick") for i in range(1, n_vans + 1)
            ]  # does not block
    except KeyboardInterrupt:
        cleanup(executor)
        sys.exit()


if __name__ == "__main__":
    typer.run(main)