
# note for the moment must set to commit ae7c7e7 'mostly working assingment tools'
from subprocess import Popen
import time
from multiprocessing import Pool, cpu_count
import glob
import os
import numpy

import matplotlib.pyplot as plt
from shapely.geometry import LineString
from descartes import PolygonPatch

from kaiju import utils, RobotGrid

nDia = 3
pitch = 22.4

angStep = 1
smoothPts = 3 # 101 for 0.05
epsilon = angStep * 2

angStep = .05
smoothPts = 50
epsilon = angStep * 100

collisionBuffer = 3
collisionShrink = 0.1
epsilon = angStep * 3
seed1 = 0
hasApogee = True
figOffset = 0
xLim = [-70, 70]
yLim = [-70, 70]
# maxPathSteps = int(700.0/angStep)
seed1 = 0
rg = RobotGrid(angStep, collisionBuffer, epsilon, seed1)
xPos, yPos = utils.hexFromDia(nDia, pitch=pitch)
for ii, (xp,yp) in enumerate(zip(xPos,yPos)):
    rg.addRobot(ii, xp, yp, hasApogee)
rg.initGrid()
for ii in range(rg.nRobots):
    r = rg.getRobot(ii)
    r.setXYUniform()
# set all positioners randomly (they are initialized at 0,0)
rg.decollide2()
rg.pathGen()
rg.smoothPaths(smoothPts) # must be odd
rg.simplifyPaths()
rg.setCollisionBuffer(collisionBuffer-collisionShrink)
rg.verifySmoothed()

ii = 0
for r in rg.allRobots:
    ii += 1
    spa = numpy.array(r.smoothedAlphaPath)
    spb = numpy.array(r.smoothedBetaPath)
    rpa = numpy.array(r.alphaPath)
    rpb = numpy.array(r.betaPath)
    aRDP = numpy.array(r.simplifiedAlphaPath);
    bRDP = numpy.array(r.simplifiedBetaPath);


    av = numpy.array(r.alphaVel)
    bv = numpy.array(r.betaVel)
    vSteps = numpy.arange(len(av))
    sav = numpy.array(r.smoothAlphaVel)
    sbv = numpy.array(r.smoothBetaVel)
    ss = numpy.arange(len(sav))

    print("plotting", ii)
    print("alpha start", rpa[0,:] - aRDP[0,:])
    print("alpha end", rpa[-1,:] - aRDP[-1,:])
    print("beta start", rpb[0,:] - bRDP[0,:])
    print("beta end", rpb[-1,:] - bRDP[-1,:])

    fig, ax = plt.subplots(2,1, figsize=(10,10))


    ax[0].plot(rpa[:,0], rpa[:,1], linewidth=0.2, label="rough alpha", alpha=0.8)
    ax[0].plot(rpb[:,0], rpb[:,1], linewidth=0.2, label="rough beta", alpha=0.8)
    ax[0].plot(spa[:,0], spa[:,1], 'k-', linewidth=0.2, label="smooth alpha")
    ax[0].plot(spb[:,0], spb[:,1], 'k-', linewidth=0.2, label="smooth beta")
    ax[0].plot(aRDP[:,0], aRDP[:,1], 'oc-', linewidth=0.2, markeredgewidth=0.4, fillstyle="none", markersize=2, label="RDP alpha", alpha=0.7)
    ax[0].plot(bRDP[:,0], bRDP[:,1], 'oc-', linewidth=0.2, markeredgewidth=0.4, fillstyle="none", markersize=2, label="RDP beta", alpha=0.7)
    ax[0].legend()

    ax[1].plot(vSteps, av, linewidth=0.2, label="alphaVel", alpha=0.4)
    ax[1].plot(vSteps, bv, linewidth=0.2, label="betaVel", alpha=0.4)
    ax[1].plot(ss, sav, 'k-', linewidth=0.2, label="smoothAlpha")
    ax[1].plot(ss, sbv, 'k-', linewidth=0.2, label="smoothBeta")

    ax[1].legend()
    # plt.legend()


    plt.savefig("robot_%s.png"%ii, dpi=1000)
    plt.close()


