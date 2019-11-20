import asyncio
from jaeger import FPS, log
import time

from kaiju import RobotGrid
import matplotlib.pyplot as plt
import numpy
from collections import OrderedDict

from trajPlotter import plotTraj
from movieExample import plotMovie
from calibLoic import csCam
import PyGuide

# seed 7 robot 0 is problematic (truncation on beta didn't work)
# seed 529 smoothing failed with  78

MaxSpeed = 4 # RPM
RobotMaxSpeed = (MaxSpeed)*360/60. # degrees per sec (3 RPM)
angStep = 0.05 # degrees per step
smoothPts = 5
epsilon = angStep * 2
collisionBuffer = 2
collisionShrink = 0.02
doPlot = False
roiRadius = 50

CCDInfo = PyGuide.CCDInfo(
    bias = 2,    # image bias, in ADU
    readNoise = 2, # read noise, in e-
    ccdGain = 2,  # inverse ccd gain, in e-/ADU
)

def getGetPositionerData():
    posDict = OrderedDict()

    # these are calibration outputs measured in mm from top left
    # centerXY = numpy.array([50.33, -45.66])
    posDict[16] = numpy.array([50.33, -26.13])
    posDict[17] = numpy.array([61.39, -45.68]) # center
    posDict[19] = numpy.array([50.08, -64.74])
    posDict[20] = numpy.array([72.56, -64.95])
    posDict[21] = numpy.array([83.87, -45.58])
    posDict[24] = numpy.array([38.95, -45.28])
    posDict[25] = numpy.array([72.78, -26.42])

    centerXY = posDict[17]
    # rotate grid such that it is aligned with
    # kaiju's definition (alpha=0 is aligned with +x)
    c90 = numpy.cos(numpy.radians(90))
    s90 = numpy.sin(numpy.radians(90))
    rotMat = numpy.array([
        [c90, s90],
        [-s90, c90]
    ])
    for key in posDict.keys():
        fromMiddle = posDict[key] - centerXY
        posDict[key] = numpy.dot(fromMiddle, rotMat)
        print("pos", key, posDict[key])
    return posDict

posDict = getGetPositionerData()

def newGrid(seed=0):
    hasApogee = True
    rg = RobotGrid(angStep, collisionBuffer, epsilon, seed)

    for posID, (xp, yp) in posDict.items():
        rg.addRobot(posID, xp, yp, hasApogee)
    rg.initGrid()

    for ii in range(rg.nRobots):
        r = rg.getRobot(ii)
        r.setXYUniform()
    rg.decollide2()
    return rg

def homeGrid():
    hasApogee = True
    seed = 0
    rg = RobotGrid(angStep, collisionBuffer, epsilon, seed)

    for posID, (xp, yp) in posDict.items():
        rg.addRobot(posID, xp, yp, hasApogee)
    rg.initGrid()

    for ii in range(rg.nRobots):
        r = rg.getRobot(ii)
        r.setAlphaBeta(0, 180)
    rg.decollide2()
    return rg

def getTargetPositions(rg):
    ## return target positions for positioners in mm
    # in kaiju's coord system (mm)
    targetPositions = OrderedDict()
    for r in rg.allRobots:
        x, y, z = r.metFiberPos
        targetPositions[r.id] = [x, y]
    return targetPositions


def generatePath(rg, plot=False, movie=False, fileIndex=0):

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
        plotMovie(rg, filename="movie_%i"%fileIndex)

    # find the positioner with the most interpolated steps
    forwardPath = {}
    reversePath = {}

    for robotID, r in zip(posDict.keys(), rg.allRobots):

        assert robotID == r.id
        if plot:
            plotTraj(r, "seed_%i_"%fileIndex, dpi=250)

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

def centroid(imgData, xyExpect):
    # xy center in mm kaiju coord sys
    mask = numpy.zeros(imgData.shape) + 1




async def main():

    # Set logging level to DEBUG
    log.set_level(20)

    # Initialise the FPS instance.
    # fps = FPS(layout="grid7.txt")
    fps = FPS()
    await fps.initialise()

    # Print the status of positioner 4
    # print("FPS status", fps[robotID].status)

    trialNumber = 0
    seed = 0
    logFile = open("moveSevenCamera.log", "w")
    while True:
        seed += 1
        rg = newGrid(seed)

        # grab the targets
        targetPositions = getTargetPositions(rg)

        print("moveSeven, seed=%i, collisionBuffer=%.4f"%(seed, collisionBuffer))
        try:
            fp, rp = generatePath(rg, plot=False, movie=False, fileIndex=seed)
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

        # send all to 0 180
        gotoHome = [fps[rID].goto(alpha=0, beta=180) for rID in posDict.keys()]
        await asyncio.gather(*gotoHome)

        logFile.write("starting forward trajectory seed=%i trial=%i collisionBuffer=%.2f\n"%(seed, trialNumber, collisionBuffer))

        print("forward path going")
        await fps.send_trajectory(fp, False)
        print("trajectory done")
        time.sleep(1)
        # measure the positions of all the guys

        imgData = csCam.camera.getImage()



        logFile.write("starting reverse trajectory seed=%i trial=%i collisionBuffer=%.2f\n"%(seed, trialNumber, collisionBuffer))

        print("reverse path")
        await fps.send_trajectory(rp, False)
        print("trajectory done")
        trialNumber += 1

        if fps.locked:
            logFile.write("FPS is locked! exiting\n")
        # Cleanly finish all pending tasks and exit
    await fps.shutdown()
    logFile.close()

# asyncio.run(main())
rg = homeGrid()

# fp, rp = generatePath(1, movie=True)

# print(fp)


