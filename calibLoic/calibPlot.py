#cython: language_level=3
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from matplotlib import patches
from matplotlib.lines import Line2D
import numpy as np
import miscmath as mm
import DEFINES

def garbage(drawingAxis, lineWidth, calibResults):
	pass

#Plot measures
def plot_measures_a(drawingAxis, lineWidth, calibResults):
	plot_measures(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_ALPHA)

def plot_measures_b(drawingAxis, lineWidth, calibResults):
	plot_measures(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_BETA)

def plot_measures(drawingAxis, lineWidth, calibResults,  axisToDraw):
	axesToTest = calibResults.calibrationParameters.axesToTest

	if axisToDraw in axesToTest:
		#Change axes scaling
		drawingAxis.set_aspect('equal')
		drawingAxis.set_xlim(	calibResults.modelCenter[0]-DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS,\
								calibResults.modelCenter[0]+DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS)
		drawingAxis.set_ylim(	calibResults.modelCenter[1]-DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS,\
								calibResults.modelCenter[1]+DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS)
		drawingAxis.invert_yaxis()

		#Retrieve calib parameters
		sortedCentroidsXY = calibResults.sortedCentroidsXY
		commandedAngle = np.multiply(calibResults.sortedTargetCommand,180/np.pi)
		(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
		
		fittedCircles = calibResults.fittedCircles
		measuredAngles = np.multiply(calibResults.measuredAngles,180/np.pi)

		plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbStartingPoints))
		
		if nbDirections >= 2:
			directionsToPlot = DEFINES.PLOT_DIRECTIONS_TO_PLOT
		else:
			directionsToPlot = [0]

		#Start plotting
		for startingPoint in range(0,nbStartingPoints):
			plottingArc = 	patches.Arc(	(fittedCircles[startingPoint,axisToDraw][0],fittedCircles[startingPoint,axisToDraw][1]),\
											2*fittedCircles[startingPoint,axisToDraw][2],2*fittedCircles[startingPoint,axisToDraw][2],\
											0,0,360,\
											color = DEFINES.PLOT_ARC_COLOR, linestyle = DEFINES.PLOT_ARC_LINESTYLE, linewidth = lineWidth*DEFINES.PLOT_ARC_LINEWIDTH_RATIO)
			drawingAxis.add_patch(plottingArc)
							
			for direction in directionsToPlot:
				if direction == DEFINES.MM_IMG_ID_CLOCKWIZE_DIR_IDENTIFIER:
					linestyle = DEFINES.PLOT_LINESTYLE_CLOCKWISE
				elif direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
					linestyle = DEFINES.PLOT_LINESTYLE_COUNTERCLOCKWISE
				for repetition in range(0,nbRepetitions):
					drawingAxis.plot(sortedCentroidsXY[repetition,startingPoint,axisToDraw,:,direction,0],sortedCentroidsXY[repetition,startingPoint,axisToDraw,:,direction,1],color = plotColors[startingPoint], marker = DEFINES.PLOT_XY_MARKER, linewidth = lineWidth, markersize = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)

#Model fit error
def plot_model_total_error(drawingAxis, lineWidth, calibResults):
	sortedCentroidsXY = calibResults.sortedCentroidsXY
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
	
	modelError = calibResults.modelError
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbStartingPoints))

	#Start plotting
	for startingPoint in range(0,nbStartingPoints):
		drawingAxis.scatter(np.ravel(1000*modelError[:,startingPoint,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,1]), np.ravel(1000*modelError[:,startingPoint,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,2]),color = plotColors[startingPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)

	minAxis = min(np.nanmin(1000*modelError[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,1]), np.nanmin(1000*modelError[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,2]))
	maxAxis = max(np.nanmax(1000*modelError[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,1]), np.nanmax(1000*modelError[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,2]))
	
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

def plot_model_error_a(drawingAxis, lineWidth, calibResults):
	plot_model_error(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_ALPHA)

def plot_model_error_b(drawingAxis, lineWidth, calibResults):
	plot_model_error(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_BETA)

def plot_model_error(drawingAxis, lineWidth, calibResults,  axisToDraw):
	sortedCentroidsXY = calibResults.sortedCentroidsXY
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
	
	modelError = calibResults.modelError
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbStartingPoints))

	#Start plotting
	for startingPoint in range(0,nbStartingPoints):
		drawingAxis.scatter(np.ravel(1000*modelError[:,startingPoint,axisToDraw,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,3]), np.ravel(1000*modelError[:,startingPoint,axisToDraw,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,4]),color = plotColors[startingPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)

	minAxis = min(np.nanmin(np.ravel(1000*modelError[:,:,axisToDraw,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,3])),np.nanmin(np.ravel(1000*modelError[:,:,axisToDraw,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,4])))
	maxAxis = max(np.nanmax(np.ravel(1000*modelError[:,:,axisToDraw,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,3])),np.nanmax(np.ravel(1000*modelError[:,:,axisToDraw,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,4])))
	
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

def plot_model_hist(drawingAxis, lineWidth, calibResults):
	modelError = calibResults.modelError

	if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
	elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
	else:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

	ravelledModelError = 1000*np.ravel(modelError[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,0])

	maxX = np.nanmax(ravelledModelError)
	xs = np.linspace(0,maxX,1000)

	density = gaussian_kde(ravelledModelError[~np.isnan(ravelledModelError)])
	density.covariance_factor = lambda : .25
	density._compute_covariance()
	drawingAxis.plot(xs,100*density(xs), color = 'darkblue', linewidth = lineWidth, label = f'{round(calibResults.mesRMSModelFit[-1],1):<3.1f} [um]')
	drawingAxis.legend(fontsize = textSize)

#Plot non-linearity
def plot_non_lin_a(drawingAxis, lineWidth, calibResults):
	plot_non_lin(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_ALPHA)

def plot_non_lin_b(drawingAxis, lineWidth, calibResults):
	plot_non_lin(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_BETA)

def plot_non_lin(drawingAxis, lineWidth, calibResults,  axisToDraw):
	axesToTest = calibResults.calibrationParameters.axesToTest
	
	if axisToDraw in axesToTest:
		sortedCentroidsXY = calibResults.sortedCentroidsXY
		commandedAngle = np.multiply(calibResults.sortedTargetCommand,180/np.pi)
		(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
		
		modelNonLinearity = np.multiply(calibResults.modelNonLinearity,180/np.pi)
		plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbStartingPoints))

		if nbDirections >= 2:
			directionsToPlot = DEFINES.PLOT_DIRECTIONS_TO_PLOT
		else:
			directionsToPlot = [0]

		for direction in directionsToPlot:
			if direction == DEFINES.MM_IMG_ID_CLOCKWIZE_DIR_IDENTIFIER:
				linestyle = DEFINES.PLOT_LINESTYLE_CLOCKWISE
			elif direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
				linestyle = DEFINES.PLOT_LINESTYLE_COUNTERCLOCKWISE
			for startingPoint in range(0,nbStartingPoints):
				for repetition in range(0,nbRepetitions):
					drawingAxis.plot(commandedAngle[startingPoint,axisToDraw,:,direction,axisToDraw],modelNonLinearity[repetition,startingPoint,axisToDraw,:,direction],color = plotColors[startingPoint], linestyle = linestyle, linewidth = lineWidth)

