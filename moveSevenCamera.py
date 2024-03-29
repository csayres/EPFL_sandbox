import sys
import os
import matplotlib


import asyncio
from jaeger import FPS, log
import time

from kaiju import RobotGrid
import matplotlib.pyplot as plt
import numpy
from collections import OrderedDict
import pickle

from trajPlotter import plotTraj
from movieExample import plotMovie
import PyGuide

tendoPath = "/home/tendo/work/python/EPFL_sandbox/calibLoic"
if os.path.exists(tendoPath):
    sys.path.append(tendoPath)
    from calibLoic import csCam
    scaleFac = csCam.SCALE_FACTOR
    matplotlib.use("TkAgg")
else:
    scaleFac = 0.033333 # MM / px
    matplotlib.use("macosx")

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
nImgAvg = 4

# set roi width to 0.5 mm (within a beta arm)
# we should only get one detection
roiRadiusMM = 0.75
roiRadiusPx = int(numpy.floor(roiRadiusMM / scaleFac))
print("roi Radius", roiRadiusPx)
detectThresh = 150

CCDInfo = PyGuide.CCDInfo(
    bias = 2,    # image bias, in ADU
    readNoise = 2, # read noise, in e-
    ccdGain = 2,  # inverse ccd gain, in e-/ADU
)

c90 = numpy.cos(numpy.radians(90))
s90 = numpy.sin(numpy.radians(90))
rot2kaiju = numpy.array([
    [c90, s90],
    [-s90, c90]
])
rot2image = numpy.array([
    [c90, -s90],
    [s90, c90]
])

centerPositioner = 17

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

    centerXY = posDict[centerPositioner]
    # rotate grid such that it is aligned with
    # kaiju's definition (alpha=0 is aligned with +x)
    for key in posDict.keys():
        fromMiddle = posDict[key] - centerXY
        posDict[key] = numpy.dot(fromMiddle, rot2kaiju)
        # print("pos", key, posDict[key])
    return centerXY, posDict

centerXYMM, posDict = getGetPositionerData()

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

def safeGrid():
    hasApogee = True
    seed = 0
    rg = RobotGrid(angStep, collisionBuffer, epsilon, seed)

    for posID, (xp, yp) in posDict.items():
        rg.addRobot(posID, xp, yp, hasApogee)
    rg.initGrid()

    for ii in range(rg.nRobots):
        r = rg.getRobot(ii)
        r.setAlphaBeta(45, 90)
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


        # add time buffer for the reverse path, because we are
        # iterating final placement after the forward path
        # this ensures the robot first moves to the position
        # computed by kaiju before following the folding path.
        armPathR = {} # reverse path
        armPathR["alpha"] = [(pos, time+0.5) for pos, time in zip(alphaDegR, alphaTimesR)]
        armPathR["beta"] = [(pos, time+0.5) for pos, time in zip(betaDegR, betaTimesR)]

        reversePath[robotID] = armPathR

        # build forward path
        alphaTimesF = numpy.abs(alphaTimesR-alphaTimesR[-1])[::-1]
        alphaDegF = alphaDegR[::-1]
        betaTimesF = numpy.abs(betaTimesR-betaTimesR[-1])[::-1]
        betaDegF = betaDegR[::-1]

        armPathF = {}
        armPathF["alpha"] = [(pos, time) for pos, time in zip(alphaDegF, alphaTimesF)]
        armPathF["beta"] = [(pos, time) for pos, time in zip(betaDegF, betaTimesF)]


        forwardPath[robotID] = armPathF

    return forwardPath, reversePath

