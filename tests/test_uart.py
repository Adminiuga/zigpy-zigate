from unittest import mock

import pytest
import serial_asyncio

from zigpy_zigate import uart


@pytest.fixture
def gw():
    gw = uart.Gateway(mock.MagicMock())
    gw._transport = mock.MagicMock()
    return gw


@pytest.mark.asyncio
async def test_connect(monkeypatch):
    api = mock.MagicMock()
    portmock = mock.MagicMock()

    async def mock_conn(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_soon(protocol.connection_made, None)
        return None, protocol
    monkeypatch.setattr(serial_asyncio, 'create_serial_connection', mock_conn)

    await uart.connect(portmock, 115200, api)


def test_send(gw):
    data = b'\x00'
    gw.send(data)
    assert gw._transport.write.call_count == 1
    assert gw._transport.write.called_once_with(data)


def test_close(gw):
    gw.close()
    assert gw._transport.close.call_count == 1


def test_data_received_chunk_frame(gw):
    data = b'\x01\x80\x10\x02\x10\x02\x15\xaa\x02\x10\x02\x1f?\xf0\xff\x03'
    gw.data_received(data[:-4])
    assert gw._api.data_received.call_count == 0
    gw.data_received(data[-4:])
    assert gw._api.data_received.call_count == 1
#     assert gw._api.data_received.call_args[0][0] == data[:-3]


def test_data_received_full_frame(gw):
    data = b'\x01\x80\x10\x02\x10\x02\x15\xaa\x02\x10\x02\x1f?\xf0\xff\x03'
    gw.data_received(data)
    assert gw._api.data_received.call_count == 1
#     assert gw._api.data_received.call_args[0][0] == data[:-3]


def test_data_received_incomplete_frame(gw):
    data = b'~\x00\x00'
    gw.data_received(data)
    assert gw._api.data_received.call_count == 0


def test_data_received_runt_frame(gw):
    data = b'\x02\x44\xC0'
    gw.data_received(data)
    assert gw._api.data_received.call_count == 0


def test_data_received_extra(gw):
    data = b'\x01\x80\x10\x02\x10\x02\x15\xaa\x02\x10\x02\x1f?\xf0\xff\x03\x00'
    gw.data_received(data)
    assert gw._api.data_received.call_count == 1
#     assert gw._api.data_received.call_args[0][0] == data[:-4]
    assert gw._buffer == b'\x00'


def test_data_received_wrong_checksum(gw):
    data = b'\x01\x80\x10\x02\x10\x02\x15\xab\x02\x10\x02\x1f?\xf0\xff\x03'
    gw.data_received(data)
    assert gw._api.data_received.call_count == 0


def test_unescape(gw):
    data = b'\x80\x10\x02\x10\x02\x15\xaa\x02\x10\x02\x1f?\xf0\xff'
    data_unescaped = b'\x80\x10\x00\x05\xaa\x00\x0f?\xf0\xff'
    r = gw._unescape(data)
    assert r == data_unescaped


def test_escape(gw):
    data = b'\x80\x10\x00\x05\xaa\x00\x0f?\xf0\xff'
    data_escaped = b'\x80\x10\x02\x10\x02\x15\xaa\x02\x10\x02\x1f?\xf0\xff'
    r = gw._escape(data)
    assert r == data_escaped


def test_length(gw):
    data = b'\x80\x10\x00\x05\xaa\x00\x0f?\xf0\xff'
    length = 5
    r = gw._length(data)
    assert r == length


def test_checksum(gw):
    data = b'\x80\x10\x00\x05\xaa\x00\x0f?\xf0\xff'
    checksum = 0xaa
    r = gw._checksum(data)
    assert r == checksum
