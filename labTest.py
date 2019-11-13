# import asyncio

# from jaeger.can import JaegerCAN
# from jaeger.positioner import Positioner

# ./jaeger --no-tron --layout ../python/jaeger/etc/fps_RTConfig.txt

from jaeger.utils import motor_steps_to_angle, bytes_to_int, int_to_bytes, get_identifier, parse_identifier
from jaeger.interfaces.cannet import CANNetBus
import can
import time
from jaeger.maskbits import PositionerStatus
import numpy

# from can.interfaces.interface import Bus

GET_ID = 1
GET_FIRMWARE_VERSION = 2
GET_STATUS = 3
SEND_NEW_TRAJECTORY = 10
SEND_TRAJECTORY_DATA = 11
TRAJECTORY_DATA_END = 12
TRAJECTORY_TRANSMISSION_ABORT = 13
START_TRAJECTORY = 14
STOP_TRAJECTORY = 15
INITIALIZE_DATUMS = 20
GO_TO_ABSOLUTE_POSITION = 30
GO_TO_RELATIVE_POSITION = 31
GET_ACTUAL_POSITION = 32
SET_ACTUAL_POSITION = 33
SET_SPEED = 40
START_FIRMWARE_UPGRADE = 200
SEND_FIRMWARE_DATA = 201

bitrate = 1000000

canBus = CANNetBus("192.168.1.31", bitrate=bitrate)
# clear the 4 'r ok' responses
canBus.recv(1)
canBus.recv(1)
canBus.recv(1)
canBus.recv(1)


def sendMsg(commandID, positioner_id=0, data=None):
    if data is None:
        data = []
    response_code = 0
    uid = 1
    arbID = get_identifier(
        positioner_id,
        int(commandID),
        uid=uid,
        response_code=response_code,
    )
    msg = can.Message(
        arbitration_id=arbID,
        data=data,
        extended_id=True,
    )
    canBus.send(msg)
    return msg


def getReply():
    reply = canBus.recv(1)
    arb = parse_identifier(reply.arbitration_id)
    data = reply.data
    return arb, data


def findPositioners():
    sendMsg(GET_ID)
    posIDs = []
    while True:
        try:
            arb, data = getReply()
            posIDs.append(arb[0])
        except:
            # timeed out no data
            break
    return posIDs

def getPosition(posID):
    sendMsg(GET_ACTUAL_POSITION, posID)
    arb, data = getReply()
    assert arb[0] == posID
    beta = bytes_to_int(data[4:])
    alpha = bytes_to_int(data[0:4])
    return alpha, beta


def gotoPosition(posID, alphaDeg, betaDeg):
    alpha_steps, beta_steps = motor_steps_to_angle(alphaDeg, betaDeg, inverse=True)
    data = int_to_bytes(alpha_steps) + int_to_bytes(beta_steps)
    sendMsg(GO_TO_ABSOLUTE_POSITION, posID, data)
    arb, data = getReply()
    betaTime = bytes_to_int(data[4:])
    alphaTime = bytes_to_int(data[0:4])
    assert arb[0] == posID
    print("times to move", betaTime * 0.0005, alphaTime * 0.0005)


# print("socket clear", canBus._socket.recv(8192))

# canBus.send(msg)

# while True:
#     try:
#         answer = canBus.recv(1) # one second timeout
#     except:
#         break
#     arb = parse_identifier(answer.arbitration_id)
#     if int(arb[0]) == 0:
#         continue
#     data = int(bytes_to_int(answer.data))
#     ps = PositionerStatus(data)
#     # print("status", ps)
#     print('answer', arb, ps)

# msg = can.Message(
#     arbitration_id=formatArbID(GET_ACTUAL_POSITION, positioner_id=23),
#     data=[],
#     extended_id=True,
# )

# print("sending get position")
# canBus.send(msg)

# while True:
#     try:
#         answer = canBus.recv(1) # one second timeout
#     except:
#         break
#     arb = parse_identifier(answer.arbitration_id)
#     if arb[0] == 0:
#         continue
#     data = bytes_to_int(answer.data)
#     # print("status", ps)
#     print('answer', arb, data)

# print("here")

if __name__ == "__main__":
    posIDs = findPositioners()
    alphaPos = []
    betaPos = []
    for posID in posIDs:
        getPosition(posID)
        gotoPosition(posID, 100, 100)




# for reply in canBus:
#     print("reply", reply.arbitration_id)


# print("msg", msg)

# canBus.send(msg)

# time.sleep(1)

# for i in range(5):
#     answer = canBus.recv(4)
#     if answer:
#         print("answer", answer.data)
#         break



# interface = "cannet"
# channels: [192.168.0.10]
# port: 19228
# buses: [1, 2, 3, 4]
# bitrate: 1000000

# command_queue = asyncio.Queue()

# INTERFACES = {
#     'slcan': {
#         'class': can.interfaces.slcan.slcanBus,
#         'multibus': False
#     },
#     'socketcan': {
#         'class': can.interfaces.socketcan.SocketcanBus,
#         'multibus': False
#     },
#     'virtual': {
#         'class': can.interfaces.virtual.VirtualBus,
#         'multibus': False
#     },
#     'cannet': {
#         'class': jaeger.interfaces.cannet.CANNetBus,
#         'multibus': True
#     }
# }

# self.interfaces[0].send(message)

# self.interfaces.append(InterfaceClass(channel, *args, **kwargs))

# loop = asyncio.get_event_loop()
# cat = JaegerCAN.from_profile(can_profile, loop=loop)


"""
reading: R ok
reading: R ok
reading: R ok
reading: R ok
sending: M 1 CED 00000410
reading: M 1 CED 5C0410 17 00 00 00
sending: M 1 CED 005C8010
reading: M 1 CED 5C8010 72 1C C7 11 72 1C C7 11
sending: M 1 CED 005C7810 00 00 00 00 00 00 00 00
reading: M 1 CED 5C7810 55 85 00 00 55 85 00 00
times to move 17.0665 17.0665
Conors-MacBook-Pro:bin csayres$ python labTest.py
reading: R ok
reading: R ok
reading: R ok
reading: R ok
sending: M 1 CED 00000410
reading: M 1 CED 5C0410 17 00 00 00
sending: M 1 CED 005C8010
reading: M 1 CED 5C8010 00 00 00 00 00 00 00 00
sending: M 1 CED 005C7810 72 1C C7 11 72 1C C7 11
reading: M 1 CED 5C7810 55 85 00 00 55 85 00 00
times to move 17.0665 17.0665
"""