def centroid(imgData, positionerTargetsMM, plot=False):
    # xy center in mm kaiju coord sys
    imgData = imgData[::-1,:]
    numCols, numRows = imgData.shape
    mask = numpy.zeros(imgData.shape) + 1
    # build the mask, draw squares around expected positions
    positionerTargetsPx = OrderedDict()
    for posID, xyKaijuMM in positionerTargetsMM.items():
        # take abs value of positioner because it's y axis is defined
        # negative (loic's positions are measured from top left)
        xyImageMM = numpy.dot(xyKaijuMM, rot2image) + numpy.abs(centerXYMM)
        xTargetPx, yTargetPx = xyImageMM / scaleFac
        positionerTargetsPx[posID] = numpy.array([xTargetPx, yTargetPx])
        # rotate into reference frame with 0,0 at bottom left
        xROI = numpy.int(numpy.floor(xTargetPx))
        yROI = numpy.int(numpy.floor(yTargetPx))
        startRow = xROI - roiRadiusPx
        if startRow < 0:
            startRow = 0
        endRow = xROI + roiRadiusPx
        if endRow > imgData.shape[1]:
            endRow = imgData.shape[1]

        startCol = yROI - roiRadiusPx
        if startCol < 0:
            startCol = 0
        endCol = yROI + roiRadiusPx
        if endCol > imgData.shape[0]:
            endCol = imgData.shape[0]

        mask[startCol:endCol, startRow:endRow] = 0

    # imshow defaults to -0.5, -0.5 for origin, set this to 0,0
    # plot the mask used too make it positive valued so it shows up
    plt.imshow(imgData + numpy.abs(mask-1)*200, origin="lower", extent=(0, numRows, 0, numCols))

    # find all the centroids, and loop through and plot them
    ctrDataList, imStats = PyGuide.findStars(
        data = imgData,
        mask = mask,
        satMask = None,
        thresh=detectThresh,
        ccdInfo = CCDInfo,
        verbosity = 0,
        doDS9 = False,
    )[0:2]
    centroidsPx = []
    for ctrData in ctrDataList:
        # need to index explicity because ctrData is actually an object
        centroidsPx.append(ctrData.xyCtr)
        xyCtr = ctrData.xyCtr
        rad = ctrData.rad
        counts = ctrData.counts
        plt.plot(xyCtr[0], xyCtr[1], 'or', markersize=10, fillstyle="none")#, alpha=0.2)
        # print("star xyCtr=%.2f, %.2f, radius=%s counts=%.2f" % (xyCtr[0], xyCtr[1], rad, counts))
    # plot the desired targets
    centroidsPx = numpy.asarray(centroidsPx)
    nTargs = len(positionerTargetsPx.values())
    nCentroids = len(centroidsPx)

    for posID, (xTargetPx, yTargetPx) in positionerTargetsPx.items():
        plt.plot(xTargetPx, yTargetPx, 'xr', markersize=10)

    if plot:
        plt.show()
    # calculate distances between all targets and all centroids
    if nCentroids > nTargs:
        # don't allow false positives
        raise RuntimeError("more centroids than targets")
    if nCentroids < nTargs:
        #allow missing centroids
        print("warning: more targets than centroids")
    if nCentroids == 0:
        raise RuntimeError("didn't find any centroids")

    # print("distMat shappe", distMat.shape)
    targArrayPx = numpy.array(list(positionerTargetsPx.values()))
    targIdArray = list(positionerTargetsPx.keys())
    # for each centroid give it a target
    cent2target = [] # holds centroidIndex, targetIndex, and distance to target in px
    for centInd, cent in enumerate(centroidsPx):
        # a row of disntances for this target
        distArr = numpy.array([numpy.linalg.norm(targ-cent) for targ in targArrayPx])
        targInd = numpy.argmin(distArr)
        cent2target.append([centInd, targInd, distArr[targInd]])
    cent2target = numpy.array(cent2target)
    # for paranoia, remove any targets with distance greater than the ROI,
    # not sure this could happen but check anyways
    cent2target = cent2target[cent2target[:,2] < roiRadiusPx]

    for cInd, tInd, dist in cent2target:
        print("centroid %i gets target %i at distance %.2f pixels"%(cInd, tInd, dist))

    # calculate the offsets (vector from centroid to target)
    # in kaiju's reference frame in mm
    positionerOffsets = OrderedDict()
    for cInd, tInd, dist in cent2target:
        tInd = int(tInd)
        cInd = int(cInd)
        posID = targIdArray[tInd]
        targPix = targArrayPx[tInd]
        centPix = centroidsPx[cInd]
        offPx = targPix - centPix
        offMM = numpy.dot(offPx * scaleFac, rot2kaiju)
        positionerOffsets[posID] = offMM
        # print("dist %i %.2f precomputed %.2f"%(posID, numpy.linalg.norm(targPix-centPix), dist))

    plt.close()
    return positionerOffsets
    # find the best target for each centroids

    # plt.plot(xROI, yROI, "ok")
    # plt.savefig("test.tiff")
    # plt.close()

