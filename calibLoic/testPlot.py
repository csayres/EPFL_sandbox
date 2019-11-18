#cython: language_level=3
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from matplotlib import patches
import numpy as np
import miscmath as mm
import DEFINES
import copy

def garbage(drawingAxis, lineWidth, testResults):
	pass

def plot_test_parameters(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	
	if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
	elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
	else:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

	drawingAxis.set_axis_off()
	drawingAxis.set_xlim(0,1)
	drawingAxis.set_ylim(0,1)

	if testResults.testParameters.stopOnDesiredError:
		stopOnDesiredErrorStr = 'Yes'
	else:
		stopOnDesiredErrorStr = 'No'

	IDDate			= f'Completed {testResults.completionTime}'
	IDText			= f'Positioner {testResults.positionerID:<4} ({testResults.testBenchName} slot #{testResults.slotID:1})'
	generalLegend 	= [	'Nb repetitions:',\
						'Nb targets:',\
						'Total targets:',\
						'Desired error [um]:',\
						'Max allowed moves:',\
						'Stop on desired error:']
	generalVars 	= [	f'{nbRepetitions:>6}',\
						f'{nbTargets:>6}',\
						f'{nbRepetitions*nbTargets:>6}',\
						f'{testResults.testParameters.desiredTargetError:>6}',\
						f'{maxNbMoves:>6}',\
						stopOnDesiredErrorStr]
	motorLegend		= [	'Speed [RPM]',\
						'Current [%]',\
						'Range [°]']
	alphaTitle		= 	'Alpha'
	alphaText		= [	f'{testResults.testParameters.motorRpmAlpha:>6}',\
						f'{testResults.testParameters.cruiseCurrentAlpha:>6}',\
						f'{testResults.testParameters.alphaTestRange[0]:>3} to {testResults.testParameters.alphaTestRange[1]:>3}']
	
	betaTitle		= 	'Beta'
	betaText		= [	f'{testResults.testParameters.motorRpmBeta:>6}',\
						f'{testResults.testParameters.cruiseCurrentBeta:>6}',\
						f'{testResults.testParameters.betaTestRange[0]:>3} to {testResults.testParameters.betaTestRange[1]:>3}']

	drawingAxis.text(0.50,1-0.02, IDText, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.50,1-0.09, IDDate, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	
	drawingAxis.text(0.02,1-0.20,generalLegend[0], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.27,generalLegend[1], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.34,generalLegend[2], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.41,generalLegend[3], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.48,generalLegend[4], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.55,generalLegend[5], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.20,generalVars[0], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.27,generalVars[1], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.34,generalVars[2], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.41,generalVars[3], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.48,generalVars[4], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.55,generalVars[5], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)

	drawingAxis.text(0.02,1-0.72,alphaTitle, size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.72,betaTitle, size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.50,1-0.82,motorLegend[0], size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.50,1-0.89,motorLegend[1], size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.50,1-0.96,motorLegend[2], size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	
	drawingAxis.text(0.02,1-0.82,alphaText[0], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.89,alphaText[1], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.96,alphaText[2], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	
	drawingAxis.text(0.98,1-0.82,betaText[0], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.89,betaText[1], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.96,betaText[2], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	
def plot_targets(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	
	#Change axes scaling
	drawingAxis.set_aspect('equal')
	drawingAxis.set_xlim(	testResults.slotsCenters[0]-DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS,\
							testResults.slotsCenters[0]+DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS)
	drawingAxis.set_ylim(	testResults.slotsCenters[1]-DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS,\
							testResults.slotsCenters[1]+DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS)
	drawingAxis.invert_yaxis()

	#generate the colors
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbRepetitions))

	#plot the positioner workspace
	externalCircle = 	patches.Arc(	(testResults.slotsCenters[0],testResults.slotsCenters[1]),\
										2*(testResults.positionersArmLengths[0]+testResults.positionersArmLengths[1]),2*(testResults.positionersArmLengths[0]+testResults.positionersArmLengths[1]),\
										0,0,360,\
										color = DEFINES.PLOT_ARC_COLOR, linestyle = DEFINES.PLOT_ARC_LINESTYLE, linewidth = lineWidth*DEFINES.PLOT_ARC_LINEWIDTH_RATIO)
	drawingAxis.add_patch(externalCircle)
	internalCircle = 	patches.Arc(	(testResults.slotsCenters[0],testResults.slotsCenters[1]),\
										2*(abs(testResults.positionersArmLengths[0]-testResults.positionersArmLengths[1])),2*(abs(testResults.positionersArmLengths[0]-testResults.positionersArmLengths[1])),\
										0,0,360,\
										color = DEFINES.PLOT_ARC_COLOR, linestyle = DEFINES.PLOT_ARC_LINESTYLE, linewidth = lineWidth*DEFINES.PLOT_ARC_LINEWIDTH_RATIO)
	drawingAxis.add_patch(internalCircle)

	#plot the targets
	drawingAxis.scatter(np.ravel(testResults.targets[0,:,0,0]), np.ravel(testResults.targets[0,:,0,1]),color = DEFINES.PLOT_TARGET_MARKER_COLOR, marker = DEFINES.PLOT_TARGET_MARKER, s = lineWidth*DEFINES.PLOT_TARGET_MARKERSIZE_RATIO)

	#plot the points and the error
	for repetition in range(0, nbRepetitions):
		drawingAxis.scatter(np.ravel(testResults.targets[repetition,:,0,0]), np.ravel(testResults.targets[repetition,:,0,1]),color = plotColors[repetition], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		drawingAxis.quiver(	np.ravel(testResults.targets[repetition,:,0,0]), np.ravel(testResults.targets[repetition,:,0,1]),\
							np.ravel(testResults.modelError[repetition,:,0,1]), np.ravel(testResults.modelError[repetition,:,0,2]),\
							color = plotColors[repetition], angles = 'xy', units = 'xy' , width = 0.005*50, headwidth = 3, headlength = 1.3*3, headaxislength = 1.3*3)

def plot_error_progression(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets*nbRepetitions

	if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
	elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
	else:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

	maxNbMoves = int(testResults.mesMaxNbMoves[-1])
	minY = np.nanmin(1000*np.ravel(testResults.modelError[:,:,:,0]))*0.9
	maxY = np.nanmax(1000*np.ravel(testResults.modelError[:,:,:,0]))*2

	drawingAxis.set_yscale("log")
	drawingAxis.set_xlim([0.8, maxNbMoves+0.2])
	drawingAxis.set_ylim([minY, maxY])
	drawingAxis.set_xticks(range(1, maxNbMoves+1))

	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	moveIndex = range(1, maxNbMoves+1)

	currentPoint = 0
	for repetition in range(0, nbRepetitions):
		for target in range(0, nbTargets):	
			drawingAxis.plot(moveIndex, 1000*np.ravel(testResults.modelError[repetition,target,0:maxNbMoves,0]), color = plotColors[currentPoint], linewidth = lineWidth)
			currentPoint += 1


	completedTargets = 0
	for move in range(0, maxNbMoves):
		drawingAxis.plot([move+1, move+1], [minY, maxY*0.7], color = 'black', linestyle = '--', linewidth = lineWidth)
		drawingAxis.text(move+1, maxY*0.8  ,f'{testResults.mesTargetConvergeance[-1][move]:<3.1f}%', size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center')

	drawingAxis.plot([0.8, maxNbMoves+1.2], [testResults.testParameters.desiredTargetError, testResults.testParameters.desiredTargetError], color = 'black', linewidth = lineWidth)

def plot_total_error(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets

	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	
	#Start plotting
	currentPoint = 0
	move = 0
	for target in range(0, nbTargets):	
		drawingAxis.scatter(1000*np.ravel(testResults.modelError[:,target,move,1]), 1000*np.ravel(testResults.modelError[:,target,move,2]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		currentPoint += 1

	minAxis = min(np.nanmin(1000*np.ravel(testResults.modelError[:,:,move,1])), np.nanmin(1000*np.ravel(testResults.modelError[:,:,move,2])))
	maxAxis = max(np.nanmax(1000*np.ravel(testResults.modelError[:,:,move,1])), np.nanmax(1000*np.ravel(testResults.modelError[:,:,move,2])))
	
	if minAxis < 0:
		minAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN
	else:
		minAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
		
	if maxAxis < 0:
		maxAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
	else:
		maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

	drawingAxis.set_xlim(minAxis,maxAxis)
	drawingAxis.set_ylim(minAxis,maxAxis)

def plot_error_a(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets
	
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	
	#Start plotting
	currentPoint = 0
	move = 0
	for target in range(0, nbTargets):	
		drawingAxis.scatter(1000*np.ravel(testResults.modelError[:,target,move,3]), 1000*np.ravel(testResults.modelError[:,target,move,4]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		currentPoint += 1

	minAxis = min(np.nanmin(1000*np.ravel(testResults.modelError[:,:,move,3])), np.nanmin(1000*np.ravel(testResults.modelError[:,:,move,4])))
	maxAxis = max(np.nanmax(1000*np.ravel(testResults.modelError[:,:,move,3])), np.nanmax(1000*np.ravel(testResults.modelError[:,:,move,4])))
	
	if minAxis < 0:
		minAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN
	else:
		minAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
		
	if maxAxis < 0:
		maxAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
	else:
		maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

	drawingAxis.set_xlim(minAxis,maxAxis)
	drawingAxis.set_ylim(minAxis,maxAxis)

def plot_error_b(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets
	
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))

	#Start plotting
	currentPoint = 0
	move = 0
	for target in range(0, nbTargets):
		drawingAxis.scatter(1000*np.ravel(testResults.modelError[:,target,move,5]), 1000*np.ravel(testResults.modelError[:,target,move,6]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		currentPoint += 1

	minAxis = min(np.nanmin(1000*np.ravel(testResults.modelError[:,:,move,5])), np.nanmin(1000*np.ravel(testResults.modelError[:,:,move,6])))
	maxAxis = max(np.nanmax(1000*np.ravel(testResults.modelError[:,:,move,5])), np.nanmax(1000*np.ravel(testResults.modelError[:,:,move,6])))
	
	if minAxis < 0:
		minAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN
	else:
		minAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
		
	if maxAxis < 0:
		maxAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
	else:
		maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

	drawingAxis.set_xlim(minAxis,maxAxis)
	drawingAxis.set_ylim(minAxis,maxAxis)

def plot_error_hist(drawingAxis, lineWidth, testResults):
	if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
	elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
	else:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

	# nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	# nbPoints = nbTargets*nbRepetitions
	move = 0

	ravelledModelError = 1000*np.ravel(testResults.modelError[:,:,move,0])
	maxX = np.nanmax(ravelledModelError)
	xs = np.linspace(0,maxX,1000)

	density = gaussian_kde(ravelledModelError[~np.isnan(ravelledModelError)])
	density.covariance_factor = lambda : .25
	density._compute_covariance()
	drawingAxis.plot(xs,100*density(xs), color = 'darkblue', linewidth = lineWidth, label = f'{round(mm.nanrms(ravelledModelError),1):<3.1f} [um]')
	drawingAxis.legend(fontsize = textSize)

def plot_total_repeatability(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets
	
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	
	#Start plotting
	if nbRepetitions > 1:
	#Start plotting
		currentPoint = 0
		for target in range(0, nbTargets):	
			drawingAxis.scatter(1000*np.ravel(testResults.repeatability[target,1]), 1000*np.ravel(testResults.repeatability[target,2]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
			currentPoint += 1

		minAxis = min(np.nanmin(1000*np.ravel(testResults.repeatability[:,1])), np.nanmin(1000*np.ravel(testResults.repeatability[:,2])))
		maxAxis = max(np.nanmax(1000*np.ravel(testResults.repeatability[:,1])), np.nanmax(1000*np.ravel(testResults.repeatability[:,2])))
		
		if minAxis < 0:
			minAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN
		else:
			minAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
			
		if maxAxis < 0:
			maxAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
		else:
			maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

		drawingAxis.set_xlim(minAxis,maxAxis)
		drawingAxis.set_ylim(minAxis,maxAxis)
	else:
		if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE
		elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_OVERVIEW
		else:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE

		drawingAxis.set_axis_off()
		drawingAxis.set_xlim(0,1)
		drawingAxis.set_ylim(0,1)
		drawingAxis.text(0.5,0.5,DEFINES.PLOT_NOT_TESTED_CAPTION, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes, bbox=dict(boxstyle = 'round',ec = (0.5,0.5,1), fc=(0.8,0.8,1.)))#, size = 20, rotation = 30., ha='center', va='center', bbox=dict(boxstyle = round,ec = (1.,0.5,0.5), fc=(1.,0.8, 0.8)))

def plot_repeatability_a(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets
	
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	
	#Start plotting
	if nbRepetitions > 1:
	#Start plotting
		currentPoint = 0
		for target in range(0, nbTargets):	
			drawingAxis.scatter(1000*np.ravel(testResults.repeatability[target,3]), 1000*np.ravel(testResults.repeatability[target,4]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
			currentPoint += 1

		minAxis = min(np.nanmin(1000*np.ravel(testResults.repeatability[:,3])), np.nanmin(1000*np.ravel(testResults.repeatability[:,4])))
		maxAxis = max(np.nanmax(1000*np.ravel(testResults.repeatability[:,3])), np.nanmax(1000*np.ravel(testResults.repeatability[:,4])))
		
		if minAxis < 0:
			minAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN
		else:
			minAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
			
		if maxAxis < 0:
			maxAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
		else:
			maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

		drawingAxis.set_xlim(minAxis,maxAxis)
		drawingAxis.set_ylim(minAxis,maxAxis)
	else:
		if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE
		elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_OVERVIEW
		else:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE

		drawingAxis.set_axis_off()
		drawingAxis.set_xlim(0,1)
		drawingAxis.set_ylim(0,1)
		drawingAxis.text(0.5,0.5,DEFINES.PLOT_NOT_TESTED_CAPTION, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes, bbox=dict(boxstyle = 'round',ec = (0.5,0.5,1), fc=(0.8,0.8,1.)))#, size = 20, rotation = 30., ha='center', va='center', bbox=dict(boxstyle = round,ec = (1.,0.5,0.5), fc=(1.,0.8, 0.8)))

def plot_repeatability_b(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets
	
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	
	#Start plotting
	if nbRepetitions > 1:
	#Start plotting
		currentPoint = 0
		for target in range(0, nbTargets):	
			drawingAxis.scatter(1000*np.ravel(testResults.repeatability[target,5]), 1000*np.ravel(testResults.repeatability[target,6]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
			currentPoint += 1

		minAxis = min(np.nanmin(1000*np.ravel(testResults.repeatability[:,5])), np.nanmin(1000*np.ravel(testResults.repeatability[:,6])))
		maxAxis = max(np.nanmax(1000*np.ravel(testResults.repeatability[:,5])), np.nanmax(1000*np.ravel(testResults.repeatability[:,6])))
		
		if minAxis < 0:
			minAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN
		else:
			minAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
			
		if maxAxis < 0:
			maxAxis *= 1-DEFINES.PLOT_AXIS_STRETCH_MARGIN
		else:
			maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

		drawingAxis.set_xlim(minAxis,maxAxis)
		drawingAxis.set_ylim(minAxis,maxAxis)
	else:
		if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE
		elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_OVERVIEW
		else:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE

		drawingAxis.set_axis_off()
		drawingAxis.set_xlim(0,1)
		drawingAxis.set_ylim(0,1)
		drawingAxis.text(0.5,0.5,DEFINES.PLOT_NOT_TESTED_CAPTION, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes, bbox=dict(boxstyle = 'round',ec = (0.5,0.5,1), fc=(0.8,0.8,1.)))#, size = 20, rotation = 30., ha='center', va='center', bbox=dict(boxstyle = round,ec = (1.,0.5,0.5), fc=(1.,0.8, 0.8)))


def plot_repeatability_hist(drawingAxis, lineWidth, testResults):
	#Start plotting
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets

	if nbRepetitions > 1:
		if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
		elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
		else:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

		ravelledRepeatability = 1000*np.ravel(testResults.repeatability[:,0])

		maxX = np.nanmax(ravelledRepeatability)
		xs = np.linspace(0,maxX,1000)

		density = gaussian_kde(ravelledRepeatability[~np.isnan(ravelledRepeatability)])
		density.covariance_factor = lambda : .25
		density._compute_covariance()
		drawingAxis.plot(xs,100*density(xs), color = 'darkblue', linewidth = lineWidth, label = f'{round(mm.nanrms(ravelledRepeatability),1):<3.1f} [um]')
		drawingAxis.legend(fontsize = textSize)

	else:
		if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE
		elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_OVERVIEW
		else:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE

		drawingAxis.set_axis_off()
		drawingAxis.set_xlim(0,1)
		drawingAxis.set_ylim(0,1)
		drawingAxis.text(0.5,0.5,DEFINES.PLOT_NOT_TESTED_CAPTION, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes, bbox=dict(boxstyle = 'round',ec = (0.5,0.5,1), fc=(0.8,0.8,1.)))#, size = 20, rotation = 30., ha='center', va='center', bbox=dict(boxstyle = round,ec = (1.,0.5,0.5), fc=(1.,0.8, 0.8)))


def plot_error_across_a(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets
	
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	
	#Start plotting
	currentPoint = 0
	move = 0
	for target in range(0, nbTargets):	
		drawingAxis.scatter(testResults.sortedCommands[:,target,move,0]*180/np.pi, 1000*np.ravel(testResults.modelError[:,target,move,3]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		currentPoint += 1

def plot_error_across_b(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets
	
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	
	#Start plotting
	currentPoint = 0
	move = 0
	for target in range(0, nbTargets):	
		drawingAxis.scatter(testResults.sortedCommands[:,target,move,1]*180/np.pi, 1000*np.ravel(testResults.modelError[:,target,move,5]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		currentPoint += 1

def plot_error_along_a(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets
	
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	
	#Start plotting
	currentPoint = 0
	move = 0
	for target in range(0, nbTargets):	
		drawingAxis.scatter(testResults.sortedCommands[:,target,move,0]*180/np.pi, 1000*np.ravel(testResults.modelError[:,target,move,4]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		currentPoint += 1

def plot_error_along_b(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	nbPoints = nbTargets
	
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbPoints))
	
	#Start plotting
	currentPoint = 0
	move = 0
	for target in range(0, nbTargets):	
		drawingAxis.scatter(testResults.sortedCommands[:,target,move,1]*180/np.pi, 1000*np.ravel(testResults.modelError[:,target,move,6]),color = plotColors[currentPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		currentPoint += 1

def plot_error_dist_each_move(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	maxNbMoves = int(min(np.max(np.ravel(testResults.nbCorrections[:,:]))+1, maxNbMoves))
	modelError = copy.deepcopy(testResults.modelError)

	if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
	elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
	else:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,maxNbMoves))

	# print((nbRepetitions, nbTargets, maxNbMoves, nbDims))
	# print(modelError)
	# print(modelError.shape)

	#Fill in the NaN with the last known error
	for repetition in range(0, nbRepetitions):
		for target in range(0, nbTargets):
			# print(str(int(testResults.nbCorrections[repetition,target])))
			for move in range(int(testResults.nbCorrections[repetition,target]), maxNbMoves):
				modelError[repetition,target,move,0] = modelError[repetition,target,int(testResults.nbCorrections[repetition,target]),0]


	maxX = np.nanmax(1000*np.ravel(modelError[:,:,:,0]))
	xs = np.linspace(0,maxX,1000)

	# print(modelError)

	for move in range(0, maxNbMoves):
		ravelledModelError = 1000*np.ravel(modelError[:,:,move,0])
		density = gaussian_kde(ravelledModelError[~np.isnan(ravelledModelError)])
		density.covariance_factor = lambda : .25
		density._compute_covariance()
		drawingAxis.plot(xs,100*density(xs), color = plotColors[move], linewidth = lineWidth, label = f'Move {move+1} ({round(mm.nanrms(ravelledModelError),1):>3.1f} [um])')
	drawingAxis.legend(fontsize = textSize)

#All plotting parameters
plotProperties	= [	[plot_test_parameters,		'Test parameters', 																		'', 						''],\
					[plot_targets,				'Targets', 																				'X [mm]', 					'Y [mm]'],\
					[plot_error_progression,	'Error progression', 																	'Move', 					'Error [um]'],\
					[plot_error_dist_each_move,	'Error distribution (each move)', 														'Error [um]', 				'% occurence'],\
					[plot_total_error,			'Total error',																			'X error [um]',				'Y error [um]'],\
					[plot_error_a,				'Alpha error',																			'Across axis [um]',			'Along axis [um]'],\
					[plot_error_b,				'Beta error',																			'Across axis [um]',			'Along axis [um]'],\
					[plot_error_hist,			'Error density',																		'Error move 1 [um]',		'% occurence'],\
					[plot_total_repeatability,	'Total repeatability', 																	'X [um]', 					'Y [um]'],\
					[plot_repeatability_a,		'Alpha repeatability',																	'Across axis [um]',			'Along axis [um]'],\
					[plot_repeatability_b,		'Beta repeatability',																	'Across axis [um]',			'Along axis [um]'],\
					[plot_repeatability_hist,	'Repeatability density', 																'Repeatability move 1 [um]','% occurence'],\
					[plot_error_across_a,		'Error across alpha', 																	'Commanded angle [°]', 		'Error [um]'],\
					[plot_error_across_b,		'Error across beta', 																	'Commanded angle [°]', 		'Error [um]'],\
					[plot_error_along_a,		'Error along alpha', 																	'Commanded angle [°]', 		'Error [um]'],\
					[plot_error_along_b,		'Error along beta', 																	'Commanded angle [°]', 		'Error [um]']]

def plot_lifetime_RMSerror(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	currentLifetimeIteration = testResults.config.currentLifetimeIteration

	#Start plotting
	drawingAxis.plot(range(1,currentLifetimeIteration+2), testResults.mesRMSError1stMove, color = 'darkblue', linewidth = lineWidth)
	
	minAxis = 0
	maxAxis = max(testResults.mesRMSError1stMove)
	
	if maxAxis < 1:
		maxAxis = 1
	else:
		maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

	drawingAxis.set_xlim(1,currentLifetimeIteration+1)
	drawingAxis.set_ylim(minAxis,maxAxis)

	#Add the validity rectangles
	addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, testResults.requirements.maxPosError, 1, testResults.config.currentLifetimeIteration)
	
def plot_lifetime_RMSrepeatability(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	currentLifetimeIteration = testResults.config.currentLifetimeIteration

	if nbRepetitions>1:
		#Start plotting
		drawingAxis.plot(range(1,currentLifetimeIteration+2), testResults.mesRMSRepeatability1stMove, color = 'darkblue', linewidth = lineWidth)
		
		minAxis = 0
		maxAxis = max(testResults.mesRMSRepeatability1stMove)
		
		if maxAxis < 0:
			maxAxis = 1
		else:
			maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

		drawingAxis.set_xlim(1,currentLifetimeIteration+1)
		drawingAxis.set_ylim(minAxis,maxAxis)

		#Add the validity rectangles
		addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, testResults.requirements.rmsPosRepeatability, 1, testResults.config.currentLifetimeIteration)
	
	else:
		if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE
		elif lineWidth == DEFINES.PLOT_LINEWIDTH_LIFETIME:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_LIFETIME
		else:
			textSize = DEFINES.PLOT_ERRTEXT_FONTSIZE_SINGLE

		drawingAxis.set_axis_off()
		drawingAxis.set_xlim(0,1)
		drawingAxis.set_ylim(0,1)
		drawingAxis.text(0.5,0.5,DEFINES.PLOT_NOT_TESTED_CAPTION, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes, bbox=dict(boxstyle = 'round',ec = (0.5,0.5,1), fc=(0.8,0.8,1.)))#, size = 20, rotation = 30., ha='center', va='center', bbox=dict(boxstyle = round,ec = (1.,0.5,0.5), fc=(1.,0.8, 0.8)))

def plot_lifetime_convergeanceRatio(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	currentLifetimeIteration = testResults.config.currentLifetimeIteration

	#Start plotting
	drawingAxis.plot(range(1,currentLifetimeIteration+2), [testResults.mesTargetConvergeance[i][-1] for i in range(0,currentLifetimeIteration+1)], color = 'darkblue', linewidth = lineWidth)
	
	minAxis = 0
	maxAxis = int(max(testResults.mesTargetConvergeance[:][-1]))
	
	if maxAxis < 0:
		maxAxis = 1
	else:
		maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

	drawingAxis.set_xlim(1,currentLifetimeIteration+1)
	drawingAxis.set_ylim(minAxis,maxAxis)

	#Add the validity rectangles
	addValidityRectanglesY(drawingAxis, minAxis, maxAxis, testResults.requirements.targetConvergeance, np.inf, 1, testResults.config.currentLifetimeIteration)
	
def plot_lifetime_maxNbMoves(drawingAxis, lineWidth, testResults):
	nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults.targets.shape
	currentLifetimeIteration = testResults.config.currentLifetimeIteration

	#Start plotting
	drawingAxis.plot(range(1,currentLifetimeIteration+2), testResults.mesMaxNbMoves, color = 'darkblue', linewidth = lineWidth)
	
	minAxis = 0
	maxAxis = max(testResults.mesMaxNbMoves)+0.2
	
	drawingAxis.set_xlim(1,currentLifetimeIteration+1)
	drawingAxis.set_ylim(minAxis,maxAxis)

	#Add the validity rectangles
	addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, testResults.requirements.maxNbMoves, 1, testResults.config.currentLifetimeIteration)

#All plotting parameters
plotPropertiesLifetime	= [	[plot_lifetime_RMSerror,			'Lifetime RMS error 1st move', 			'Lifetime iteration', 	'RMS error [um]'],\
							[plot_lifetime_RMSrepeatability,	'Lifetime RMS repeatability 1st move', 	'Lifetime iteration', 	'RMS repeatability [um]'],\
							[plot_lifetime_convergeanceRatio,	'Lifetime target convergeance ratio', 	'Lifetime iteration', 	'Target convergeance [%]'],\
							[plot_lifetime_maxNbMoves,			'Lifetime nb moves required',			'Lifetime iteration', 	'Nb moves to reach target']]
							
def addValidityRectanglesY(drawingAxis, minAxis, maxAxis, minRequirement, maxRequirement, xStart, xEnd):
	if maxAxis > maxRequirement:
		if maxRequirement <= minAxis: #alphaMax is under the plot - no validity region
			nonValidRectangleTop = patches.Rectangle((xStart, minAxis), xEnd-xStart, abs(maxAxis-minAxis), edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(nonValidRectangleTop)
		
		elif minAxis < minRequirement: #validity borned by the requirements on top and bottom
			validRectangle = patches.Rectangle((xStart, minRequirement), xEnd-xStart, abs(maxRequirement-minRequirement), edgecolor = 'None', facecolor = DEFINES.PLOT_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			nonValidRectangleTop = patches.Rectangle((xStart, maxRequirement), xEnd-xStart, abs(maxAxis-maxRequirement), edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			nonValidRectangleBottom = patches.Rectangle((xStart, minAxis), xEnd-xStart, abs(minRequirement-minAxis), edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(validRectangle)
			drawingAxis.add_patch(nonValidRectangleTop)
			drawingAxis.add_patch(nonValidRectangleBottom)

		else: #validity borned by the requirements on top and axis on bottom
			validRectangle = patches.Rectangle((xStart, minAxis), xEnd-xStart, abs(maxRequirement-minAxis), edgecolor = 'None', facecolor = DEFINES.PLOT_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			nonValidRectangleTop = patches.Rectangle((xStart, maxRequirement), xEnd-xStart, abs(maxAxis-maxRequirement), edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(validRectangle)
			drawingAxis.add_patch(nonValidRectangleTop)

	elif minAxis < minRequirement: 
		if minRequirement >= maxAxis: #alphaMin is over the plot - no validity region
			nonValidRectangleBottom = patches.Rectangle((xStart, minAxis), xEnd-xStart, abs(maxAxis-minAxis), edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(nonValidRectangleBottom)
		
		else: #validity borned by the requirements on bottom and axis on top
			validRectangle = patches.Rectangle((xStart, minRequirement), xEnd-xStart, abs(maxAxis-minRequirement), edgecolor = 'None', facecolor = DEFINES.PLOT_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			nonValidRectangleBottom = patches.Rectangle((xStart, minAxis), xEnd-xStart, abs(minRequirement-minAxis), edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(validRectangle)
			drawingAxis.add_patch(nonValidRectangleBottom)
	
	else: #validity borned by the axis on top and bottom
		validRectangle = patches.Rectangle((xStart, minAxis), xEnd-xStart, abs(maxAxis-minAxis), edgecolor = 'None', facecolor = DEFINES.PLOT_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
		drawingAxis.add_patch(validRectangle)


def main():
	pass

if __name__ == '__main__':
	main()