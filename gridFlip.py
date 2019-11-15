from kaiju import utils, RobotGrid
from multiprocessing import Pool, cpu_count
from functools import partial
import numpy

nDia = 27
pitch = 22.4
hasApogee = True
angStep = 0.1
collisionBuffer = 2.25
nTrials = 500

theta = numpy.radians(90)
cos = numpy.cos(theta)
sin = numpy.sin(theta)

def doOne(seed, flip90=False):
    rg = RobotGrid(angStep, collisionBuffer, 2.2, seed)
    xPos, yPos = utils.hexFromDia(nDia, pitch=22.4)
    for ii, (xp,yp) in enumerate(zip(xPos,yPos)):
        if flip90:
            xrot = cos * xp + sin * yp
            yrot = sin * xp - cos * yp
            rg.addRobot(ii, xrot, yrot, hasApogee)
        else:
            rg.addRobot(ii, xp, yp, hasApogee)
    rg.initGrid()
    for ii in range(rg.nRobots):
        r = rg.getRobot(ii)
        r.setXYUniform()  # r.setXYUniform can give nan values for alpha beta?

    # set all positioners randomly (they are initialized at 0,0)

    rg.decollide2()


    rg.pathGen() # calling decollide twice breaks things?


    robotsFolded = 0
    for r in rg.allRobots:
        if r.alpha == 0 and r.beta == 180:
            robotsFolded += 1

    # if rg.didFail:
    #     filename = "seed_%i"%seed
    #     if flip90:
    #         filename += "_flipped"
    #     else:
    #         filename += "_notflipped"
    #     utils.plotOne(1, rg, figname=filename+".png", isSequence=False, internalBuffer=collisionBuffer)

    return robotsFolded

p = Pool(10)
foldedNormal = numpy.asarray(p.map(doOne, range(nTrials)))
p.close()

print("normal percent", numpy.sum(foldedNormal)/(547*nTrials))
p = Pool(10)
doPartial = partial(doOne, flip90=True)
folded90 = numpy.asarray(p.map(doPartial, range(nTrials)))
p.close()

print("flipped percent", numpy.sum(folded90)/(547*nTrials))


