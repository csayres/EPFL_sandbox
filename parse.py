import re
GO_TO_ABSOLUTE_POSITION = 30
GET_ACTUAL_POSITION = 32

replyRE = re.compile(r'^M 1 CED (?P<arbID>\w+)\s?(?P<data>[\w\w\s?]*)$', re.IGNORECASE)

inputs = [
    "R ok",
    "R ok",
    "R ok",
    "R ok",
    "M 1 CED 5C0410 17 00 00 00",
    "M 1 CED 5C8010 72 1C C7 11 72 1C C7 11",
    "M 1 CED 5C7810 55 85 00 00 55 85 00 00",
    "R ok",
    "R ok",
    "R ok",
    "R ok",
    "M 1 CED 5C0410 17 00 00 00",
    "M 1 CED 5C8010 00 00 00 00 00 00 00 00",
    "M 1 CED 5C7810 55 85 00 00 55 85 00 00",
    "M 1 CED 5C7810",
]

def parseHexData(hexData, cmdID):
    hexData = hexData.replace(" ", "")
    binIffied = bin(int(hexData,16))[2:].zfill(64)
    if cmdID == GO_TO_ABSOLUTE_POSITION:
        # parse as times
        alphaTime = int(binIffied[:32], 2)
        betaTime = int(binIffied[32:], 2)
        print("times", alphaTime*0.0005, betaTime*0.0005)
    print("len", len(binIffied))


def positionsFromHexData(hexData):
    pass

def arbFromHex(arbHex):
    numBits = 29
    binIffied = bin(int(arbHex, 16))[2:].zfill(numBits)
    positioner = int(binIffied[0:11], 2)
    commandID = int(binIffied[11:19], 2)
    uid = int(binIffied[19:25], 2)
    responseCode = int(binIffied[25:], 2)
    return positioner, commandID, uid, responseCode

def hexFromArb(positioner, commandID, uid, responseCode):
    posid_bin = format(positioner, '011b')
    cid_bin = format(commandID, '08b')
    cuid_bin = format(uid, '06b')
    response_bin = format(responseCode, '04b')
    identifier = posid_bin + cid_bin + cuid_bin + response_bin
    return hex(int(identifier,2))[2:].upper()


def parseLine(line):
    out = replyRE.match(inp)
    if out is None:
        return None
    arbID = out.group("arbID")
    data = out.group("data")
    po, c, u, r = arbFromHex(arbID)
    if data:
        parseHexData(data, c)


    # arbOut = hexFromArb(po, c, u, r)
    # print("pos", po, "command", c, "uid", u, "response", r)
    # return out.group("arbID"), out.group("data")


for inp in inputs:
    out = parseLine(inp)
    print(out)


