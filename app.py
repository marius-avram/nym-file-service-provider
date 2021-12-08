import asyncio
from constants import Constants, Operations
from utils.service_provider_exception import ServiceProviderException
import websockets
import struct
import hashlib
import os

# request tags
SEND_REQUEST_TAG = 0x00
REPLY_REQUEST_TAG = 0x01
SELF_ADDRESS_REQUEST_TAG = 0x02

# response tags
ERROR_RESPONSE_TAG = 0x00
RECEIVED_RESPONSE_TAG = 0x01
SELF_ADDRESS_RESPONSE_TAG = 0x02


def make_self_address_request() -> bytes:
    return bytes([SELF_ADDRESS_REQUEST_TAG])


def parse_self_address_response(raw_response: bytes) -> bytes:
    if len(raw_response) != 97 or raw_response[0] != SELF_ADDRESS_RESPONSE_TAG:
        raise ServiceProviderException('Received invalid response')

    return raw_response[1:]


def make_send_request(recipient: bytes, message: bytes, with_reply_surb: bool) -> bytes:
    # a big endian uint64
    message_len = len(message).to_bytes(length=8, byteorder='big', signed=False)

    return bytes([SEND_REQUEST_TAG]) + bytes([with_reply_surb]) + recipient + message_len + message


def make_reply_request(message: bytes, reply_surb: bytes) -> bytes:
    message_len = len(message).to_bytes(length=8, byteorder='big', signed=False)
    surb_len = len(reply_surb).to_bytes(length=8, byteorder='big', signed=False)

    return bytes([REPLY_REQUEST_TAG]) + surb_len + reply_surb + message_len + message


# it should have structure of RECEIVED_RESPONSE_TAG || with_reply || (surb_len || surb) || msg_len || msg
# where surb_len || surb is only present if 'with_reply' is true
def parse_received(raw_response: bytes) -> tuple([bytes, bytes, bytes]):
    if raw_response[0] != RECEIVED_RESPONSE_TAG:
        raise ServiceProviderException('Received invalid response!')

    if raw_response[1] == 1:
        has_surb = True
    elif raw_response[1] == 0:
        has_surb = False
    else:
        raise ServiceProviderException('Received invalid response!')

    data = raw_response[2:]
    if has_surb:
        (surb_len,), other = struct.unpack(">Q", data[:8]), data[8:]
        surb = other[:surb_len]
        (msg_len,) = struct.unpack(">Q", other[surb_len:surb_len + 8])

        if len(other[surb_len + 8:]) != msg_len:
            raise ServiceProviderException("invalid msg len")
        operation = other[surb_len+8]
        msg = other[surb_len + 9:]
        return operation, msg, surb
    else:
        (msg_len,), other = struct.unpack(">Q", data[:8]), data[8:]
        if len(other) != msg_len:
            raise ServiceProviderException("invalid msg len")
        operation = other[0]
        msg = other[1:msg_len]
        return operation, msg, None

def compute_raw_data_md5sum(raw_data: bytes) -> str:
    return hashlib.md5(raw_data).hexdigest()

def save_received_file(received_data):
    filename = compute_raw_data_md5sum(received_data)
    file_path = Constants.UPLOAD_DIR + filename
    with open(file_path, "wb") as output_file:
        print("writing the file back to the disk!")
        output_file.write(received_data)

def read_file(md5sum: bytes):
    filename = md5sum.decode('utf-8')
    print("reading file {}".format(md5sum))
    file_path = Constants.UPLOAD_DIR + filename
    file_content = None
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            file_content = file.read()
    return file_content

def delete_file(md5sum: bytes):
    filename = md5sum.decode('utf-8')
    print("deleting file {}".format(md5sum))
    file_path = Constants.UPLOAD_DIR + filename
    if os.path.exists(file_path):
        os.remove(file_path)

async def main_loop():
    uri = "ws://localhost:1977"
    async with websockets.connect(uri) as websocket:
        while True:
            print("waiting to receive a message from the mix network...")
            received_response = await websocket.recv()
            operation, received_data, surb = parse_received(received_response)
            print ("operation {}".format(operation))
            
            if operation == Operations.WRITE_FILE:
                save_received_file(received_data)
                reply_ok = make_reply_request(b'OK', surb)
                print("sending a reply back")
                await websocket.send(reply_ok)
                print("reply sent")
            elif operation == Operations.READ_FILE:
                file_content = read_file(received_data)
                reply_message_with_file = make_reply_request(file_content, surb)
                print("sending a reply back")
                await websocket.send(reply_message_with_file)
                print("reply sent")
            elif operation == Operations.DELETE_FILE:
                delete_file(received_data)

asyncio.get_event_loop().run_until_complete(main_loop())
