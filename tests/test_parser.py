import pytest
from bleak.backends.scanner import AdvertisementData

from smartclim_ble.parser import SmartClimSensorData


def test_sensor_data_decode():
    # Advertising frame
    sensor = SmartClimSensorData()
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


def test_sensor_data_supported():
    ### Nominal case
    sensor = SmartClimSensorData()
    adv_data = AdvertisementData(
        local_name="089352809434933736",
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=-82,
        manufacturer_data={13: b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"},
        platform_data=(
            "/org/bluez/hci0/dev_F0_C7_7F_85_71_EF",
            {
                "Address": "F0:C7:7F:85:71:EF",
                "AddressType": "public",
                "Name": "089352809434933736",
                "Alias": "089352809434933736",
                "Paired": False,
                "Trusted": False,
                "Blocked": False,
                "LegacyPairing": False,
                "RSSI": -82,
            },
        ),
    )
    assert sensor.supported_data(adv_data) is True

    ### Not corresponding cases
    # No manufacturing data
    adv_data = AdvertisementData(
        local_name="089352809434933736",
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=-82,
        manufacturer_data={},
        platform_data=(
            "/org/bluez/hci0/dev_F0_C7_7F_85_71_EF",
            {
                "Address": "F0:C7:7F:85:71:EF",
                "AddressType": "public",
                "Name": "089352809434933736",
                "Alias": "089352809434933736",
                "Paired": False,
                "Trusted": False,
                "Blocked": False,
                "LegacyPairing": False,
                "RSSI": -82,
            },
        ),
    )
    assert sensor.supported_data(adv_data) is False

    # Wrong key in manufacturing data
    adv_data = AdvertisementData(
        local_name="089352809434933736",
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=-82,
        manufacturer_data={15: b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"},
        platform_data=(
            "/org/bluez/hci0/dev_F0_C7_7F_85_71_EF",
            {
                "Address": "F0:C7:7F:85:71:EF",
                "AddressType": "public",
                "Name": "089352809434933736",
                "Alias": "089352809434933736",
                "Paired": False,
                "Trusted": False,
                "Blocked": False,
                "LegacyPairing": False,
                "RSSI": -82,
            },
        ),
    )
    assert sensor.supported_data(adv_data) is False

    # Wrong start byte in manufacturing data
    adv_data = AdvertisementData(
        local_name="089352809434933736",
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=-82,
        manufacturer_data={13: b"\x06\x00\x93\x00\x02V\x07\x00\x00\x06,"},
        platform_data=(
            "/org/bluez/hci0/dev_F0_C7_7F_85_71_EF",
            {
                "Address": "F0:C7:7F:85:71:EF",
                "AddressType": "public",
                "Name": "089352809434933736",
                "Alias": "089352809434933736",
                "Paired": False,
                "Trusted": False,
                "Blocked": False,
                "LegacyPairing": False,
                "RSSI": -82,
            },
        ),
    )
    assert sensor.supported_data(adv_data) is False

    # Wrong manufacturing data size
    adv_data = AdvertisementData(
        local_name="089352809434933736",
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=-82,
        manufacturer_data={13: b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06\x07,"},
        platform_data=(
            "/org/bluez/hci0/dev_F0_C7_7F_85_71_EF",
            {
                "Address": "F0:C7:7F:85:71:EF",
                "AddressType": "public",
                "Name": "089352809434933736",
                "Alias": "089352809434933736",
                "Paired": False,
                "Trusted": False,
                "Blocked": False,
                "LegacyPairing": False,
                "RSSI": -82,
            },
        ),
    )
    assert sensor.supported_data(adv_data) is False


def test_sensor_data_get_manuf_data():
    ### Nominal case
    sensor = SmartClimSensorData()
    adv_data = AdvertisementData(
        local_name="089352809434933736",
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=-82,
        manufacturer_data={13: b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"},
        platform_data=(
            "/org/bluez/hci0/dev_F0_C7_7F_85_71_EF",
            {
                "Address": "F0:C7:7F:85:71:EF",
                "AddressType": "public",
                "Name": "089352809434933736",
                "Alias": "089352809434933736",
                "Paired": False,
                "Trusted": False,
                "Blocked": False,
                "LegacyPairing": False,
                "RSSI": -82,
            },
        ),
    )
    assert sensor.get_manufacturing_data(adv_data) == bytearray(
        b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"
    )

    adv_data = AdvertisementData(
        local_name="089352809434933736",
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=-82,
        manufacturer_data={15: b"\x05\x00\x93\x00\x02V\x07\x00\x00\x06,"},
        platform_data=(
            "/org/bluez/hci0/dev_F0_C7_7F_85_71_EF",
            {
                "Address": "F0:C7:7F:85:71:EF",
                "AddressType": "public",
                "Name": "089352809434933736",
                "Alias": "089352809434933736",
                "Paired": False,
                "Trusted": False,
                "Blocked": False,
                "LegacyPairing": False,
                "RSSI": -82,
            },
        ),
    )
    with pytest.raises(Exception):
        sensor.get_manufacturing_data(adv_data)
