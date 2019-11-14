import asyncio
from jaeger import FPS, log
import time

from kaiju import RobotGrid, utils
import matplotlib.pyplot as plt
import numpy

import pickle

MaxSpeed = 5 # RPM
RobotMaxSpeed = (MaxSpeed-2)*360/60. # degrees per sec (3 RPM)
angStep = 0.05 # degrees per step
smoothPts = 50
epsilon = angStep * 100
collisionBuffer = 3
collisionShrink = 0.1
nTests = 50
makeNewPaths = True
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
        print("failed")
        raise(RuntimeError, "path gen failed")
    rg.smoothPaths()
    rg.setCollisionBuffer(collisionBuffer - collisionShrink)
    rg.verifySmoothed()

    if rg.smoothCollisions:
        raise(RuntimeError, "smoothing failed")

    # find the positioner with the most interpolated steps
    useRobot = None
    maxSteps = 0
    for i, r in enumerate(rg.allRobots):
        m = len(r.smoothBetaPath)
        if m > maxSteps:
            maxSteps = m
            useRobot = r

    bp = numpy.array(useRobot.betaPath)
    sbp = numpy.array(useRobot.interpSmoothBetaPath)
    ibp = numpy.array(useRobot.smoothBetaPath)

    ap = numpy.array(useRobot.alphaPath)
    sap = numpy.array(useRobot.interpSmoothAlphaPath)
    iap = numpy.array(useRobot.smoothAlphaPath)

    if plot:
        plt.figure(figsize=(10,10))
        print("ip points", len(ibp))
        plt.plot(bp[:,0], bp[:,1], 'g', alpha=0.5)
        plt.plot(sbp[:,0], sbp[:,1])
        plt.plot(ibp[:,0], ibp[:,1], 'ok', alpha=0.5, fillstyle="none", markersize=1)
        plt.plot()
        plt.savefig("%i_beta.png"%useRobot.id, dpi=250)
        plt.close()

        plt.figure(figsize=(10,10))

        print("ip points", len(iap))
        plt.plot(ap[:,0], ap[:,1], 'g', alpha=0.5)
        plt.plot(sap[:,0], sap[:,1])
        plt.plot(iap[:,0], iap[:,1], 'ok', alpha=0.5, fillstyle="none", markersize=1)
        plt.plot()
        plt.savefig("%i_alpha.png"%useRobot.id, dpi=250)
        plt.close()

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

        23 : armPathR
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

        23 : armPathF
    }


    return forwardPath, reversePath, maxSteps

if makeNewPaths:
    problematicTuples = []
    trajPoints = []
    seeds = []
    for seed in range(2000):
        print("seed", seed)
        try:
            fp, rp, maxSteps = generatePath(seed)
        except:
            continue
        if len(problematicTuples) < nTests:
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
        alphaPts = numpy.asarray(fp[23]["alpha"])
        betaPts = numpy.asarray(fp[23]["beta"])
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
    print("FPS status", fps[23].status)

    # Send positioner 4 to alpha=0, beta=180 # path transfer position
    await fps[23].goto(alpha=0, beta=180)

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

        print("forward path to ", fp[23]["alpha"][-1], fp[23]["beta"][-1])
        await fps.send_trajectory(fp, False)
        print("trajectory done")

        time.sleep(1)

        print("reverse path")
        await fps.send_trajectory(rp, False)
        print("trajectory done")

    # Cleanly finish all pending tasks and exit
    await fps.shutdown()

# asyncio.run(main())

