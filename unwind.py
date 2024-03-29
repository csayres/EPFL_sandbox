import asyncio
from jaeger import FPS, log
import time

from kaiju import RobotGrid, utils
import matplotlib.pyplot as plt
import numpy

import pickle
from collections import OrderedDict

from trajPlotter import plotTraj

from movieExample import plotMovie

# seed 7 robot 0 is problematic (truncation on beta didn't work)
# seed 529 smoothing failed with  78

MaxSpeed = 4 # RPM
RobotMaxSpeed = (MaxSpeed)*360/60. # degrees per sec (3 RPM)
angStep = 0.05 # degrees per step
smoothPts = 5
epsilon = angStep * 2
collisionBuffer = 2
collisionShrink = 0.02
nSavedPaths = 50
makeNewPaths = False
doPlot = False
# posList = [19, 20, 24, 17, 21, 16, 25]
# time = angStep * stepNum / speed
# hack make sure these are sorted by
posDict = OrderedDict()

# these are 'perfect'
# posDict[16] = [-19.39896904, -11.20000000]
# posDict[17] = [0, 0]
# posDict[19] = [19.39896904, -11.20000000]
# posDict[20] = [19.39896904, 11.20000000]
# posDict[21] = [0, 22.4]
# posDict[24] = [0, -22.4]
# posDict[25] = [-19.39896904, 11.20000000]

# these are calibration outputs measured in mm from top left
centerPositioner = 17
posDict[16] = numpy.array([50.33, -26.13])
posDict[17] = numpy.array([61.38, -45.77])
posDict[19] = numpy.array([50.08, -64.74])
posDict[20] = numpy.array([72.56, -64.95])
posDict[21] = numpy.array([83.87, -45.58])
posDict[24] = numpy.array([38.98, -45.43])
posDict[25] = numpy.array([72.78, -26.42])

centerXY = posDict[centerPositioner]

c90 = numpy.cos(numpy.radians(90))
s90 = numpy.sin(numpy.radians(90))
rotMat = numpy.array([
    [c90, s90],
    [-s90, c90]
])
for key in posDict.keys():
    fromMiddle = posDict[key] - centerXY
    posDict[key] = numpy.dot(fromMiddle, rotMat)
    # print("pos", key, posDict[key])


# print("pos ids", posDict.keys())

async def main():

    # Set logging level to DEBUG
    #log.set_level(20)

    # Initialise the FPS instance.
    fps = FPS(layout="grid7.txt")
    await fps.initialise()

    hasApogee = True
    seed = 0 # ignored we're setting ppositions manually
    rg = RobotGrid(angStep, collisionBuffer, epsilon, seed)

    # epfl grid is sideways
    # xPos, yPos = utils.hexFromDia(nDia, pitch=pitch)
    # for ii, (xp, yp), posID in enumerate(zip(xPos, yPos, posList)):
    #     rg.addRobot(posID, xp, yp, hasApogee)
    # rg.initGrid()

    for posID, (xp,yp) in posDict.items():
        # print("loading pos %i [%.2f, %.2f]"%(posID, xp, yp))
        rg.addRobot(posID, xp, yp, hasApogee)
    rg.initGrid()

    #print("fps.positioners", fps.positioners)
    for ii in range(rg.nRobots):
        r = rg.getRobot(ii)
        # print("loading pos %i [%.2f, %.2f]"%(r.id, r.xPos, r.yPos))
        # print("robotID", r.id)
        await fps.positioners[r.id].update_position()
        alpha, beta = fps.positioners[r.id].position
        print("IIII", r.id, alpha, beta)
        r.setAlphaBeta(alpha, beta)
    # set all positioners randomly (they are initialized at 0,0)
    # rg.decollide2()
    rg.pathGen()
    if rg.didFail:
        print("path gen failed")
        raise(RuntimeError, "path gen failed")
    rg.smoothPaths(smoothPts)
    rg.simplifyPaths()
    rg.setCollisionBuffer(collisionBuffer - collisionShrink)
    rg.verifySmoothed()

    if rg.smoothCollisions:
        print("smoothing failed with ", rg.smoothCollisions)
        raise(RuntimeError, "smoothing failed")

    # find the positioner with the most interpolated steps
    reversePath = {}

    for robotID, r in zip(posDict.keys(), rg.allRobots):

        assert robotID == r.id

        # bp = numpy.array(r.betaPath)
        # sbp = numpy.array(r.interpSmoothBetaPath)
        ibp = numpy.array(r.simplifiedBetaPath)

        # ap = numpy.array(r.alphaPath)
        # sap = numpy.array(r.interpSmoothAlphaPath)
        iap = numpy.array(r.simplifiedAlphaPath)

        # generate kaiju trajectory (for robot 23)
        # time = angStep * stepNum / speed

        alphaTimesR = iap[:,0] * angStep / RobotMaxSpeed
        alphaDegR = iap[:,1]
        betaTimesR = ibp[:,0] * angStep / RobotMaxSpeed
        betaDegR = ibp[:,1]

        armPathR = {} # reverse path
        armPathR["alpha"] = [(pos, time) for pos, time in zip(alphaDegR, alphaTimesR)]
        armPathR["beta"] = [(pos, time) for pos, time in zip(betaDegR, betaTimesR)]

        reversePath[robotID] = armPathR


    await fps.send_trajectory(reversePath)
    await fps.shutdown()


asyncio.run(main())