#Plot mean non-linearity
def plot_mean_non_lin_a(drawingAxis, lineWidth, calibResults):
	plot_mean_non_lin(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_ALPHA)

def plot_mean_non_lin_b(drawingAxis, lineWidth, calibResults):
	plot_mean_non_lin(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_BETA)

def plot_mean_non_lin(drawingAxis, lineWidth, calibResults,  axisToDraw):
	axesToTest = calibResults.calibrationParameters.axesToTest
	
	if axisToDraw in axesToTest:
		sortedCentroidsXY = calibResults.sortedCentroidsXY
		commandedAngle = np.multiply(calibResults.sortedTargetCommand,180/np.pi)
		(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
		
		modelNonLinearity = np.multiply(calibResults.modelNonLinearity,180/np.pi)
		plotColors = plt.cm.PiYG(np.linspace(0,1,nbDirections))

		meanNonLinearity = np.zeros((nbSteps,nbDirections))
		stdNonLinearity = np.zeros((nbSteps,nbDirections))
		minCurve = np.zeros((nbSteps,nbDirections))
		maxCurve = np.zeros((nbSteps,nbDirections))
		if nbDirections >= 2:
			directionsToPlot = DEFINES.PLOT_DIRECTIONS_TO_PLOT
		else:
			directionsToPlot = [0]
			
		for direction in directionsToPlot:
			if direction == DEFINES.MM_IMG_ID_CLOCKWIZE_DIR_IDENTIFIER:
				linestyle = DEFINES.PLOT_LINESTYLE_CLOCKWISE
			elif direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
				linestyle = DEFINES.PLOT_LINESTYLE_COUNTERCLOCKWISE
			for step in range(0,nbSteps):
				meanNonLinearity[step,direction] = np.nanmean(np.ravel(modelNonLinearity[:,:,axisToDraw,step,direction]))
				stdNonLinearity[step,direction] = np.nanstd(np.ravel(modelNonLinearity[:,:,axisToDraw,step,direction]))
				minCurve[step,direction] = meanNonLinearity[step,direction] - stdNonLinearity[step,direction]
				maxCurve[step,direction] = meanNonLinearity[step,direction] + stdNonLinearity[step,direction]

			drawingAxis.plot(commandedAngle[0,axisToDraw,:,direction,axisToDraw],meanNonLinearity[:,direction],color = plotColors[direction], linestyle = linestyle, linewidth = lineWidth)
			drawingAxis.fill_between(commandedAngle[0,axisToDraw,:,direction,axisToDraw],minCurve[:,direction],maxCurve[:,direction],color = DEFINES.PLOT_STD_FILL_COLOR, alpha = DEFINES.PLOT_STD_FILL_TRANSPARENCY)

#Plot uncertainty of non-linearity
def plot_unc_non_lin_a(drawingAxis, lineWidth, calibResults):
	plot_unc_non_lin(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_ALPHA)

def plot_unc_non_lin_b(drawingAxis, lineWidth, calibResults):
	plot_unc_non_lin(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_BETA)

def plot_unc_non_lin(drawingAxis, lineWidth, calibResults,  axisToDraw):
	axesToTest = calibResults.calibrationParameters.axesToTest
	
	if axisToDraw in axesToTest:
		sortedCentroidsXY = calibResults.sortedCentroidsXY
		commandedAngle = np.multiply(calibResults.sortedTargetCommand,180/np.pi)
		(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
		
		modelNonLinearity = np.multiply(calibResults.modelNonLinearity,180/np.pi)
		plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbStartingPoints))

		meanNonLinearity = np.zeros((nbSteps,nbDirections))
		stdNonLinearity = np.zeros((nbSteps,nbDirections))
		minCurve = np.zeros((nbSteps,nbDirections))
		maxCurve = np.zeros((nbSteps,nbDirections))
		if nbDirections >= 2:
			directionsToPlot = DEFINES.PLOT_DIRECTIONS_TO_PLOT
		else:
			directionsToPlot = [0]

		for direction in directionsToPlot:
			if direction == DEFINES.MM_IMG_ID_CLOCKWIZE_DIR_IDENTIFIER:
				linestyle = DEFINES.PLOT_LINESTYLE_CLOCKWISE
			elif direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
				linestyle = DEFINES.PLOT_LINESTYLE_COUNTERCLOCKWISE
			for step in range(0,nbSteps):
				meanNonLinearity[step,direction] = np.nanmean(np.ravel(modelNonLinearity[:,:,axisToDraw,step,direction]))
				stdNonLinearity[step,direction] = np.nanstd(np.ravel(modelNonLinearity[:,:,axisToDraw,step,direction]))
				minCurve[step,direction] = - stdNonLinearity[step,direction]
				maxCurve[step,direction] = stdNonLinearity[step,direction]

				modelNonLinearity[:,:,axisToDraw,step,direction] = np.subtract(modelNonLinearity[:,:,axisToDraw,step,direction],meanNonLinearity[step,direction])

			for startingPoint in range(0,nbStartingPoints):
				for repetition in range(0,nbRepetitions):
					drawingAxis.plot(commandedAngle[startingPoint,axisToDraw,:,direction,axisToDraw],modelNonLinearity[repetition,startingPoint,axisToDraw,:,direction],color = plotColors[startingPoint], linestyle = linestyle, linewidth = lineWidth)
			drawingAxis.fill_between(commandedAngle[0,axisToDraw,:,direction,axisToDraw],minCurve[:,direction],maxCurve[:,direction],color = DEFINES.PLOT_STD_FILL_COLOR, alpha = DEFINES.PLOT_STD_FILL_TRANSPARENCY)