async def main():

    # Set logging level to DEBUG
    # log.set_level()

    # Initialise the FPS instance.
    # fps = FPS(layout="grid7.txt")
    fps = FPS()
    await fps.initialise()

    # Print the status of positioner 4
    # print("FPS status", fps[robotID].status)

    trialNumber = 0
    seed = 7000
    logFile = open("moveSevenCamera.log", "w")
    while True:
        seed += 1
        # rg = safeGrid()
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
        await fps.send_trajectory(fp)
        print("trajectory done")
        # command 5 repositioning moves
        positionerAlphaBeta = OrderedDict()
        for r in rg.allRobots:
            positionerAlphaBeta[r.id] = [r.alphaPath[0][1], r.betaPath[0][1]]

        for posIter in range(5):
            # measure the positions of all the guys use 4 images for centroid
            imgDataList = []
            for imageIter in range(nImgAvg):
                imgDataList.append(csCam.camera.getImage())
            # centroid on the average image
            imgData = numpy.sum(imgDataList, axis=0) / nImgAvg
            positionerOffsets = centroid(imgData, targetPositions, plot=False)
            # print the position errors in microns
            for r in rg.allRobots:
                try:
                    xOffMM, yOffMM = positionerOffsets[r.id]
                except:
                    print("no found offset for robot %i, skipping correction")
                    continue

                print("iter %i: robot %i has error of %.2f microns"%(posIter, r.id, numpy.linalg.norm([xOffMM, yOffMM]) * 1000 ))
                # figure out alpha beta offset for this positioner
                alphaLast, betaLast = positionerAlphaBeta[r.id]
                r.setAlphaBeta(alphaLast, betaLast)
                xFiberLast, yFiberLast, zFiberLast = r.metFiberPos
                # add fiber offset
                xOff, yOff = positionerOffsets[r.id]
                nextFiberX = xFiberLast + xOff
                nextFiberY = yFiberLast + yOff
                metFiberID = 0
                nextAlpha, nextBeta = r.alphaBetaFromFiberXY(nextFiberX, nextFiberY, metFiberID)
                alphaOff = nextAlpha - alphaLast
                betaOff = nextBeta - betaLast
                if numpy.max(numpy.abs([alphaOff, betaOff])) > 10:
                    print("max alpha beta offsets are too high: %.2f, %.2f"%(alphaOff, betaOff))
                    continue
                positionerAlphaBeta[r.id] = [nextAlpha, nextBeta]
                await fps[r.id].goto(alpha=nextAlpha, beta=nextBeta)

        logFile.write("starting reverse trajectory seed=%i trial=%i collisionBuffer=%.2f\n"%(seed, trialNumber, collisionBuffer))

        print("reverse path")
        await fps.send_trajectory(rp)
        print("trajectory done")
        trialNumber += 1

        if fps.locked:
            logFile.write("FPS is locked! exiting\n")
            break
        # Cleanly finish all pending tasks and exit
    await fps.shutdown()
    logFile.close()

# asyncio.run(main())
def multiImage():
    rg = homeGrid()

    targPos = getTargetPositions(rg)

    # find number of images after which centroids become stable
    outputList = []
    nImages = list(range(1,10))
    for nImg in nImages:
        print("trying nImg", nImg)
        imgList = []
        for i in range(nImg):
            tStart = time.time()
            imgList.append(csCam.camera.getImage())
            print("image took %.2f seconds"%(time.time()-tStart))
        imgList = numpy.array(imgList)
        print("imgList shape", imgList.shape)
        stackedImg = numpy.sum(imgList, axis=0) / nImg
        print("averaged shape", stackedImg.shape)
        centToTarget = centroid(stackedImg, targPos, plot=False)
        outputList.append(centToTarget)

    outputList = numpy.array(outputList)
    print("outputList shape", outputList.shape)

    # on plot per centroid
    # plt.figure()
    fig, axs = plt.subplots(outputList.shape[1], 1)
    for i, ax in enumerate(axs):
        microns = outputList[:,i,1] * scaleFac * 1000
        ax.plot(nImages, microns - microns[0], label="cent %i"%i) # middle index is centroid number, last is distance
    plt.ylabel("microns")
    plt.xlabel("n images averaged")
    # plt.legend()
    plt.show()

def measureDisplacement(fromFile=False):
    rg = homeGrid()
    targPos = getTargetPositions(rg)
    if fromFile:
        f = open("imgData.pkl", "rb")
        imgData = pickle.load(f)
        f.close()
    else:
        imgDataList = []
        for i in range(nImgAvg):
            imgDataList.append(csCam.camera.getImage())
        imgDataList = numpy.array(imgDataList)
        imgData = numpy.sum(imgDataList, axis=0) / nImgAvg
        f = open("imgData.pkl", "wb")
        pickle.dump(imgData, f)
        f.close()
    output = centroid(imgData, targPos, plot=True)

asyncio.run(main())

# measureDisplacement(fromFile=True)

# multiImage()

# plt.plot(nImages, outputList)

# fp, rp = generatePath(1, movie=True)

# print(fp)


