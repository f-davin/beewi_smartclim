"""Parser for BeeWi SmartClim BLE devices"""

import re
from dataclasses import dataclass
from datetime import datetime

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

CONNECTED_DATA_SIZE = 10
ADVERTISING_DATA_SIZE = 11


@dataclass
class ManufacturerData:
    manufacturer: str = ""
    model: str = ""
    serial: str = ""
    fw_revision: str = ""
    hw_revision: str = ""
    soft_revision: str = ""


@dataclass
class SensorData:
    """Data to store the information about the sensor"""

    name: str = ""
    temperature: float = 0.0
    humidity: int = 0
    battery: int = 0

    def decode(self, raw_data: bytearray, is_adv_data: bool = False) -> None:
        """
        Decode the raw data and update the corresponding value.

        :param raw_data: Bytes from the frame.
        :param is_adv_data: Information if data comes from advertising data of active connection.
        :return: None
        """
        frame_length = CONNECTED_DATA_SIZE
        offset = 0
        if is_adv_data:
            frame_length = ADVERTISING_DATA_SIZE
            offset = 1

        if len(raw_data) != frame_length:
            raise Exception("Wrong size to decode data")

        # Positive value: byte 1 & 2 present the tenfold of the temperature
        # Negative value: byte 2 - byte 3 present the tenfold of the temperature
        # t0 = val [ 0 ]
        # t1 = val [ 1 ]
        # t2 = val [ 2 ]
        # if t2 == 255:
        #   temperature = (t1 - t2) / 10.0
        # else:
        #   temperature = ((t0 * 255) + t1) / 10.0
        temperature = raw_data[2 + offset] + raw_data[1 + offset]
        if temperature > 0x8000:
            temperature = temperature - 0x10000
        self.temperature = temperature / 10.0
        self.humidity = raw_data[4 + offset]
        self.battery = raw_data[9 + offset]

    def supported_data(self, adv_data: AdvertisementData) -> bool:
        ret = False
        manuf_data = adv_data.manufacturer_data
        if len(manuf_data) != 0:
            bytes_data = manuf_data[list(manuf_data.keys())[0]].hex()
            if type(bytes_data) is str:
                bytes_data = bytearray.fromhex(bytes_data)
                if bytes_data is not None:
                    if len(bytes_data) == CONNECTED_DATA_SIZE:
                        ret = True
                    elif (
                        len(bytes_data) == ADVERTISING_DATA_SIZE
                        and bytes_data[0] == 0x05
                    ):
                        ret = True
        return ret


@dataclass
class BeeWiSmartClimAdvertisement:
    """Class to realize the treatment of an advertising frame."""

    device: BLEDevice = None
    readings: SensorData = SensorData()

    def __init__(
        self,
        device: BLEDevice = None,
        ad_data: AdvertisementData = None,
    ):
        """Constructor."""
        self.device = device

        if device and ad_data:
            self.readings.name = device.name
            data = ad_data.manufacturer_data
            key = list(data.keys())[0]
            self.readings.decode(data[key], True)


class BeeWiSmartClim:
    # Param return value if no data
    AR4_NO_DATA_FOR_PARAM = -1

    UUID_MANUFACTURER_NAME = "00002a29-0000-1000-8000-00805f9b34fb"  # Handle 0x0025
    UUID_SOFTWARE_REV = "00002a28-0000-1000-8000-00805f9b34fb"  # Handle 0x0023
    UUID_SERIAL_NUMBER = "00002a25-0000-1000-8000-00805f9b34fb"  # Handle 0x001d
    UUID_MODEL = "00002a24-0000-1000-8000-00805f9b34fb"  # Handle 0x001b
    UUID_FIRMWARE_REV = "00002a26-0000-1000-8000-00805f9b34fb"  # Handle 0x001f
    UUID_HARDWARE_REV = "00002a27-0000-1000-8000-00805f9b34fb"  # Handle 0X0021
    UUID_GET_VALUES = "a8b3fb43-4834-4051-89d0-3de95cddd318"  # Handle 0x003f

    # Regexp
    REGEX_MAC = "([0-9a-f]{2}[:-]){5}([0-9a-f]{2})"
    REGEX_UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    REGEX_ADDR = f"({REGEX_MAC})|({REGEX_UUID})"

    def __init__(self, address: str):
        if not re.match(self.REGEX_ADDR, address.lower()):
            raise Exception("Invalid device address")

        self.address = address
        self.device = BleakClient(address)
        self.reading: bool = True
        self.manufacturer_data: ManufacturerData = ManufacturerData()
        self.last_values_read: datetime = datetime.now()

    async def read_manufactoring_data(self) -> None:
        """Read the data from the manufacturer."""
        manufacturer = await self.device.read_gatt_char(self.UUID_MANUFACTURER_NAME)
        self.manufacturer_data.manufacturer = manufacturer
        self.manufacturer_data.model = await self.device.read_gatt_char(self.UUID_MODEL)
        self.manufacturer_data.serial = await self.device.read_gatt_char(
            self.UUID_SERIAL_NUMBER
        )
        self.manufacturer_data.fw_revision = await self.device.read_gatt_char(
            self.UUID_FIRMWARE_REV
        )
        self.manufacturer_data.hw_revision = await self.device.read_gatt_char(
            self.UUID_HARDWARE_REV
        )
        self.manufacturer_data.soft_revision = await self.device.read_gatt_char(
            self.UUID_SOFTWARE_REV
        )

    async def current_readings(self) -> SensorData:
        """Extract current readings from remote device"""
        readings = SensorData()
        values = await self.device.read_gatt_char(self.UUID_GET_VALUES)
        readings.decode(values, False)
        self.last_values_read = datetime.now()
        return readings

    async def get_seconds_since_update(self) -> int:
        """
        Get the value for how long (in seconds) has passed since last
        datapoint was logged
        """
        current_time = datetime.now()
        delta = current_time - self.last_values_read
        return delta.seconds