#Plot hysteresis
def plot_hysteresis(drawingAxis, lineWidth, calibResults):
	axesToTest = calibResults.calibrationParameters.axesToTest
	sortedCentroidsXY = calibResults.sortedCentroidsXY
	commandedAngle = np.multiply(calibResults.sortedTargetCommand,180/np.pi)
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
	
	measuredHysteresis = np.multiply(calibResults.measuredHysteresis,180/np.pi)
	plotColors = plt.cm.bwr(np.linspace(0,1,nbAxes))
	linestyle = DEFINES.PLOT_LINESTYLE_COUNTERCLOCKWISE

	if nbDirections > 1:
		for axisToDraw in axesToTest:
			for startingPoint in range(0,nbStartingPoints):
				for repetition in range(0,nbRepetitions):
					drawingAxis.plot(commandedAngle[startingPoint,axisToDraw,:,0,axisToDraw],measuredHysteresis[repetition,startingPoint,axisToDraw,:],color = plotColors[axisToDraw], linestyle = linestyle, linewidth = lineWidth)
		
		if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
		elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
		else:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

		customLegend = [	Line2D([0], [0], color=plotColors[0], lw=lineWidth),
							Line2D([0], [0], color=plotColors[1], lw=lineWidth)]

		drawingAxis.legend(customLegend,['Alpha','Beta'], fontsize = textSize)

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

def plot_mean_hysteresis(drawingAxis, lineWidth, calibResults):
	axesToTest = calibResults.calibrationParameters.axesToTest
	sortedCentroidsXY = calibResults.sortedCentroidsXY
	commandedAngle = np.multiply(calibResults.sortedTargetCommand,180/np.pi)
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
	
	measuredHysteresis = np.multiply(calibResults.measuredHysteresis,180/np.pi)
	plotColors = plt.cm.bwr(np.linspace(0,1,nbAxes))
	linestyle = DEFINES.PLOT_LINESTYLE_COUNTERCLOCKWISE

	if nbDirections > 1:
		axesLabels = ['Alpha','Beta']
		for axisToDraw in axesToTest:
			meanHysteresis = np.zeros((nbSteps))
			stdHysteresis = np.zeros((nbSteps))
			minCurve = np.zeros((nbSteps))
			maxCurve = np.zeros((nbSteps))		
			for step in range(0,nbSteps):
				meanHysteresis[step] = np.nanmean(np.ravel(measuredHysteresis[:,:,axisToDraw,step]))
				stdHysteresis[step] = np.nanstd(np.ravel(measuredHysteresis[:,:,axisToDraw,step]))
				minCurve[step] = meanHysteresis[step] - stdHysteresis[step]
				maxCurve[step] = meanHysteresis[step] + stdHysteresis[step]

			drawingAxis.plot(commandedAngle[0,axisToDraw,:,0,axisToDraw],meanHysteresis[:],color = plotColors[axisToDraw], linestyle = linestyle, linewidth = lineWidth)
			drawingAxis.fill_between(commandedAngle[0,axisToDraw,:,0,axisToDraw],minCurve[:],maxCurve[:],color = DEFINES.PLOT_STD_FILL_COLOR, alpha = DEFINES.PLOT_STD_FILL_TRANSPARENCY)

		if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
		elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
		else:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

		customLegend = [	Line2D([0], [0], color=plotColors[0], lw=lineWidth),
							Line2D([0], [0], color=plotColors[1], lw=lineWidth)]

		drawingAxis.legend(customLegend,['Alpha','Beta'], fontsize = textSize)

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

	
#Plot repeatability
def plot_total_repeatability(drawingAxis, lineWidth, calibResults):
	sortedCentroidsXY = calibResults.sortedCentroidsXY
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
	
	measuredRepeatability = calibResults.measuredRepeatability
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbStartingPoints))

	#Start plotting
	if nbRepetitions > 1:
		for startingPoint in range(0,nbStartingPoints):
			drawingAxis.scatter(np.ravel(1000*measuredRepeatability[:,startingPoint,:,:,:,1]), np.ravel(1000*measuredRepeatability[:,startingPoint,:,:,:,2]),color = plotColors[startingPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		minAxis = min(np.nanmin(np.ravel(1000*measuredRepeatability[:,:,:,:,:,1])),np.nanmin(np.ravel(1000*measuredRepeatability[:,:,:,:,:,2])))
		maxAxis = max(np.nanmax(np.ravel(1000*measuredRepeatability[:,:,:,:,:,1])),np.nanmax(np.ravel(1000*measuredRepeatability[:,:,:,:,:,2])))
		
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

def plot_repeatability_a(drawingAxis, lineWidth, calibResults):
	plot_repeatability(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_ALPHA)

def plot_repeatability_b(drawingAxis, lineWidth, calibResults):
	plot_repeatability(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_BETA)

def plot_repeatability(drawingAxis, lineWidth, calibResults,  axisToDraw):
	sortedCentroidsXY = calibResults.sortedCentroidsXY
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
	
	measuredRepeatability = calibResults.measuredRepeatability
	plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbStartingPoints))

	#Start plotting
	if nbRepetitions > 1:
		for startingPoint in range(0,nbStartingPoints):
			drawingAxis.scatter(np.ravel(1000*measuredRepeatability[:,startingPoint,axisToDraw,:,:,3]), np.ravel(1000*measuredRepeatability[:,startingPoint,axisToDraw,:,:,4]),color = plotColors[startingPoint], marker = DEFINES.PLOT_XY_MARKER, s = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)
		minAxis = min(np.nanmin(np.ravel(1000*measuredRepeatability[:,:,axisToDraw,:,:,3])),np.nanmin(np.ravel(1000*measuredRepeatability[:,:,axisToDraw,:,:,4])))
		maxAxis = max(np.nanmax(np.ravel(1000*measuredRepeatability[:,:,axisToDraw,:,:,3])),np.nanmax(np.ravel(1000*measuredRepeatability[:,:,axisToDraw,:,:,4])))
		
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
		drawingAxis.text(0.5,0.5,DEFINES.PLOT_NOT_TESTED_CAPTION, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes, bbox=dict(boxstyle = 'round',ec = (0.5,0.5,1), fc=(0.8,0.8,1.)))

def plot_repeatability_hist(drawingAxis, lineWidth, calibResults):
	sortedCentroidsXY = calibResults.sortedCentroidsXY
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
	
	if nbRepetitions > 1:
		measuredRepeatability = calibResults.measuredRepeatability

		if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
		elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
		else:
			textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

		ravelledRepeatability = 1000*np.ravel(measuredRepeatability[:,:,:,:,:,0])
		maxX = np.nanmax(ravelledRepeatability)
		xs = np.linspace(0,maxX,1000)

		density = gaussian_kde(ravelledRepeatability[~np.isnan(ravelledRepeatability)])
		density.covariance_factor = lambda : .25
		density._compute_covariance()
		drawingAxis.plot(xs,100*density(xs), color = 'darkblue', linewidth = lineWidth, label = f'{round(calibResults.mesRMSRepeatability[-1],1):<3.1f} [um]')
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

