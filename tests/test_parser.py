import logging
from unittest.mock import patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import (
    DeviceClass,
    DeviceKey,
    SensorDescription,
    SensorDeviceInfo,
    SensorUpdate,
    SensorValue,
    Units,
)

from smartclim_ble.parser import BeeWiSmartClimBluetoothDeviceData

KEY_BATTERY = DeviceKey(key="battery", device_id=None)
KEY_TEMPERATURE = DeviceKey(key="temperature", device_id=None)
KEY_HUMIDITY = DeviceKey(key="humidity", device_id=None)


@pytest.fixture(autouse=True)
def logging_config(caplog):
    caplog.set_level(logging.DEBUG)


@pytest.fixture(autouse=True)
def mock_platform():
    with patch("sys.platform") as p:
        p.return_value = "linux"
        yield p


def bytes_to_service_info(
    payload: bytes | None, key: int, address: str = "00:00:00:00:00:00"
) -> BluetoothServiceInfo:
    manuf_data = {}
    if payload is not None:
        manuf_data[key] = payload

    return BluetoothServiceInfo(
        name="Test",
        address=address,
        rssi=-60,
        manufacturer_data=manuf_data,
        service_data={},
        service_uuids=[],
        source="",
    )


def test_can_create():
    BeeWiSmartClimBluetoothDeviceData()


def test_sensor_data_decode():
    # Advertising frame
    sensor = BeeWiSmartClimBluetoothDeviceData()

    assert sensor._parse_data(bytearray.fromhex("0500de00023b070000062e"), True) is True
    assert sensor.temperature == 22.2
    assert sensor.humidity == 59
    assert sensor.battery == 46

    # Connected frame
    assert sensor._parse_data(bytearray.fromhex("00de00023b070000062e"), False) is True
    assert sensor.temperature == 22.2
    assert sensor.humidity == 59
    assert sensor.battery == 46

    # Negatives temperatures
    assert sensor._parse_data(bytearray.fromhex("05003A000227070000062C"), True) is True
    assert sensor.temperature == 5.8
    assert sensor._parse_data(bytearray.fromhex("0500FDFF0228070000062C"), True) is True
    assert sensor.temperature == -0.2
    assert sensor._parse_data(bytearray.fromhex("0500EAFF0229070000062C"), True) is True
    assert sensor.temperature == -2.1

    # Wrong frame size
    assert sensor._parse_data(bytearray.fromhex("0500de00023b070000062e22")) is False


def test_sensor_data_get_manuf_data():
    ### Nominal case
    sensor = BeeWiSmartClimBluetoothDeviceData()
    data_string = b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"
    adv_data = bytes_to_service_info(data_string, key=13, address="2C:11:65:25:70:04")
    assert sensor.get_manufacturing_data(adv_data) == bytearray(
        b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"
    )

    data_string = b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"
    adv_data = bytes_to_service_info(data_string, key=15, address="2C:11:65:25:70:04")
    with pytest.raises(Exception):
        sensor.get_manufacturing_data(adv_data)


def test_sensor_data_supported():
    ### Nominal case
    sensor = BeeWiSmartClimBluetoothDeviceData()
    data_string = b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"
    adv_data = bytes_to_service_info(data_string, key=13, address="2C:11:65:25:70:04")
    assert sensor.supported(adv_data) is True

    ### Not corresponding cases
    # No manufacturing data
    adv_data = bytes_to_service_info(None, key=0, address="2C:11:65:25:70:04")
    assert sensor.supported(adv_data) is False

    # Wrong key in manufacturing data
    data_string = b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"
    adv_data = bytes_to_service_info(data_string, key=15, address="2C:11:65:25:70:04")
    assert sensor.supported(adv_data) is False

    # Wrong start byte in manufacturing data
    data_string = b"\x06\x00\x93\x00\x02V\x07\x00\x00\x06,"
    adv_data = bytes_to_service_info(data_string, key=13, address="2C:11:65:25:70:04")
    assert sensor.supported(adv_data) is False

    # Wrong manufacturing data size
    data_string = b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06\x07,"
    adv_data = bytes_to_service_info(data_string, key=13, address="2C:11:65:25:70:04")
    assert sensor.supported(adv_data) is False


def test_beewi_smartclim():
    """Test parser for XMWSDJ04MMC with encryption."""
    data_string = b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"
    advertisement = bytes_to_service_info(
        data_string, key=13, address="2C:11:65:25:70:04"
    )

    device = BeeWiSmartClimBluetoothDeviceData()
    assert device.supported(advertisement)
    assert device.update(advertisement) == SensorUpdate(
        title=None,
        devices={},
        entity_descriptions={
            KEY_TEMPERATURE: SensorDescription(
                device_key=KEY_TEMPERATURE,
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement="°C",
            ),
            KEY_HUMIDITY: SensorDescription(
                device_key=KEY_HUMIDITY,
                device_class=DeviceClass.HUMIDITY,
                native_unit_of_measurement="%",
            ),
            KEY_BATTERY: SensorDescription(
                device_key=KEY_BATTERY,
                device_class=DeviceClass.BATTERY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
        },
        entity_values={
            KEY_TEMPERATURE: SensorValue(
                name="Temperature", device_key=KEY_TEMPERATURE, native_value=14.7
            ),
            KEY_HUMIDITY: SensorValue(
                name="Humidity", device_key=KEY_HUMIDITY, native_value=86.0
            ),
            KEY_BATTERY: SensorValue(
                name="Battery", device_key=KEY_BATTERY, native_value=44
            ),
        },
    )
