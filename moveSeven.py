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
posDict[16] = [-19.39896904, -11.20000000]
posDict[17] = [0, 0]
posDict[19] = [19.39896904, -11.20000000]
posDict[20] = [19.39896904, 11.20000000]
posDict[21] = [0, 22.4]
posDict[24] = [0, -22.4]
posDict[25] = [-19.39896904, 11.20000000]


# print("pos ids", posDict.keys())


def generatePath(seed=0, plot=False, movie=False):
    nDia = 3
    pitch = 22.4

    hasApogee = True
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

    for ii in range(rg.nRobots):
        r = rg.getRobot(ii)
        # print("loading pos %i [%.2f, %.2f]"%(r.id, r.xPos, r.yPos))
        # print("robotID", r.id)
        r.setXYUniform()
    # set all positioners randomly (they are initialized at 0,0)
    rg.decollide2()
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

    if movie:
        plotMovie(rg, filename="movie_%i"%seed)

    # find the positioner with the most interpolated steps
    forwardPath = {}
    reversePath = {}

    for robotID, r in zip(posDict.keys(), rg.allRobots):

        assert robotID == r.id
        if plot:
            plotTraj(r, "seed_%i_"%seed, dpi=250)

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

        # build forward path
        alphaTimesF = numpy.abs(alphaTimesR-alphaTimesR[-1])[::-1]
        alphaDegF = alphaDegR[::-1]
        betaTimesF = numpy.abs(betaTimesR-betaTimesR[-1])[::-1]
        betaDegF = betaDegR[::-1]

        armPathF = {} # reverse path
        armPathF["alpha"] = [(pos, time) for pos, time in zip(alphaDegF, alphaTimesF)]
        armPathF["beta"] = [(pos, time) for pos, time in zip(betaDegF, betaTimesF)]

        forwardPath[robotID] = armPathF

    return forwardPath, reversePath

async def main():

    # Set logging level to DEBUG
    log.set_level(50)

    # Initialise the FPS instance.
    fps = FPS(layout="grid7.txt")
    await fps.initialise()

    # Print the status of positioner 4
    # print("FPS status", fps[robotID].status)

    trialNumber = 0
    for seed in range(5000,40000):
        if trialNumber > 50:
            break

        print("moveSeven, seed=%i, collisionBuffer=%.4f"%(seed, collisionBuffer))
        try:
            fp, rp = generatePath(seed, plot=False)
        except:
            print("path deadlocked skip it")
            continue

        maxSteps = 0
        for abDict in fp.values():
            nPts = len(abDict["beta"])
            if nPts > maxSteps:
                maxSteps = nPts
        if maxSteps < 50:
            print("skipping un interesting path")
            continue

        print("max steps", maxSteps)

        # Send positioner 4 to alpha=0, beta=180 # path transfer position
        gotoHome = [fps[rID].goto(alpha=0, beta=180) for rID in posDict.keys()]
        await asyncio.gather(*gotoHome)

        print("forward path going")
        await fps.send_trajectory(fp, False)
        print("trajectory done")

        time.sleep(1)

        print("reverse path")
        await fps.send_trajectory(rp, False)
        print("trajectory done")
        trialNumber += 1

        # Cleanly finish all pending tasks and exit
    await fps.shutdown()

asyncio.run(main())

# fp, rp = generatePath(1, movie=True)

# print(fp)