#Plot exagerated circularity
def plot_circularity_mes_a(drawingAxis, lineWidth, calibResults):
	plot_circularity_mes(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_ALPHA)

def plot_circularity_mes_b(drawingAxis, lineWidth, calibResults):
	plot_circularity_mes(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_BETA)

def plot_circularity_mes(drawingAxis, lineWidth, calibResults,  axisToDraw):
	axesToTest = calibResults.calibrationParameters.axesToTest

	if axisToDraw in axesToTest:
		#Change axes scaling
		drawingAxis.set_aspect('equal')
		drawingAxis.set_xlim(	calibResults.modelCenter[0]-DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS,\
								calibResults.modelCenter[0]+DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS)
		drawingAxis.set_ylim(	calibResults.modelCenter[1]-DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS,\
								calibResults.modelCenter[1]+DEFINES.PLOT_MEASURES_AXES_LIMITS_RADIUS)
		drawingAxis.invert_yaxis()

		#Retrieve calib parameters
		sortedCentroidsXY = calibResults.sortedCentroidsXY
		(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
		
		modelEccentricity = calibResults.modelEccentricity
		fittedCircles = calibResults.fittedCircles
		measuredAngles = np.multiply(calibResults.measuredAngles,180/np.pi)

		plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbStartingPoints))
		
		if nbDirections >= 2:
			directionsToPlot = DEFINES.PLOT_DIRECTIONS_TO_PLOT
		else:
			directionsToPlot = [0]

		#Start plotting
		for startingPoint in range(0,nbStartingPoints):
			centerX = fittedCircles[startingPoint,axisToDraw][0]
			centerY = fittedCircles[startingPoint,axisToDraw][1]
			circleRadius = fittedCircles[startingPoint,axisToDraw][2]
			plottingArc = 	patches.Arc(	(centerX,centerY),\
											2*circleRadius,2*circleRadius,\
											0,0,360,\
											color = DEFINES.PLOT_ARC_COLOR, linestyle = DEFINES.PLOT_ARC_LINESTYLE, linewidth = lineWidth*DEFINES.PLOT_ARC_LINEWIDTH_RATIO)
			drawingAxis.add_patch(plottingArc)
			
			for direction in directionsToPlot:
				if direction == DEFINES.MM_IMG_ID_CLOCKWIZE_DIR_IDENTIFIER:
					linestyle = DEFINES.PLOT_LINESTYLE_CLOCKWISE
				elif direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
					linestyle = DEFINES.PLOT_LINESTYLE_COUNTERCLOCKWISE
				for repetition in range(0,nbRepetitions):
					exageratedCircularity = np.zeros((nbSteps,2))
					for step in range(0,nbSteps):
						measureX = sortedCentroidsXY[repetition,startingPoint,axisToDraw,step,direction,0]
						measureY = sortedCentroidsXY[repetition,startingPoint,axisToDraw,step,direction,1]
						measuredAngle = np.mod(np.arctan2(measureY-centerY,measureX-centerX),2*np.pi)
						
						newRadius = circleRadius+modelEccentricity[repetition,startingPoint,axisToDraw,step,direction]*DEFINES.PLOT_CIRCULARITY_EXAGERATION_RATIO
						
						exageratedCircularity[step,0] = centerX+np.cos(measuredAngle)*newRadius
						exageratedCircularity[step,1] = centerY+np.sin(measuredAngle)*newRadius

					drawingAxis.plot(exageratedCircularity[:,0],exageratedCircularity[:,1],color = plotColors[startingPoint], marker = DEFINES.PLOT_XY_MARKER, linewidth = lineWidth, markersize = lineWidth*DEFINES.PLOT_MARKERSIZE_RATIO)

#Plot circularity
def plot_circularity_a(drawingAxis, lineWidth, calibResults):
	plot_circularity(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_ALPHA)

def plot_circularity_b(drawingAxis, lineWidth, calibResults):
	plot_circularity(drawingAxis, lineWidth, calibResults,  DEFINES.PARAM_AXIS_BETA)

