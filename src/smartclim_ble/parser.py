"""Parser for BeeWi SmartClim BLE devices"""

from dataclasses import dataclass
from typing import Optional

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


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
        frame_length = 10
        offset = 0
        if is_adv_data:
            frame_length = 13
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


@dataclass
class BeeWiSmartClimAdvertisement:
    """Class to realize the treatment of an advertising frame."""

    device: Optional[BLEDevice] = None
    readings: Optional[SensorData] = None

    def __init__(
        self,
        device: Optional[BLEDevice] = None,
        ad_data: Optional[AdvertisementData] = None,
    ):
        """Constructor."""
        self.device = device

        if device and ad_data:
            self.readings = SensorData()
            self.readings.name = device.name
            data = ad_data.manufacturer_data
            key = list(data.keys())[0]
            self.readings.decode(data[key])
