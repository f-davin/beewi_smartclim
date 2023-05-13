import pytest

from smartclim_ble.parser import SensorData


def test_sensor_data_decode():
    # Advertising frame
    sensor = SensorData()
    sensor.decode(bytearray.fromhex("0500de00023b070000062e"), True)
    assert sensor.temperature == 22.2
    assert sensor.humidity == 59
    assert sensor.battery == 46

    # Connected frame
    sensor.decode(bytearray.fromhex("00de00023b070000062e"), False)
    assert sensor.temperature == 22.2
    assert sensor.humidity == 59
    assert sensor.battery == 46

    # Negatives temperatures
    sensor.decode(bytearray.fromhex("05003A000227070000062C"), True)
    assert sensor.temperature == 5.8
    sensor.decode(bytearray.fromhex("0500FDFF0228070000062C"), True)
    assert sensor.temperature == -0.2
    sensor.decode(bytearray.fromhex("0500EAFF0229070000062C"), True)
    assert sensor.temperature == -2.1

    # Wrong frame size
    with pytest.raises(Exception):
        sensor.decode(bytearray.fromhex("0500de00023b070000062e22"))