def plot_circularity(drawingAxis, lineWidth, calibResults,  axisToDraw):
	axesToTest = calibResults.calibrationParameters.axesToTest

	if axisToDraw in axesToTest:
		sortedCentroidsXY = calibResults.sortedCentroidsXY
		commandedAngle = np.multiply(calibResults.sortedTargetCommand,180/np.pi)
		(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
		
		modelEccentricity = calibResults.modelEccentricity
		plotColors = plt.cm.gist_rainbow(np.linspace(0,1,nbStartingPoints))

		if axisToDraw in axesToTest:
			if nbDirections >= 2:
				directionsToPlot = DEFINES.PLOT_DIRECTIONS_TO_PLOT
			else:
				directionsToPlot = [0]

			for direction in directionsToPlot:
				if direction == DEFINES.MM_IMG_ID_CLOCKWIZE_DIR_IDENTIFIER:
					linestyle = DEFINES.PLOT_LINESTYLE_CLOCKWISE
				elif direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
					linestyle = DEFINES.PLOT_LINESTYLE_COUNTERCLOCKWISE
				for startingPoint in range(0,nbStartingPoints):
					for repetition in range(0,nbRepetitions):
						drawingAxis.plot(commandedAngle[startingPoint,axisToDraw,:,direction,axisToDraw],1000*modelEccentricity[repetition,startingPoint,axisToDraw,:,direction],color = plotColors[startingPoint], linestyle = linestyle, linewidth = lineWidth)

#Display informations
def plot_test_parameters(drawingAxis, lineWidth, calibResults):
	axesToTest = calibResults.calibrationParameters.axesToTest
	sortedCentroidsXY = calibResults.sortedCentroidsXY
	valuesToRemove = calibResults.valuesToRemove
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
	
	if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
	elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
	else:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

	drawingAxis.set_axis_off()
	drawingAxis.set_xlim(0,1)
	drawingAxis.set_ylim(0,1)

	if nbDirections > 1:
		hystStr = 'Enabled'
	else:
		hystStr = 'Disabled'

	if calibResults.calibrationParameters.storeHallPositions:
		hallStr = 'Enabled'
	else:
		hallStr = 'Disabled'

	#Compute the actual number of poitns performed during calibration
	totalNbPoints = nbRepetitions*nbStartingPoints*nbSteps*nbDirections

	performedPointsAlpha = 0
	performedPointsBeta = 0

	if DEFINES.PARAM_AXIS_ALPHA in axesToTest:
		performedPointsAlpha = totalNbPoints-np.count_nonzero(np.isnan(np.ravel(sortedCentroidsXY[:,:,DEFINES.PARAM_AXIS_ALPHA,:,:,0])))

	if DEFINES.PARAM_AXIS_BETA in axesToTest:
		performedPointsBeta = totalNbPoints-np.count_nonzero(np.isnan(np.ravel(sortedCentroidsXY[:,:,DEFINES.PARAM_AXIS_BETA,:,:,0])))

	#+str(calibResults.positionerID)
	IDDate			= f'Completed {calibResults.completionTime}'
	IDText			= f'Positioner {calibResults.positionerID:<4} ({calibResults.testBenchName} slot #{calibResults.slotID:1})'
	generalLegend 	= [	'Nb repetitions:',\
						'Nb starting Points:',\
						'Nb steps:',\
						'Total points per axis:',\
						'Hysteresis:',\
						'Hall sensors:']
	generalVars 	= [	f'{nbRepetitions:>6}',\
						f'{nbStartingPoints:>6}',\
						f'{nbSteps:>6}',\
						f'{totalNbPoints:>6}',\
						hystStr,\
						hallStr]
	motorLegend		= [	'Speed [RPM]',\
						'Current [%]',\
						'Range [°]',\
						'Tested points']
	alphaTitle		= 	'Alpha'
	alphaText		= [	f'{calibResults.calibrationParameters.motorRpmAlpha:>6}',\
						f'{calibResults.calibrationParameters.cruiseCurrentAlpha:>6}',\
						f'{calibResults.calibrationParameters.alphaAxisRange[0]:>3} to {calibResults.calibrationParameters.alphaAxisRange[1]:>3}',\
						f'{performedPointsAlpha:>6}']
	
	betaTitle		= 	'Beta'
	betaText		= [	f'{calibResults.calibrationParameters.motorRpmBeta:>6}',\
						f'{calibResults.calibrationParameters.cruiseCurrentBeta:>6}',\
						f'{calibResults.calibrationParameters.betaAxisRange[0]:>3} to {calibResults.calibrationParameters.betaAxisRange[1]:>3}',\
						f'{performedPointsBeta:>6}']

	drawingAxis.text(0.5,1-0.02, IDText, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.5,1-0.09, IDDate, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	
	drawingAxis.text(0.02,1-0.2,generalLegend[0], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.27,generalLegend[1], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.34,generalLegend[2], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.41,generalLegend[3], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.48,generalLegend[4], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.02,1-0.55,generalLegend[5], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.2,generalVars[0], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.27,generalVars[1], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.34,generalVars[2], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.41,generalVars[3], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.48,generalVars[4], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.55,generalVars[5], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	
	drawingAxis.text(0.02,1-0.65,alphaTitle, size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.98,1-0.65,betaTitle, size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.5,1-0.75,motorLegend[0], size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.5,1-0.82,motorLegend[1], size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.5,1-0.89,motorLegend[2], size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.5,1-0.96,motorLegend[3], size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	if DEFINES.PARAM_AXIS_ALPHA in axesToTest:
		drawingAxis.text(0.02,1-0.75,alphaText[0], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
		drawingAxis.text(0.02,1-0.82,alphaText[1], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
		drawingAxis.text(0.02,1-0.89,alphaText[2], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
		if performedPointsAlpha == totalNbPoints:
			drawingAxis.text(0.02,1-0.96,alphaText[3], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes)
		else:
			drawingAxis.text(0.02,1-0.96,alphaText[3], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes, color = DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	else:
		drawingAxis.text(0.02,1-0.82,DEFINES.PLOT_NOT_TESTED_CAPTION, size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes, bbox=dict(boxstyle = 'round',ec = (0.5,0.5,1), fc=(0.8,0.8,1.)))
	if DEFINES.PARAM_AXIS_BETA in axesToTest:
		drawingAxis.text(0.98,1-0.75,betaText[0], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
		drawingAxis.text(0.98,1-0.82,betaText[1], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
		drawingAxis.text(0.98,1-0.89,betaText[2], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
		if performedPointsBeta == totalNbPoints:
			drawingAxis.text(0.98,1-0.96,betaText[3], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes)
		else:
			drawingAxis.text(0.98,1-0.96,betaText[3], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes, color = DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	else:
		drawingAxis.text(0.98,1-0.82,DEFINES.PLOT_NOT_TESTED_CAPTION, size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes, bbox=dict(boxstyle = 'round',ec = (0.5,0.5,1), fc=(0.8,0.8,1.)))

def plot_requirements(drawingAxis, lineWidth, calibResults):
	axesToTest 			= calibResults.calibrationParameters.axesToTest
	sortedCentroidsXY 	= calibResults.sortedCentroidsXY
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = sortedCentroidsXY.shape
	commandedAngle 		= np.multiply(calibResults.sortedTargetCommand,180/np.pi)
	requirements 		= calibResults.requirements

	if lineWidth == DEFINES.PLOT_LINEWIDTH_SINGLE:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE
	elif lineWidth == DEFINES.PLOT_LINEWIDTH_OVERVIEW:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_OVERVIEW
	else:
		textSize = DEFINES.PLOT_TEXT_FONTSIZE_SINGLE

	drawingAxis.set_axis_off()
	drawingAxis.set_xlim(0,1)
	drawingAxis.set_ylim(0,1)
	
	IDDate			= calibResults.config.currentProjectTime
	IDText			= f'Positioner {calibResults.positionerID:<4}'
	generalLegend 	= [	'Alpha length [mm]:',\
						'Beta length [mm]:',\
						'RMS model fit [um]:',\
						'RMS repeatability [um]:',\
						'Max hysteresis [°]:',\
						'Max non-linearity [°]:',\
						'Max NL derivative [°/°]:',\
						'RMS alignment error [°]:',\
						'Max alignment error [°]:',\
						'Max roundness error [um]:']

	alphaLength = calibResults.mesAlphaLength[-1]
	betaLength = calibResults.mesBetaLength[-1]
	RMSModelFit = calibResults.mesRMSModelFit[-1]
	RMSRepeatability = calibResults.mesRMSRepeatability[-1]
	maxHysteresis = calibResults.mesMaxHysteresis[-1]
	maxNonLinearity = calibResults.mesMaxNL[-1]
	maxNonLinDerivative = calibResults.mesMaxNLDerivative[-1]
	RMSalignmentError = calibResults.mesRMSAlignmentError[-1]
	maxAlignmentError = calibResults.mesMaxAlignmentError[-1]
	roundnessDeviation = calibResults.mesMaxRoundnessError[-1]

	generalVars 	= [	f'{round(alphaLength,2):4.2f}',\
						f'{round(betaLength,2):4.2f}',\
						f'{round(RMSModelFit,2):4.2f}',\
						f'{round(RMSRepeatability,2):4.2f}',\
						f'{round(maxHysteresis,3):4.3f}',\
						f'{round(maxNonLinearity,3):4.3f}',\
						f'{round(maxNonLinDerivative,3):4.3f}',\
						f'{round(RMSalignmentError,3):4.3f}',\
						f'{round(maxAlignmentError,3):4.3f}',\
						f'{round(roundnessDeviation,2):4.2f}']

	#Check the requirements
	textColors 		= []
	i = 0

	if DEFINES.PARAM_AXIS_ALPHA not in axesToTest or alphaLength == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif abs(alphaLength - requirements.nominalAlphaLength) <= requirements.maxAlphaLengthDeviation:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	i += 1

	if DEFINES.PARAM_AXIS_BETA not in axesToTest or betaLength == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif abs(betaLength - requirements.nominalBetaLength) <= requirements.maxBetaLengthDeviation:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	i += 1

	if DEFINES.PARAM_AXIS_ALPHA not in axesToTest or DEFINES.PARAM_AXIS_BETA not in axesToTest or RMSModelFit == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif RMSModelFit <= requirements.maxPosError:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	i += 1

	if DEFINES.PARAM_AXIS_ALPHA not in axesToTest or DEFINES.PARAM_AXIS_BETA not in axesToTest or not nbRepetitions > 1 or RMSRepeatability == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif RMSRepeatability <= requirements.rmsPosRepeatability:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	i += 1

	if DEFINES.PARAM_AXIS_ALPHA not in axesToTest or DEFINES.PARAM_AXIS_BETA not in axesToTest or maxHysteresis == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif maxHysteresis <= requirements.maxHysteresis:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	i += 1
	
	if DEFINES.PARAM_AXIS_ALPHA not in axesToTest or DEFINES.PARAM_AXIS_BETA not in axesToTest or maxNonLinearity == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif maxNonLinearity <= requirements.maxNonLinearity:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	i += 1
	
	if DEFINES.PARAM_AXIS_ALPHA not in axesToTest or DEFINES.PARAM_AXIS_BETA not in axesToTest or maxNonLinDerivative == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif maxNonLinDerivative <= requirements.maxNonLinearityDerivative:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	i += 1
	
	if DEFINES.PARAM_AXIS_ALPHA not in axesToTest or DEFINES.PARAM_AXIS_BETA not in axesToTest or not calibResults.calibrationParameters.includeTiltRun or rmsAlignmentError == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif RMSalignmentError <= requirements.rmsAlignmentError:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	i += 1
	
	if DEFINES.PARAM_AXIS_ALPHA not in axesToTest or DEFINES.PARAM_AXIS_BETA not in axesToTest or not calibResults.calibrationParameters.includeTiltRun or maxAlignmentError == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif maxAlignmentError <= requirements.maxAlignmentError:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	i += 1
	
	if DEFINES.PARAM_AXIS_ALPHA not in axesToTest or DEFINES.PARAM_AXIS_BETA not in axesToTest or roundnessDeviation == np.nan:
		textColors.append(DEFINES.PLOT_REQUIREMENT_NOT_AVAILABLE_COLOR)
		generalVars[i] = DEFINES.PLOT_REQUIREMENT_N_A_TEXT
	elif roundnessDeviation <= requirements.maxRoundnessDeviation:
		textColors.append(DEFINES.PLOT_REQUIREMENT_PASSED_COLOR)
	else:
		textColors.append(DEFINES.PLOT_REQUIREMENT_FAILED_COLOR)
	
	textIncrement = 0.07
	textStart = 0.20

	
	drawingAxis.text(0.5,1-0.02, IDText, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	drawingAxis.text(0.5,1-0.09, IDDate, size = textSize, rotation = 0, horizontalalignment='center',verticalalignment='center',transform = drawingAxis.transAxes)
	
	for i in range(0,len(generalLegend)):
		textVerticalPlace = 1-textStart-i*textIncrement
		drawingAxis.text(0.02,textVerticalPlace,generalLegend[i], size = textSize, rotation = 0, horizontalalignment='left',verticalalignment='center',transform = drawingAxis.transAxes, color = textColors[i])
		drawingAxis.text(0.98,textVerticalPlace,generalVars[i], size = textSize, rotation = 0, horizontalalignment='right',verticalalignment='center',transform = drawingAxis.transAxes, color = textColors[i])
	

#All plotting parameters
plotProperties	= [	[plot_measures_a,			'Alpha measures', 																				'X [mm]', 				'Y [mm]'],\
					[plot_measures_b,			'Beta measures', 																				'X [mm]', 				'Y [mm]'],\
					[plot_model_total_error,	'Total model error',																			'X error [um]',			'Y error [um]'],\
					[plot_model_error_a,		'Alpha model error',																			'Across axis [um]',		'Along axis [um]'],\
					[plot_model_error_b,		'Beta model error',																				'Across axis [um]',		'Along axis [um]'],\
					[plot_model_hist,			'Model fit distribution',																		'Model fit error [um]',	'% occurences'],\
					[plot_non_lin_a,			'Non-linearity Alpha', 																			'Commanded angle [°]', 	'Non-linearity [°]'],\
					[plot_non_lin_b,			'Non-linearity Beta', 																			'Commanded angle [°]', 	'Non-linearity [°]'],\
					[plot_mean_non_lin_a,		'Mean non-linearity Alpha', 																	'Commanded angle [°]', 	'Mean non-linearity [°]'],\
					[plot_mean_non_lin_b,		'Mean non-linearity Beta', 																		'Commanded angle [°]', 	'Mean non-linearity [°]'],\
					[plot_unc_non_lin_a,		'Non-linearity uncertainty Alpha', 																'Commanded angle [°]', 	'Non-linearity uncertainty [°]'],\
					[plot_unc_non_lin_b,		'Non-linearity uncertainty Beta', 																'Commanded angle [°]', 	'Non-linearity uncertainty [°]'],\
					[plot_hysteresis,			'Hysteresis', 																					'Commanded angle [°]', 	'Hysteresis [°]'],\
					[plot_mean_hysteresis,		'Mean hysteresis', 																				'Commanded angle [°]', 	'Mean hysteresis [°]'],\
					[plot_total_repeatability,	'Total repeatability', 																			'X [um]', 				'Y [um]'],\
					[plot_repeatability_a,		'Alpha repeatability',																			'Across axis [um]',		'Along axis [um]'],\
					[plot_repeatability_b,		'Beta repeatability',																			'Across axis [um]',		'Along axis [um]'],\
					[plot_repeatability_hist,	'Repeatability distribution',																	'Repeatability [um]',	'% occurences'],\
					[plot_circularity_mes_a,	'Alpha circularity (exagerated '+str(DEFINES.PLOT_CIRCULARITY_EXAGERATION_RATIO)+'x)', 			'X [mm]', 				'Y [mm]'],\
					[plot_circularity_mes_b,	'Beta circularity (exagerated '+str(DEFINES.PLOT_CIRCULARITY_EXAGERATION_RATIO)+'x)', 			'X [mm]', 				'Y [mm]'],\
					[plot_circularity_a,		'Alpha circularity error', 																		'Commanded angle [°]', 	'Circularity deviation [um]'],\
					[plot_circularity_b,		'Beta circularity error',																		'Commanded angle [°]', 	'Circularity deviation [um]'],\
					[plot_test_parameters,		'Test parameters',																				'',						''],\
					[plot_requirements,			'Requirements',																					'',						'']]


def plot_lifetime_lengthAlpha(drawingAxis, lineWidth, calibResults):
	currentLifetimeIteration = calibResults.config.currentLifetimeIteration

	#Start plotting
	drawingAxis.plot(range(1,currentLifetimeIteration+2), calibResults.mesAlphaLength, color = 'darkblue', linewidth = lineWidth)
	
	minAxis = min(calibResults.mesAlphaLength) - calibResults.requirements.maxAlphaLengthDeviation
	maxAxis = max(calibResults.mesAlphaLength) + calibResults.requirements.maxAlphaLengthDeviation

	drawingAxis.set_xlim(1,calibResults.config.currentLifetimeIteration)
	drawingAxis.set_ylim(minAxis,maxAxis)

	minAlpha = calibResults.requirements.nominalAlphaLength-calibResults.requirements.maxAlphaLengthDeviation
	maxAlpha = calibResults.requirements.nominalAlphaLength+calibResults.requirements.maxAlphaLengthDeviation

	#Add the validity rectangles
	addValidityRectanglesY(drawingAxis, minAxis, maxAxis, minAlpha, maxAlpha, 1, calibResults.config.currentLifetimeIteration)
	

def plot_lifetime_lengthBeta(drawingAxis, lineWidth, calibResults):
	currentLifetimeIteration = calibResults.config.currentLifetimeIteration

	#Start plotting
	drawingAxis.plot(range(1,currentLifetimeIteration+2), calibResults.mesBetaLength, color = 'darkblue', linewidth = lineWidth)
	
	minAxis = min(calibResults.mesBetaLength)-calibResults.requirements.maxBetaLengthDeviation
	maxAxis = max(calibResults.mesBetaLength)+calibResults.requirements.maxBetaLengthDeviation

	drawingAxis.set_xlim(1,calibResults.config.currentLifetimeIteration)
	drawingAxis.set_ylim(minAxis,maxAxis)

	minBeta = calibResults.requirements.nominalBetaLength-calibResults.requirements.maxBetaLengthDeviation
	maxBeta = calibResults.requirements.nominalBetaLength+calibResults.requirements.maxBetaLengthDeviation

	#Add the validity rectangles
	addValidityRectanglesY(drawingAxis, minAxis, maxAxis, minBeta, maxBeta, 1, calibResults.config.currentLifetimeIteration)

def plot_lifetime_RMSModelFit(drawingAxis, lineWidth, calibResults):
	currentLifetimeIteration = calibResults.config.currentLifetimeIteration

	#Start plotting
	drawingAxis.plot(range(1,currentLifetimeIteration+2), calibResults.mesRMSModelFit, color = 'darkblue', linewidth = lineWidth)
	
	minAxis = 0
	maxAxis = max(calibResults.mesRMSModelFit)

	if maxAxis < 0:
		maxAxis = 1
	else:
		maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN
	
	drawingAxis.set_xlim(1,calibResults.config.currentLifetimeIteration)
	drawingAxis.set_ylim(minAxis,maxAxis)

	#Add the validity rectangles
	addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, calibResults.requirements.maxRoundnessDeviation, 1, calibResults.config.currentLifetimeIteration)
	
def plot_lifetime_RMSRepeatability(drawingAxis, lineWidth, calibResults):
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = calibResults.sortedCentroidsXY.shape
	currentLifetimeIteration = calibResults.config.currentLifetimeIteration

	if nbRepetitions>1 and calibResults.mesMaxHysteresis != np.nan:
		#Start plotting
		drawingAxis.plot(range(1,currentLifetimeIteration+2), calibResults.mesRMSRepeatability, color = 'darkblue', linewidth = lineWidth)
		
		minAxis = 0
		maxAxis = max(calibResults.mesRMSRepeatability)
		
		if maxAxis < 0:
			maxAxis = 1
		else:
			maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

		drawingAxis.set_xlim(1,calibResults.config.currentLifetimeIteration)
		drawingAxis.set_ylim(minAxis,maxAxis)

		#Add the validity rectangles
		addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, calibResults.requirements.rmsPosRepeatability, 1, calibResults.config.currentLifetimeIteration)
	
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

def plot_lifetime_MaxHysteresis(drawingAxis, lineWidth, calibResults):
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = calibResults.sortedCentroidsXY.shape
	currentLifetimeIteration = calibResults.config.currentLifetimeIteration

	if nbDirections>1 and calibResults.mesMaxHysteresis != np.nan:
		#Start plotting
		drawingAxis.plot(range(1,currentLifetimeIteration+2), calibResults.mesMaxHysteresis, color = 'darkblue', linewidth = lineWidth)
		
		minAxis = 0
		maxAxis = max(calibResults.mesMaxHysteresis)

		if maxAxis < 0.01:
			maxAxis = 0.01
		else:
			maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

		drawingAxis.set_xlim(1,calibResults.config.currentLifetimeIteration)
		drawingAxis.set_ylim(minAxis,maxAxis)

		#Add the validity rectangles
		addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, calibResults.requirements.maxHysteresis, 1, calibResults.config.currentLifetimeIteration)
	
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

def plot_lifetime_MaxNL(drawingAxis, lineWidth, calibResults):
	currentLifetimeIteration = calibResults.config.currentLifetimeIteration

	#Start plotting
	drawingAxis.plot(range(1,currentLifetimeIteration+2), calibResults.mesMaxNL, color = 'darkblue', linewidth = lineWidth)
	
	minAxis = 0
	maxAxis = max(calibResults.mesMaxNL)+0.2
	
	drawingAxis.set_xlim(1,calibResults.config.currentLifetimeIteration)
	drawingAxis.set_ylim(minAxis,maxAxis)

	#Add the validity rectangles
	addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, calibResults.requirements.maxNonLinearity, 1, calibResults.config.currentLifetimeIteration)
	

def plot_lifetime_RMSAlignmentError(drawingAxis, lineWidth, calibResults):
	currentLifetimeIteration = calibResults.config.currentLifetimeIteration

	if calibResults.calibrationParameters.includeTiltRun and calibResults.mesRMSAlignmentError != np.nan:
		#Start plotting
		drawingAxis.plot(range(1,currentLifetimeIteration+2), calibResults.mesRMSAlignmentError, color = 'darkblue', linewidth = lineWidth)
		
		minAxis = 0
		maxAxis = max(calibResults.mesRMSAlignmentError)

		if maxAxis < 0.01:
			maxAxis = 0.01
		else:
			maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

		drawingAxis.set_xlim(1,calibResults.config.currentLifetimeIteration)
		drawingAxis.set_ylim(minAxis,maxAxis)

		#Add the validity rectangles
		addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, calibResults.requirements.rmsAlignmentError, 1, calibResults.config.currentLifetimeIteration)
	
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

def plot_lifetime_MaxAlignmentError(drawingAxis, lineWidth, calibResults):
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData) = calibResults.sortedCentroidsXY.shape
	currentLifetimeIteration = calibResults.config.currentLifetimeIteration

	if calibResults.calibrationParameters.includeTiltRun and calibResults.mesMaxAlignmentError != np.nan:
		#Start plotting
		drawingAxis.plot(range(1,currentLifetimeIteration+2), calibResults.mesMaxAlignmentError, color = 'darkblue', linewidth = lineWidth)
		
		minAxis = 0
		maxAxis = max(calibResults.mesMaxAlignmentError)

		if maxAxis < 0.01:
			maxAxis = 0.01
		else:
			maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN

		drawingAxis.set_xlim(1,calibResults.config.currentLifetimeIteration)
		drawingAxis.set_ylim(minAxis,maxAxis)

		#Add the validity rectangles
		addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, calibResults.requirements.maxAlignmentError, 1, calibResults.config.currentLifetimeIteration)
	
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

def plot_lifetime_MaxRoundnessError(drawingAxis, lineWidth, calibResults):
	currentLifetimeIteration = calibResults.config.currentLifetimeIteration

	#Start plotting
	drawingAxis.plot(range(1,currentLifetimeIteration+2), calibResults.mesMaxRoundnessError, color = 'darkblue', linewidth = lineWidth)
	
	minAxis = 0
	maxAxis = max(calibResults.mesMaxRoundnessError)
		
	if maxAxis < 1:
		maxAxis = 1
	else:
		maxAxis *= 1+DEFINES.PLOT_AXIS_STRETCH_MARGIN
	
	drawingAxis.set_xlim(1,calibResults.config.currentLifetimeIteration)
	drawingAxis.set_ylim(minAxis,maxAxis)

	#Add the validity rectangles
	addValidityRectanglesY(drawingAxis, minAxis, maxAxis, 0, calibResults.requirements.maxRoundnessDeviation, 1, calibResults.config.currentLifetimeIteration)
	
plotPropertiesLifetime	= [	[plot_lifetime_lengthAlpha,			'Lifetime alpha length', 			'Lifetime iteration', 	'Alpha length [mm]'],\
							[plot_lifetime_lengthBeta,			'Lifetime beta length', 			'Lifetime iteration', 	'Beta length [mm]'],\
							[plot_lifetime_RMSModelFit,			'Lifetime RMS model fit',			'Lifetime iteration',	'RMS model fit [um]'],\
							[plot_lifetime_RMSRepeatability,	'Lifetime RMS repeatability',		'Lifetime iteration',	'RMS repeatability [um]'],\
							[plot_lifetime_MaxHysteresis,		'Lifetime maximal hysteresis',		'Lifetime iteration',	'Maximal hysteresis [°]'],\
							[plot_lifetime_MaxNL,				'Lifetime maximal non-linearity',	'Lifetime iteration',	'Maximal non-linearity [°]'],\
							[plot_lifetime_RMSAlignmentError,	'Lifetime RMS alignment error', 	'Lifetime iteration', 	'RMS alignment error [°]'],\
							[plot_lifetime_MaxAlignmentError,	'Lifetime maximal alignment error', 'Lifetime iteration', 	'Maximal alignment error [°]'],\
							[plot_lifetime_MaxRoundnessError,	'Lifetime maximal roundness error', 'Lifetime iteration', 	'Maximal roundness error [um]']]

def addValidityRectanglesX(drawingAxis, minAxis, maxAxis, minRequirement, maxRequirement, yStart, yEnd):
	if maxAxis > maxRequirement:
		if maxRequirement <= minAxis: #alphaMax is exceeding the plot - no validity region
			nonValidRectangleRight = patches.Rectangle((minAxis, yStart), abs(maxAxis-minAxis), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(nonValidRectangleRight)
		
		elif minAxis < minRequirement: #validity borned by the requirements on left and right
			validRectangle = patches.Rectangle((minRequirement, yStart), abs(maxRequirement-minRequirement), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			nonValidRectangleRight = patches.Rectangle((maxRequirement, yStart), abs(maxAxis-maxRequirement), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			nonValidRectangleLeft = patches.Rectangle((minAxis, yStart), abs(minRequirement-minAxis), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(validRectangle)
			drawingAxis.add_patch(nonValidRectangleRight)
			drawingAxis.add_patch(nonValidRectangleLeft)

		else: #validity borned by the requirements on right and axis on left
			validRectangle = patches.Rectangle((minAxis, yStart), abs(maxRequirement-minAxis), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			nonValidRectangleRight = patches.Rectangle((maxRequirement, yStart), abs(maxAxis-maxRequirement), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(validRectangle)
			drawingAxis.add_patch(nonValidRectangleRight)

	elif minAxis < minRequirement: 
		if minRequirement >= maxAxis: #alphaMin is exceeding the plot - no validity region
			nonValidRectangleLeft = patches.Rectangle((minAxis, yStart), abs(maxAxis-minAxis), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(nonValidRectangleLeft)
		
		else: #validity borned by the requirements on left and axis on right
			validRectangle = patches.Rectangle((minRequirement, yStart), abs(maxAxis-minRequirement), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			nonValidRectangleLeft = patches.Rectangle((minAxis, yStart), abs(minRequirement-minAxis), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_NON_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
			drawingAxis.add_patch(validRectangle)
			drawingAxis.add_patch(nonValidRectangleLeft)
	
	else: #validity borned by the axis on right and left
		validRectangle = patches.Rectangle((minAxis, yStart), abs(maxAxis-minAxis), yEnd-yStart, edgecolor = 'None', facecolor = DEFINES.PLOT_CONFORM_AREA_FILL_COLOR, alpha = DEFINES.PLOT_CONFORMITY_AREA_FILL_ALPHA, fill = True)
		drawingAxis.add_patch(validRectangle)

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
	a = 1

if __name__ == '__main__':
	main()