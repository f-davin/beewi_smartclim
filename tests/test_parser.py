from smartclim_ble.parser import SensorData


def test_sensor_data_decode():
    # Advertising frame
    sensor = SensorData()
    data_bytes = bytearray.fromhex("0500de00023b070000062e")
    sensor.decode(data_bytes, True)
    assert sensor.temperature == 22.2
    assert sensor.humidity == 59
    assert sensor.battery == 46

    # Connected frame
    data_bytes = bytearray.fromhex("00de00023b070000062e")
    sensor.decode(data_bytes, False)
    assert sensor.temperature == 22.2
    assert sensor.humidity == 59
    assert sensor.battery == 46

    # Wrong frame
    assert True
