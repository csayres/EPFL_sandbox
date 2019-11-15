import asyncio
from jaeger import FPS, log
import time

from kaiju import RobotGrid, utils
import matplotlib.pyplot as plt
import numpy

import pickle

from trajPlotter import plotTraj

# seed 7 robot 0 is problematic (truncation on beta didn't work)
# seed 529 smoothing failed with  78

MaxSpeed = 5 # RPM
RobotMaxSpeed = (MaxSpeed-0.5)*360/60. # degrees per sec (3 RPM)
angStep = 0.05 # degrees per step
smoothPts = 5
epsilon = angStep * 2
collisionBuffer = 3
collisionShrink = 0.02
nSavedPaths = 50
makeNewPaths = False
doPlot = False
nTrials = 2000
robotID = 14
# time = angStep * stepNum / speed

def generatePath(seed=0, plot=False):
    nDia = 3
    pitch = 22.4

    hasApogee = True
    rg = RobotGrid(angStep, collisionBuffer, epsilon, seed)
    xPos, yPos = utils.hexFromDia(nDia, pitch=pitch)
    for ii, (xp, yp) in enumerate(zip(xPos, yPos)):
        rg.addRobot(ii, xp, yp, hasApogee)
    rg.initGrid()
    for ii in range(rg.nRobots):
        r = rg.getRobot(ii)
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

    # find the positioner with the most interpolated steps
    useRobot = None
    maxSteps = 0
    for i, r in enumerate(rg.allRobots):
        m = len(r.simplifiedBetaPath) # beta path is usually more complicated
        if m > maxSteps:
            maxSteps = m
            useRobot = r

    if plot:
        plotTraj(useRobot, "seed_%i_"%seed, dpi=250)

    # bp = numpy.array(useRobot.betaPath)
    # sbp = numpy.array(useRobot.interpSmoothBetaPath)
    ibp = numpy.array(useRobot.simplifiedBetaPath)

    # ap = numpy.array(useRobot.alphaPath)
    # sap = numpy.array(useRobot.interpSmoothAlphaPath)
    iap = numpy.array(useRobot.simplifiedAlphaPath)

    # generate kaiju trajectory (for robot 23)
    # time = angStep * stepNum / speed

    alphaTimesR = iap[:,0] * angStep / RobotMaxSpeed
    alphaDegR = iap[:,1]
    betaTimesR = ibp[:,0] * angStep / RobotMaxSpeed
    betaDegR = ibp[:,1]

    armPathR = {} # reverse path
    armPathR["alpha"] = [(pos, time) for pos, time in zip(alphaDegR, alphaTimesR)]
    armPathR["beta"] = [(pos, time) for pos, time in zip(betaDegR, betaTimesR)]

    reversePath = {

        robotID : armPathR
    }

    # build forward path
    alphaTimesF = numpy.abs(alphaTimesR-alphaTimesR[-1])[::-1]
    alphaDegF = alphaDegR[::-1]
    betaTimesF = numpy.abs(betaTimesR-betaTimesR[-1])[::-1]
    betaDegF = betaDegR[::-1]

    armPathF = {} # reverse path
    armPathF["alpha"] = [(pos, time) for pos, time in zip(alphaDegF, alphaTimesF)]
    armPathF["beta"] = [(pos, time) for pos, time in zip(betaDegF, betaTimesF)]

    forwardPath = {

        robotID : armPathF
    }


    return forwardPath, reversePath, maxSteps

if makeNewPaths:
    problematicTuples = []
    trajPoints = []
    seeds = []
    for seed in range(nTrials):
        print("seed", seed)
        try:
            fp, rp, maxSteps = generatePath(seed, plot=doPlot)
            print("generate path worked")
        except:
            continue

        if len(problematicTuples) < nSavedPaths:
            problematicTuples.append([fp,rp])
            trajPoints.append(maxSteps)
            seeds.append(seed)
        else:
            iMinTraj = numpy.argmin(trajPoints)
            if maxSteps > trajPoints[iMinTraj]:
                problematicTuples.pop(iMinTraj)
                trajPoints.pop(iMinTraj)
                problematicTuples.append([fp,rp])
                trajPoints.append(maxSteps)
                seeds.pop(iMinTraj)
                seeds.append(seed)


    print("n traj", len(problematicTuples))
    print("max pts", trajPoints)

    f = open("traj.pkl", "wb")
    pickle.dump([problematicTuples, trajPoints, seeds], f)
    f.close()

else:
    f = open("traj.pkl", "rb")
    problematicTuples, trajPoints, seeds = pickle.load(f)
    f.close()

def plotTrajectories():
    fig = plt.figure(figsize=(10,10))
    for fp, rp in problematicTuples:
        alphaPts = numpy.asarray(fp[robotID]["alpha"])
        betaPts = numpy.asarray(fp[robotID]["beta"])
        plt.plot(alphaPts[:,1], alphaPts[:,0], 'k')
        plt.plot(betaPts[:,1], betaPts[:,0], 'k')
    fig.savefig("traj.png")
    plt.close()

plotTrajectories()



async def main():

    # Set logging level to DEBUG
    log.set_level(50)

    # Initialise the FPS instance.
    fps = FPS(layout="singlePositioner.txt")
    await fps.initialise()

    # Print the status of positioner 4
    print("FPS status", fps[robotID].status)

    # Send positioner 4 to alpha=0, beta=180 # path transfer position
    await fps[robotID].goto(alpha=0, beta=180)

    for ii, (fp, rp) in enumerate(problematicTuples):
        print("trajectory", ii)

        # print("forward path")
        # print("alpha points:")
        # for pos in fp[23]["alpha"]:
        #     print ("  %s"%str(pos))
        # print("beta points:")
        # for pos in fp[23]["beta"]:
        #     print ("  %s"%str(pos))

        # print("")
        # print("reverse path")
        # print("alpha points:")
        # for pos in rp[23]["alpha"]:
        #     print ("  %s"%str(pos))
        # print("beta points:")
        # for pos in rp[23]["beta"]:
        #     print ("  %s"%str(pos))


        time.sleep(1)

        print("forward path to ", fp[robotID]["alpha"][-1], fp[robotID]["beta"][-1])
        await fps.send_trajectory(fp, False)
        print("trajectory done")

        time.sleep(1)

        print("reverse path")
        await fps.send_trajectory(rp, False)
        print("trajectory done")
        # break

    # Cleanly finish all pending tasks and exit
    await fps.shutdown()

asyncio.run(main())

