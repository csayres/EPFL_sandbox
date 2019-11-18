#cython: language_level=3
import DEFINES
import miscmath as mm
from scipy import optimize, io, interpolate, stats
import calibPlot as customPlot
import numpy as np
import os
import time
import logger as log
import matplotlib.pyplot as plt
import json
import copy
import classConfig
import classPositioners
import gc
import errors

class Parameters():
	__slots__ = (	'approachDistance',\
					'cruiseCurrentAlpha',\
					'cruiseCurrentBeta',\
					'motorRpmAlpha',\
					'motorRpmBeta',\
					'waitCurrentAlpha',\
					'waitCurrentBeta',\
					'numberOfStartingPoints',\
					'numberOfRepetitions',\
					'numberOfStepsPerCircle',\
					'axesToTest',\
					'hysteresisEnable',\
					'alphaAxisRange',\
					'betaAxisRange',\
					'storeHallPositions',\
					'resetOffsetAfterCalib',\
					'includeTiltRun',\
					'bigCentroidRatio')

	def __init__(self):
		self.approachDistance					= 0.5		# [deg]

		self.cruiseCurrentAlpha					= 100		# [%]
		self.cruiseCurrentBeta					= 100		# [%]
		self.motorRpmAlpha 						= 4000		# [RPM]
		self.motorRpmBeta 						= 4000		# [RPM]
		self.waitCurrentAlpha 					= 30 		# [%]
		self.waitCurrentBeta 					= 30 		# [%]

		self.numberOfStartingPoints				= 5	#10
		self.numberOfRepetitions				= 3
		self.numberOfStepsPerCircle				= 183		# Minimum 4 for correct circle fitting #365
		self.axesToTest							= [DEFINES.PARAM_AXIS_ALPHA, DEFINES.PARAM_AXIS_BETA]
		self.hysteresisEnable					= True
		self.alphaAxisRange						= [-2, 362]	# [deg]
		self.betaAxisRange						= [-2, 362]	# [deg]
		self.storeHallPositions					= False
		self.resetOffsetAfterCalib				= False

		#Tilt parameters
		self.includeTiltRun						= False
		self.bigCentroidRatio					= 10		# Each x-th point will grab a big centroid

	def load(self,fileName):
		#Load all the data in the file, exculding the fileInfos
		try:
			with open(os.path.join(fileName),'r') as inFile:
				variablesToLoad=json.load(inFile)
				for key in variablesToLoad.keys():
					if key in type(self).__slots__:
						setattr(self, key, variablesToLoad[key])
					else:
						log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING,1,f'Unexpected data was encountered during the loading of the calibration parameters. Faulty key: {key}')
						if DEFINES.RAISE_ERROR_ON_UNEXPECTED_KEY:
							raise errors.IOError('Unexpected data was encountered during the loading of the calibration parameters') from None
						
		except OSError:
			raise errors.IOError('The calibration parameters file could not be found') from None

	def save(self,filePath,fileName):
		variablesToSave = {}
		for slots in [getattr(cls, '__slots__', []) for cls in type(self).__mro__]:
			for attr in slots:
				variablesToSave[attr] = getattr(self, attr)

		os.makedirs(filePath, exist_ok=True)
		with open(os.path.join(filePath, fileName),'w+') as outFile:
			json.dump(variablesToSave, outFile, separators = (',\n',': '))

	def check_parameters(self, positionerPhysics):
		#Check data consistency
		if self.alphaAxisRange[0] < positionerPhysics.alphaAxisRange[0]:
			raise errors.OutOfRangeError(f'Alpha axis range start value is too small (minimum: {positionerPhysics.alphaAxisRange[0]:f5.2})') from None
		if self.alphaAxisRange[1] > positionerPhysics.alphaAxisRange[1]:
			raise errors.OutOfRangeError(f'Alpha axis range end value is too big (maximum: {positionerPhysics.alphaAxisRange[1]:f5.2})') from None
		if self.betaAxisRange[0] < positionerPhysics.betaAxisRange[0]:
			raise errors.OutOfRangeError(f'Beta axis range start value is too small (minimum: {positionerPhysics.betaAxisRange[0]:f5.2})') from None
		if self.betaAxisRange[1] > positionerPhysics.betaAxisRange[1]:
			raise errors.OutOfRangeError(f'Beta axis range end value is too big (maximum: {positionerPhysics.betaAxisRange[1]:f5.2})') from None
		if self.alphaAxisRange[0]-self.approachDistance < positionerPhysics.alphaAxisRange[0]:
			raise errors.OutOfRangeError('Approach distance value is too big (conflict with alpha start)') from None
		if self.alphaAxisRange[1]+self.approachDistance > positionerPhysics.alphaAxisRange[1]:
			raise errors.OutOfRangeError('Approach distance value is too big (conflict with alpha end)') from None
		if self.betaAxisRange[0]-self.approachDistance < positionerPhysics.betaAxisRange[0]:
			raise errors.OutOfRangeError('Approach distance value is too big (conflict with beta start)') from None
		if self.betaAxisRange[1]+self.approachDistance > positionerPhysics.betaAxisRange[1]:
			raise errors.OutOfRangeError('Approach distance value is too big (conflict with beta end)') from None
		if self.cruiseCurrentAlpha > positionerPhysics.maxCurrent:
			raise errors.OutOfRangeError(f'Alpha cruise current is too big (maximum: {positionerPhysics.maxCurrent})') from None
		if self.cruiseCurrentBeta > positionerPhysics.maxCurrent:
			raise errors.OutOfRangeError(f'Beta cruise current is too big (maximum: {positionerPhysics.maxCurrent})') from None
		if self.waitCurrentAlpha > positionerPhysics.maxCurrent:
			raise errors.OutOfRangeError(f'Alpha idle current is too big (maximum: {positionerPhysics.maxCurrent})') from None
		if self.waitCurrentBeta > positionerPhysics.maxCurrent:
			raise errors.OutOfRangeError(f'Beta idle current is too big (maximum: {positionerPhysics.maxCurrent})') from None
		if self.motorRpmAlpha > positionerPhysics.maxRpmAlpha:
			raise errors.OutOfRangeError(f'Alpha motor speed is too big (maximum: {positionerPhysics.maxRpmAlpha})') from None
		if self.motorRpmBeta > positionerPhysics.maxRpmBeta:
			raise errors.OutOfRangeError(f'Beta motor speed is too big (maximum: {positionerPhysics.maxRpmBeta})') from None
		if self.numberOfStartingPoints > 2**DEFINES.MM_IMG_ID_BITS_FOR_STARTING_POINT-1:
			raise errors.OutOfRangeError(f'Number of starting points is too big (maximum: {2**DEFINES.MM_IMG_ID_BITS_FOR_STARTING_POINT-1})') from None
		if self.numberOfRepetitions > 2**DEFINES.MM_IMG_ID_BITS_FOR_REPETITION-1:
			raise errors.OutOfRangeError(f'Number of repetitions is too big (maximum: {2**DEFINES.MM_IMG_ID_BITS_FOR_REPETITION-1})') from None
		if self.numberOfStepsPerCircle > 2**DEFINES.MM_IMG_ID_BITS_FOR_STEP-1:
			raise errors.OutOfRangeError(f'Number of steps is too big (maximum: {2**DEFINES.MM_IMG_ID_BITS_FOR_STEP-1})') from None
		if self.includeTiltRun and (self.bigCentroidRatio < 1 or self.bigCentroidRatio is not int(self.bigCentroidRatio)):
			raise errors.OutOfRangeError('Big centroid ratio is invalid (minimum ratio: 1, integers only)') from None
			
class Results():
	__slots__ = (	'config',\
					'requirements',\
					'testBenchName',\
					'positionerID',\
					'slotID',\
					'sortedTargetCommand',\
					'sortedCentroidsXY',\
					'sortedCentroidsTilt',\
					'sortedHallMeasures',\
					'calibrationParameters',\
					'fittedCircles',\
					'measuredLengths',\
					'measuredAngles',\
					'measuredHysteresis',\
					'measuredRepeatability',\
					'modelError',\
					'modelCenter',\
					'modelOffsets',\
					'modelArmLengths',\
					'metrologyToScienceOffset',\
					'modelNonLinearity',\
					'modelNLDerivative',\
					'modelEccentricity',\
					'mesAlphaLength',\
					'mesBetaLength',\
					'mesRMSModelFit',\
					'mesRMSRepeatability',\
					'mesMaxHysteresis',\
					'mesMaxNL',\
					'mesMaxNLDerivative',\
					'mesRMSAlignmentError',\
					'mesMaxAlignmentError',\
					'mesMaxRoundnessError',\
					'valuesToRemove',\
					'runDone',\
					'completionTime',\
					'calcDone')

	def __init__(self):
		self.config						= classConfig.Config()
		self.requirements 				= classPositioners.PositionerRequirements()
		self.calibrationParameters 		= Parameters()

		self.testBenchName				= ''
		self.positionerID				= []
		self.slotID						= []

		self.sortedTargetCommand		= []
		self.sortedCentroidsXY 			= []
		self.sortedCentroidsTilt 		= []
		self.sortedHallMeasures 		= []

		self.fittedCircles				= []
		self.measuredLengths 			= []
		self.metrologyToScienceOffset 	= 0
		self.measuredAngles 			= []
		self.measuredHysteresis 		= []
		self.measuredRepeatability	 	= []

		self.modelError					= []
		self.modelCenter 				= []
		self.modelOffsets 				= []
		self.modelArmLengths 			= []
		self.modelNonLinearity 			= []
		self.modelNLDerivative			= []
		self.modelEccentricity 			= []

		self.mesAlphaLength 			= []
		self.mesBetaLength 				= []
		self.mesRMSModelFit 			= []
		self.mesRMSRepeatability 		= []
		self.mesMaxHysteresis 			= []
		self.mesMaxNL 					= []
		self.mesMaxNLDerivative 		= []
		self.mesRMSAlignmentError		= []
		self.mesMaxAlignmentError		= []
		self.mesMaxRoundnessError 		= []

		self.valuesToRemove				= []

		self.runDone 					= False
		self.completionTime 			= 'N/A'
		self.calcDone 					= False

	def load(self,fileName):
		try:
			#Load all the data in the file, exculding the fileInfos
			with open(os.path.join(fileName),'r') as inFile:
				variablesToLoad=json.load(inFile)
				for key in variablesToLoad.keys():
					if key in type(self).__slots__:
						if isinstance(variablesToLoad[key], list):
							if 	key == 'mesAlphaLength' or \
								key == 'mesBetaLength' or \
								key == 'mesRMSModelFit' or \
								key == 'mesRMSRepeatability' or \
								key == 'mesMaxHysteresis' or \
								key == 'mesMaxNL' or \
								key == 'mesMaxNLDerivative' or \
								key == 'mesRMSAlignmentError' or \
								key == 'mesMaxAlignmentError' or \
								key == 'mesMaxRoundnessError':
								setattr(self, key, variablesToLoad[key])
							else:
								setattr(self, key, np.array(variablesToLoad[key]))
						else:
							setattr(self, key, variablesToLoad[key])
					elif key in type(self.calibrationParameters).__slots__:
						if isinstance(variablesToLoad[key], list):
							setattr(self.calibrationParameters, key, np.array(variablesToLoad[key]))
						else:
							setattr(self.calibrationParameters, key, variablesToLoad[key])
					elif key in type(self.config).__slots__:
						if isinstance(variablesToLoad[key], list):
							setattr(self.config, key, np.array(variablesToLoad[key]))
						else:
							setattr(self.config, key, variablesToLoad[key])
					elif key in type(self.requirements).__slots__:
						if isinstance(variablesToLoad[key], list):
							setattr(self.requirements, key, np.array(variablesToLoad[key]))
						else:
							setattr(self.requirements, key, variablesToLoad[key])
					else:
						log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING,1,f'Unexpected data was encountered during the loading of the calibration results. Faulty key: {key}')
						if DEFINES.RAISE_ERROR_ON_UNEXPECTED_KEY:
							raise errors.IOError('Unexpected data was encountered during the loading of the calibration results') from None
						
		except OSError:
			raise errors.IOError('The calibration results file could not be found') from None

	def save(self,filePath,fileName):
		variablesToSave = {}
		for slots in [getattr(cls, '__slots__', []) for cls in type(self).__mro__]:
			for attr in slots:
				if isinstance(getattr(self, attr), np.ndarray): #convert the numpy arrays to lists
					variablesToSave[attr] = getattr(self, attr).tolist()
				elif attr == 'calibrationParameters':
					for subSlots in [getattr(cls, '__slots__', []) for cls in type(self.calibrationParameters).__mro__]:
						for subAttr in subSlots:
							if isinstance(getattr(self.calibrationParameters, subAttr), np.ndarray):
								variablesToSave[subAttr] = getattr(self.calibrationParameters, subAttr).tolist()
							else:
								variablesToSave[subAttr] = getattr(self.calibrationParameters, subAttr)
				elif attr == 'config':
					for subSlots in [getattr(cls, '__slots__', []) for cls in type(self.config).__mro__]:
						for subAttr in subSlots:
							if isinstance(getattr(self.config, subAttr), np.ndarray):
								variablesToSave[subAttr] = getattr(self.config, subAttr).tolist()
							else:
								variablesToSave[subAttr] = getattr(self.config, subAttr)
				elif attr == 'requirements':
					for subSlots in [getattr(cls, '__slots__', []) for cls in type(self.requirements).__mro__]:
						for subAttr in subSlots:
							if isinstance(getattr(self.requirements, subAttr), np.ndarray):
								variablesToSave[subAttr] = getattr(self.requirements, subAttr).tolist()
							else:
								variablesToSave[subAttr] = getattr(self.requirements, subAttr)
				else: 
					variablesToSave[attr] = getattr(self, attr)

		os.makedirs(filePath, exist_ok=True)
		with open(os.path.join(filePath, fileName),'w+') as outFile:
			json.dump(variablesToSave, outFile, separators = (',\n',': '))

def run(testBench, calibrationParameters, calibResults, config, processManager):
	try:
		if len(calibResults) is not testBench.nbSlots:
			raise errors.Error("Calibration result container has the wrong length") from None

		#clear any remaining result in the centroid results container
		processManager.clear_centroids_results()

		#Extract data from program parameters and do necessary conversions
		if calibrationParameters.hysteresisEnable:
			nbDirections = 2
		else:
			nbDirections = 1

		nbRepetitions = calibrationParameters.numberOfRepetitions
		nbStartingPoints = calibrationParameters.numberOfStartingPoints
		axesToTest = calibrationParameters.axesToTest
		nbAxes = len(axesToTest)
		nbSteps = calibrationParameters.numberOfStepsPerCircle
		approachDistance = calibrationParameters.approachDistance

		#Check that the commands are not exceeding the workspace
		if calibrationParameters.alphaAxisRange[0]-abs(approachDistance) < testBench.positioners[0].physics.alphaAxisRange[0]:
			calibrationParameters.alphaAxisRange[0] = testBench.positioners[0].physics.alphaAxisRange[0]+abs(approachDistance)
		if calibrationParameters.alphaAxisRange[1]+abs(approachDistance) > testBench.positioners[0].physics.alphaAxisRange[1]:
			calibrationParameters.alphaAxisRange[1] = testBench.positioners[0].physics.alphaAxisRange[1]-abs(approachDistance)
		if calibrationParameters.betaAxisRange[0]-abs(approachDistance) < testBench.positioners[0].physics.betaAxisRange[0]:
			calibrationParameters.betaAxisRange[0] = testBench.positioners[0].physics.betaAxisRange[0]+abs(approachDistance)
		if calibrationParameters.betaAxisRange[1]+abs(approachDistance) > testBench.positioners[0].physics.betaAxisRange[1]:
			calibrationParameters.betaAxisRange[1] = testBench.positioners[0].physics.betaAxisRange[1]-abs(approachDistance)


		incrementsPerDeg	= testBench.positioners[0].physics.incrementsPerRotation/DEFINES.DEGREES_PER_ROTATION
		incrementsPerRad	= testBench.positioners[0].physics.incrementsPerRotation/DEFINES.RADIANS_PER_ROTATION

		ROI = np.zeros(5)

		#Spawn calibration targets
		startingCoord 	= [	np.linspace(	calibrationParameters.alphaAxisRange[0],\
											calibrationParameters.alphaAxisRange[1],\
											nbStartingPoints,endpoint = False),\
							np.linspace(	calibrationParameters.betaAxisRange[0],\
											(calibrationParameters.betaAxisRange[1]-calibrationParameters.betaAxisRange[0])/2,\
											nbStartingPoints,endpoint = True)]

		stepCoord 		= [	np.linspace(	calibrationParameters.alphaAxisRange[0],\
											calibrationParameters.alphaAxisRange[1],\
											nbSteps,endpoint = True),\
							np.linspace(	calibrationParameters.betaAxisRange[0],\
											calibrationParameters.betaAxisRange[1],\
											nbSteps,endpoint = True)]

		#create result containers
		totalNbPoints 		= nbRepetitions*nbStartingPoints*nbAxes*nbSteps*nbDirections
		sortedTargetCommand = np.zeros((nbStartingPoints,max(axesToTest)+1,nbSteps,nbDirections,2))
		sortedHallMeasures	= np.zeros((testBench.nbSlots,nbRepetitions,nbStartingPoints,max(axesToTest)+1,nbSteps,nbDirections,2))
		sortedCentroidsXY 	= np.zeros((testBench.nbSlots,nbRepetitions,nbStartingPoints,max(axesToTest)+1,nbSteps,nbDirections,8))

		if totalNbPoints == 0:
			totalPtsDigits = 1
		else:
			totalPtsDigits = int(np.log10(totalNbPoints)+1) #get the number of digits to display

		if calibrationParameters.includeTiltRun:
			sortedCentroidsTilt = np.zeros((nbStartingPoints,max(axesToTest)+1,nbSteps,nbDirections,8))
		else:
			sortedCentroidsTilt = []
		

		#Setup the ROI if it is not dynamic
		if testBench.cameraXY.parameters.softROIrequired:
			testBench.cameraXY.setMaxROI()
			testBench.cameraXY.setExposure(testBench.slotsExposures[0])

		#start all positioners current and set speed
		testBench.set_current_all_positioners(calibrationParameters.cruiseCurrentAlpha, calibrationParameters.cruiseCurrentBeta)
		testBench.set_speed_all_positioners(calibrationParameters.motorRpmAlpha, calibrationParameters.motorRpmBeta)
		testBench.move_all_positioners_to_origin()
		
		#Start the moves
		tStart = time.time()
		currentPoint = 1
		allImgIDs = []

		for repetition in range(0,nbRepetitions):
			for startingPoint in range(0,nbStartingPoints):
				for axis in axesToTest:
					for direction in range(0,nbDirections):
						for step in range(0,nbSteps):
							t0 = time.perf_counter()
							
							if direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
								stepIndex = step
								approachMove = approachDistance
							else:
								stepIndex = nbSteps-step-1
								approachMove = -approachDistance

							#create motor commands for the step
							if axis == DEFINES.CALIB_ALPHA_INDEX:
								sortedTargetCommand[startingPoint,axis,stepIndex,direction,DEFINES.CALIB_ALPHA_INDEX] = stepCoord[DEFINES.CALIB_ALPHA_INDEX][stepIndex]
								sortedTargetCommand[startingPoint,axis,stepIndex,direction,DEFINES.CALIB_BETA_INDEX] = startingCoord[DEFINES.CALIB_BETA_INDEX][startingPoint]
								
								approachAngleAlpha = stepCoord[DEFINES.CALIB_ALPHA_INDEX][stepIndex]-approachMove
								currentAlpha = calibrationParameters.cruiseCurrentAlpha
								
								#If it is the first step of the startingPoint, also adjust the beta axis
								if stepIndex == 0 and direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
									approachAngleBeta = startingCoord[DEFINES.CALIB_BETA_INDEX][startingPoint]-approachMove
									currentBeta = calibrationParameters.cruiseCurrentBeta
								else:
									approachAngleBeta = startingCoord[DEFINES.CALIB_BETA_INDEX][startingPoint]
							else:
								sortedTargetCommand[startingPoint,axis,stepIndex,direction,DEFINES.CALIB_BETA_INDEX] = stepCoord[DEFINES.CALIB_BETA_INDEX][stepIndex]
								sortedTargetCommand[startingPoint,axis,stepIndex,direction,DEFINES.CALIB_ALPHA_INDEX] = startingCoord[DEFINES.CALIB_ALPHA_INDEX][startingPoint]
								
								approachAngleBeta = stepCoord[DEFINES.CALIB_BETA_INDEX][stepIndex]-approachMove
								currentBeta = calibrationParameters.cruiseCurrentBeta

								#If it is the first step of the startingPoint, also adjust the alpha axis
								if stepIndex == 0 and direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
									approachAngleAlpha = startingCoord[DEFINES.CALIB_ALPHA_INDEX][startingPoint]-approachMove
									currentAlpha = calibrationParameters.cruiseCurrentAlpha
								else:
									approachAngleAlpha = startingCoord[DEFINES.CALIB_ALPHA_INDEX][startingPoint]
							
							t1 = time.perf_counter()
							log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,	f'T init : {t1-t0:6.5f} s',removeMsgHeader = False)
							
							#Change current
							if not (calibrationParameters.waitCurrentAlpha == currentAlpha and calibrationParameters.waitCurrentBeta == currentBeta):
								testBench.set_current_all_positioners(currentAlpha, currentBeta)
								
							#goto the approach distance
							testBench.move_all_positioners(approachAngleAlpha, approachAngleBeta)

							#goto the target point
							testBench.move_all_positioners(sortedTargetCommand[startingPoint,axis,stepIndex,direction,DEFINES.CALIB_ALPHA_INDEX], sortedTargetCommand[startingPoint,axis,stepIndex,direction,DEFINES.CALIB_BETA_INDEX])
							
							#Change current
							if not (currentAlpha == calibrationParameters.waitCurrentAlpha and currentBeta == calibrationParameters.waitCurrentBeta):
								testBench.set_current_all_positioners(calibrationParameters.waitCurrentAlpha, calibrationParameters.waitCurrentBeta)
								
							#take the image
							alpha_angle = mm.deg2rad(sortedTargetCommand[startingPoint,axis,stepIndex,direction,DEFINES.CALIB_ALPHA_INDEX])
							beta_angle = mm.deg2rad(sortedTargetCommand[startingPoint,axis,stepIndex,direction,DEFINES.CALIB_BETA_INDEX])

							t2 = time.perf_counter()
							log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,	f'T com  : {t2-t1:6.5f} s',removeMsgHeader = True)
							
							if testBench.cameraXY.parameters.softROIrequired:
								completeImage = testBench.cameraXY.getImage()
							
							t6 = time.perf_counter()
							log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,	f'T img  : {t6-t2:6.5f} s',removeMsgHeader = True)
							
							for positioner in testBench.positioners:
								
								imageID = mm.generate_img_ID(positioner.benchSlot, repetition, startingPoint, axis, stepIndex, direction, DEFINES.MM_IMG_ID_XY_IDENTIFIER)

								if positioner.calibrated:
									# print(positioner.model.lengthBeta)
									(targetX,targetY) = mm.get_endpoint(	positioner.model.centerX,positioner.model.centerY,\
																			positioner.model.lengthAlpha,positioner.model.lengthBeta,\
																			alpha_angle+positioner.model.offsetAlpha,beta_angle+positioner.model.offsetBeta)
									(targetX,targetY) = (	int(targetX/testBench.cameraXY.parameters.scaleFactor),\
															int(targetY/testBench.cameraXY.parameters.scaleFactor))
									ROI[0] = targetX
									ROI[1] = targetY
									ROI[2] = DEFINES.PC_CAMERA_XY_CALIB_CROP
									ROI[3] = DEFINES.PC_CAMERA_XY_CALIB_CROP
									ROI[4] = (positioner.model.lengthAlpha+positioner.model.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/testBench.cameraXY.parameters.scaleFactor
									
									if testBench.cameraXY.parameters.softROIrequired:
										#Do a software crop of the approximated model area
										# print(f'\tComputing image {i:>2}/{testBench.nbSlots:2}')
										(image, offsetX, offsetY) = mm.cropImage(completeImage,ROI,testBench.cameraXY.parameters.maxX,testBench.cameraXY.parameters.maxY)
										validityCenter = (positioner.model.centerX/testBench.cameraXY.parameters.scaleFactor,positioner.model.centerY/testBench.cameraXY.parameters.scaleFactor)
										validityRadius = (positioner.model.lengthAlpha+positioner.model.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/testBench.cameraXY.parameters.scaleFactor
										
										# t100 = time.perf_counter()
										processManager.centroidQueuePut((image, offsetX, offsetY, imageID, validityCenter, validityRadius), block = True)
										# print(f'{time.perf_counter()-t100:5.4f}')
										# (image,addedOffsetX,addedOffsetY) = mm.computeValidSoftROI(image, testBench.cameraXY.parameters.maxX, testBench.cameraXY.parameters.maxY, validityCenter, validityRadius)
										# offsetX += addedOffsetX
										# offsetY += addedOffsetY
										# testBench.cameraXY.parameters.ROIoffsetX = offsetX
										# testBench.cameraXY.parameters.ROIoffsetY = offsetY
										# result = cc.compute_centroid(image,testBench.cameraXY.parameters,imageID)
										# processManager.resultList.append(result)

										allImgIDs.append(imageID)
									else:
										#Do a hardware crop of the approximated model area and compute the centroid
										# print(f'\tTaking image {i:>2}/{testBench.nbSlots:2}')
										testBench.cameraXY.setROI(ROI)
										testBench.cameraXY.setExposure(testBench.slotsExposures[positioner.benchSlot])
										testBench.cameraXY.getImage(processManager.centroidQueue,imageID)
										
										allImgIDs.append(imageID)

								elif testBench.cameraXY.parameters.softROIrequired:
									# print(f'\tComputing image {i:>2}/{testBench.nbSlots:2}')
									#Send whole image to queue and ask for soft ROI
									validityCenter = (positioner.model.centerX/testBench.cameraXY.parameters.scaleFactor,positioner.model.centerY/testBench.cameraXY.parameters.scaleFactor)
									validityRadius = (positioner.model.lengthAlpha+positioner.model.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/testBench.cameraXY.parameters.scaleFactor
									
									# t100 = time.perf_counter()
									processManager.centroidQueuePut((completeImage, 0, 0, imageID, validityCenter, validityRadius), block = True)
									# print(f'{time.perf_counter()-t100:5.4f}')
									# (image,offsetX,offsetY) = mm.computeValidSoftROI(completeImage, testBench.cameraXY.parameters.maxX, testBench.cameraXY.parameters.maxY, validityCenter, validityRadius)
									# testBench.cameraXY.parameters.ROIoffsetX = offsetX
									# testBench.cameraXY.parameters.ROIoffsetY = offsetY
									# result = cc.compute_centroid(image,testBench.cameraXY.parameters,imageID)
									# processManager.resultList.append(result)

									allImgIDs.append(imageID)
								else:
									#Do a hardware crop of the positioner whole workspace and compute the centroid
									ROI[0] = positioner.model.centerX/testBench.cameraXY.parameters.scaleFactor
									ROI[1] = positioner.model.centerY/testBench.cameraXY.parameters.scaleFactor
									ROI[2] = 2*(positioner.model.lengthAlpha+positioner.model.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/testBench.cameraXY.parameters.scaleFactor
									ROI[3] = 2*(positioner.model.lengthAlpha+positioner.model.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/testBench.cameraXY.parameters.scaleFactor
									ROI[4] = (positioner.model.lengthAlpha+positioner.model.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/testBench.cameraXY.parameters.scaleFactor

									testBench.cameraXY.setROI(ROI)
									testBench.cameraXY.getImage(processManager.centroidQueue,imageID)

									allImgIDs.append(imageID)

								if calibrationParameters.includeTiltRun and ((currentPoint-1)%calibrationParameters.bigCentroidRatio is 0):
									imageID = mm.generate_img_ID(positioner.benchSlot, repetition, startingPoint, axis, stepIndex, direction, DEFINES.MM_IMG_ID_TILT_IDENTIFIER)
									testBench.cameraTilt.getImage(processManager.centroidQueue,imageID)
									allImgIDs.append(imageID)
									
							t3 = time.perf_counter()
							log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,	f'T proc : {t3-t6:6.5f} s',removeMsgHeader = True)
							
							if calibrationParameters.storeHallPositions:
								for positioner in testBench.positioners:
									tempVal = positioner.get_hall_position(testBench.canUSB)
									sortedHallMeasures[positioner.benchSlot,repetition,startingPoint,axis,stepIndex,direction,:] = tempVal
							
							t4 = time.perf_counter()
							
							log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,	f'T hall : {t4-t3:6.5f} s',removeMsgHeader = True)
							log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,	f'T tot  : {t4-t0:6.5f} s',removeMsgHeader = True)

							#print ETA
							completion = currentPoint/totalNbPoints
							(tRemaining, days, hours, minutes, seconds) = mm.get_ETA(tStart,completion)
							completion *= 100
							strETA = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(time.time()+tRemaining))
							log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'ETA: {strETA} (point {currentPoint:>{totalPtsDigits}}/{totalNbPoints:>{totalPtsDigits}} ({completion:6.2f}%), {days:02d}d {hours:02d}h{minutes:02d}m{seconds:04.1f}s remaining)',overwritable = True)
							
							currentPoint += 1

		#Change current
		if not (calibrationParameters.cruiseCurrentAlpha == calibrationParameters.waitCurrentAlpha and calibrationParameters.cruiseCurrentBeta == calibrationParameters.waitCurrentBeta):
			testBench.set_current_all_positioners(calibrationParameters.cruiseCurrentAlpha, calibrationParameters.cruiseCurrentBeta)

		#Move back to the origin and shut current down
		testBench.move_all_positioners_to_origin()
		testBench.stop_all_positioners()
		
		#get the calibration data from processManager
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Waiting for the calculations to finish.')
		previousLength = 0
		poll = 0
		totalNbCentroids = testBench.nbSlots*totalNbPoints
		while poll < int(DEFINES.PROC_MAX_RESULTS_POLLS):
			lenCentroids = processManager.get_centroid_results_length()
			centroids = processManager.get_centroids_result(end = lenCentroids)

			if lenCentroids >= totalNbCentroids:
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG,0,'Done')
				break
			elif lenCentroids != previousLength:
				previousLength = copy.deepcopy(lenCentroids)
				poll = 0 # restart watchdog if a new result was detected
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Current state: {previousLength}/{totalNbCentroids} ({totalNbCentroids-previousLength} results missing)', overwritable = True)

			time.sleep(DEFINES.PROC_RESULTS_POLL_PERIOD)

		if not len(centroids) >= totalNbCentroids:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING,0,f'Calculation timed out.')
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING,0,f'Still lacking {totalNbCentroids-previousLength} results')
			missingResults = list(set(centroids[:][7])^set(allImgIDs))
			for imgId in missingResults:
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,1,f'Missing image ID {imgId:064}')
			# raise errors.Error("Missing calibration results")

		processManager.clear_centroids_results()

		#sort the results
		for i in range(0,len(centroids)):
			image_ID = np.int64(centroids[i][7])
			(benchSlot, repetition, startingPoint, axis, step, direction, centroidType) = mm.get_img_ID(image_ID)

			if centroidType == DEFINES.MM_IMG_ID_XY_IDENTIFIER:
				sortedCentroidsXY[benchSlot, repetition, startingPoint, axis, step, direction] = centroids[i]
			elif centroidType == DEFINES.MM_IMG_ID_TILT_IDENTIFIER:
				sortedCentroidsTilt[benchSlot, repetition, startingPoint, axis, step, direction] = centroids[i]

		# store the results
		for slot in range(0, testBench.nbSlots):
			calibResults[slot].sortedTargetCommand 		= mm.deg2rad(sortedTargetCommand)
			calibResults[slot].sortedCentroidsXY 		= sortedCentroidsXY[slot]
			calibResults[slot].sortedHallMeasures 		= sortedHallMeasures[slot]
			calibResults[slot].testBenchName 			= testBench.benchName
			calibResults[slot].positionerID 			= int(testBench.positioners[slot].ID)
			calibResults[slot].slotID 					= int(testBench.slotIDs[slot])
			if calibrationParameters.includeTiltRun:
				calibResults[slot].sortedCentroidsTilt 	= sortedCentroidsTilt[slot]
			else:
				calibResults[slot].sortedCentroidsTilt 	= []
			calibResults[slot].metrologyToScienceOffset = testBench.positioners[slot].physics.metrologyToScience
			calibResults[slot].calibrationParameters 	= calibrationParameters
			calibResults[slot].config 					= config
			calibResults[slot].requirements 			= testBench.positioners[slot].requirements
			calibResults[slot].completionTime 			= time.strftime("%Y-%m-%d-%Hh%Mm%Ss", time.localtime(time.time()))
			calibResults[slot].runDone 					= True

	except errors.Error as e:
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
		raise errors.CalibrationError("Calibration run failed")
	
def compute_model(calibResults, testBench = None):

	nbSlots = len(calibResults)
	
	for slot in range(0,nbSlots):
		if (not calibResults[slot].runDone) or calibResults[slot].calcDone:
			continue
		axesToTest 			= calibResults[slot].calibrationParameters.axesToTest
		sortedCentroidsXY 	= calibResults[slot].sortedCentroidsXY
		commandedAngle 		= calibResults[slot].sortedTargetCommand
		nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData = sortedCentroidsXY.shape

		valuesToRemove 			= np.isnan(sortedCentroidsXY[:,:,:,:,:,0])

		fittedCircles 			= np.full((nbStartingPoints,nbAxes,3),np.nan)

		measuredLengths 		= np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections),np.nan)
		degeneratedMeasuredLengths = np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections),np.nan)
		measuredAngles 			= np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,2),np.nan)
		measuredHysteresis 		= np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps),np.nan)
		measuredRepeatability 	= np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,5),np.nan) #Total, X, Y, Across, Along
		
		modelOffsets 			= np.full((nbAxes),np.nan)
		modelArmLengths 		= np.full((nbAxes),np.nan)
		modelCenter				= np.full((2),np.nan)
		modelNonLinearity 		= np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections),np.nan)
		modelNLDerivative		= np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps-1,nbDirections),np.nan)
		modelEccentricity		= np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections),np.nan)
		modelError				= np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,5),np.nan) #Total, Xerr, Yerr, AcrossErr, AlongErr

		tempOffset				= np.full((nbStartingPoints,nbAxes),np.nan)
		degeneratedNonLinearity = np.full((nbStartingPoints,nbDirections),np.nan)

		# Fit the circles to the data
		strSlot = slot+1
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,1,f'Calculating model fit of positioner #{calibResults[slot].positionerID} (Slot #{calibResults[slot].slotID}, {strSlot}/{nbSlots})')
		for startingPoint in range(0,nbStartingPoints):
			for axis in axesToTest:
				#remove the outliers
				for i in range(0,DEFINES.CALIB_MAX_ITER_FOR_OUTLIERS_DETECTION):
					xData = []
					yData = []
					#input the data in a particular order
					for step in range(0,nbSteps):
						for direction in range(0,nbDirections):
						# direction = DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER #fit model only on the couterclockwize
							for repetition in range(0,nbRepetitions):
								if not valuesToRemove[repetition,startingPoint,axis,step,direction]:
									xData.append(sortedCentroidsXY[repetition,startingPoint,axis,step,direction,0])
									yData.append(sortedCentroidsXY[repetition,startingPoint,axis,step,direction,1])
					xData = np.asarray(xData)
					yData = np.asarray(yData)
					if len(xData) > 2:
						#iterate the center to remove the outliers
						distanceToCircle = np.zeros((nbSteps, nbDirections, nbRepetitions))
						approximatedCircle = mm.fit_circle(xData, yData)
						for step in range(0,nbSteps):
							for direction in range(0,nbDirections):
								for repetition in range(0,nbRepetitions):
									x = sortedCentroidsXY[repetition,startingPoint,axis,step,direction,0]
									y = sortedCentroidsXY[repetition,startingPoint,axis,step,direction,1]
									distanceToCircle[step, direction, repetition] = np.sqrt((approximatedCircle[0]-x)**2 + (approximatedCircle[1]-y)**2)
						
						zScore = abs(stats.zscore(distanceToCircle))

						if np.nanmax(zScore) <= DEFINES.CALIB_CALC_MIN_ZSCORE_OUTLIER or np.nanmax(distanceToCircle) <= DEFINES.CALIB_CALC_MIN_ERROR_OUTLIER/1000:
							break

						for step in range(0,nbSteps):
							for direction in range(0,nbDirections):
								for repetition in range(0,nbRepetitions):
									valuesToRemove[repetition,startingPoint,axis,step,direction] = valuesToRemove[repetition,startingPoint,axis,step,direction] or ((zScore[step,direction,repetition] > DEFINES.CALIB_CALC_MIN_ZSCORE_OUTLIER) and distanceToCircle[step,direction,repetition] > DEFINES.CALIB_CALC_MIN_ERROR_OUTLIER/1000)
									if valuesToRemove[repetition,startingPoint,axis,step,direction]:
										# print(f'R{repetition:1}D{direction:1}S{step:03}: {distanceToCircle[step, direction, repetition]:05.3f} ({zScore[step,direction,repetition]:6.3f})')
										sortedCentroidsXY[repetition,startingPoint,axis,step,direction,:] = (np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,sortedCentroidsXY[repetition,startingPoint,axis,step,direction,7])
					else:
						raise errors.Error("Not enough points in measured data to fit circle")

				direction = DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER #fit model only on the couterclockwize
				xData = []
				yData = []
				#input the data in a particular order
				for step in range(0,nbSteps):
					# for direction in range(0,nbDirections):
					for repetition in range(0,nbRepetitions):
						if not valuesToRemove[repetition,startingPoint,axis,step,direction]:
							xData.append(sortedCentroidsXY[repetition,startingPoint,axis,step,direction,0])
							yData.append(sortedCentroidsXY[repetition,startingPoint,axis,step,direction,1])
				xData = np.asarray(xData)
				yData = np.asarray(yData)
				if len(xData) > 2:
					fittedCircles[startingPoint,axis] = mm.fit_circle(xData,yData)
				else:
					raise errors.Error("Not enough points in measured data to fit circle")

		# If beta was the only axis tested, fit the alpha circle on the centers of the beta axis' fitting circles
		if DEFINES.PARAM_AXIS_BETA in axesToTest and not DEFINES.PARAM_AXIS_ALPHA in axesToTest:				
			# Fit the circles to the data
			xData = np.ravel(fittedCircles[:,DEFINES.PARAM_AXIS_BETA,0])
			yData = np.ravel(fittedCircles[:,DEFINES.PARAM_AXIS_BETA,1])
			xData = xData[~np.isnan(xData)]
			yData = yData[~np.isnan(yData)]

			if len(xData) > 2:
					fittedCircles[startingPoint,axis] = mm.fit_circle(xData,yData)
			else:
				raise errors.Error("Not enough points in measured data to fit circle")

		#Compute the overall positioner center
		modelCenter[0] = np.mean(np.ravel(fittedCircles[:,DEFINES.PARAM_AXIS_ALPHA,0]))
		modelCenter[1] = np.mean(np.ravel(fittedCircles[:,DEFINES.PARAM_AXIS_ALPHA,1]))

		# Compute arm angles and arm lengths at all measured points
		for axis in axesToTest:
			for startingPoint in range(0,nbStartingPoints):
				centerX = fittedCircles[startingPoint,axis,0]
				centerY = fittedCircles[startingPoint,axis,1]

				for direction in range(0,nbDirections):
					for step in range(0,nbSteps):
						for repetition in range(0,nbRepetitions):
							if not valuesToRemove[repetition,startingPoint,axis,step,direction]:
								measureX = sortedCentroidsXY[repetition,startingPoint,axis,step,direction,0]
								measureY = sortedCentroidsXY[repetition,startingPoint,axis,step,direction,1]

								measuredAngles[repetition,startingPoint,axis,step,direction,0] = np.mod(np.arctan2(measureX-centerX,measureY-centerY),2*np.pi)
								
								#Remove alpha angle from beta measures
								if axis == DEFINES.PARAM_AXIS_BETA and DEFINES.PARAM_AXIS_ALPHA in axesToTest:
									measuredAngles[repetition,startingPoint,axis,step,direction,0] -= measuredAngles[repetition,startingPoint,DEFINES.PARAM_AXIS_ALPHA,step,direction,1]
								
								#add measurement of the angle to the other axis' center
								measuredLengths[repetition,startingPoint,axis,step,direction] = mm.dist((centerX,centerY),(measureX,measureY))
								
								if axis == DEFINES.PARAM_AXIS_BETA and DEFINES.PARAM_AXIS_ALPHA in axesToTest:
									measureX = fittedCircles[startingPoint,axis,0]
									measureY = fittedCircles[startingPoint,axis,1]
									measuredAngles[repetition,startingPoint,axis,step,direction,1] = np.mod(np.arctan2(measureX-centerX,measureY-centerY),2*np.pi)

								if axis == DEFINES.PARAM_AXIS_ALPHA and DEFINES.PARAM_AXIS_BETA in axesToTest:
									measureX = fittedCircles[startingPoint,DEFINES.PARAM_AXIS_BETA,0]
									measureY = fittedCircles[startingPoint,DEFINES.PARAM_AXIS_BETA,1]
									measuredAngles[repetition,startingPoint,axis,step,direction,1] = np.mod(np.arctan2(measureX-centerX,measureY-centerY),2*np.pi)
									degeneratedMeasuredLengths[repetition,startingPoint,axis,step,direction] = mm.dist((centerX,centerY),(measureX,measureY))

								#store temporary non-linearity
								modelNonLinearity[repetition,startingPoint,axis,step,direction] = np.mod(measuredAngles[repetition,startingPoint,axis,step,direction,0]-commandedAngle[startingPoint,axis,step,direction,axis]+np.pi,2*np.pi)-np.pi
								
								#compute hysteresis
								if direction == DEFINES.MM_IMG_ID_CLOCKWIZE_DIR_IDENTIFIER:
									measuredHysteresis[repetition,startingPoint,axis,step] = np.mod(measuredAngles[repetition,startingPoint,axis,step,DEFINES.MM_IMG_ID_CLOCKWIZE_DIR_IDENTIFIER,0]-measuredAngles[repetition,startingPoint,axis,step,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,0]+np.pi,2*np.pi)-np.pi

					#Degenerated is the non-linearity using the Center-to-center parameters
					if axis == DEFINES.PARAM_AXIS_ALPHA and DEFINES.PARAM_AXIS_BETA in axesToTest:
						degeneratedNonLinearity[startingPoint,direction] = np.nanmean(np.ravel(np.mod(measuredAngles[:,startingPoint,axis,0,direction,1]-commandedAngle[startingPoint,DEFINES.PARAM_AXIS_BETA,0,direction,DEFINES.PARAM_AXIS_ALPHA]+np.pi,2*np.pi)-np.pi))

				#Get all the offsets in the same 180°. For example, measure of 179° and -179° should give 180° offset, not 0°.
				referenceOffset = modelNonLinearity[0,startingPoint,axis,0,0]
				for direction in range(0,nbDirections):
					for repetition in range(0,nbRepetitions):
						for step in range(0,nbSteps):
							while referenceOffset - modelNonLinearity[repetition,startingPoint,axis,step,direction] < -np.pi:
								modelNonLinearity[repetition,startingPoint,axis,step,direction] -= 2*np.pi
							while referenceOffset - modelNonLinearity[repetition,startingPoint,axis,step,direction] > np.pi:
								modelNonLinearity[repetition,startingPoint,axis,step,direction] += 2*np.pi

				#get offset from the temporary non-linearity and remove it
				tempOffset[startingPoint,axis] = np.nanmean(np.ravel(modelNonLinearity[:,startingPoint,axis,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER]))
				measuredAngles[:,startingPoint,axis,:,:,0] -= tempOffset[startingPoint,axis]

				for direction in range(0,nbDirections):
					for step in range(0,nbSteps):
						for repetition in range(0,nbRepetitions):
							#get the measured angles in the same full rotation as the command (i.e. a -5° measure should be mapped to the -5° command, and not remain 355°)
							while commandedAngle[startingPoint,axis,step,direction,axis]-measuredAngles[repetition,startingPoint,axis,step,direction,0] < -np.pi:
								measuredAngles[repetition,startingPoint,axis,step,direction,0] -= 2*np.pi
							while commandedAngle[startingPoint,axis,step,direction,axis]-measuredAngles[repetition,startingPoint,axis,step,direction,0] > np.pi:
								measuredAngles[repetition,startingPoint,axis,step,direction,0] += 2*np.pi
							
							modelNonLinearity[repetition,startingPoint,axis,step,direction] = np.mod(measuredAngles[repetition,startingPoint,axis,step,direction,0]-commandedAngle[startingPoint,axis,step,direction,axis]+np.pi,2*np.pi)-np.pi

				#compute non-linearity derivative
				for direction in range(0,nbDirections):
					for step in range(0,nbSteps-1):
						for repetition in range(0,nbRepetitions):
							if not valuesToRemove[repetition,startingPoint,axis,step,direction]:
								angleInc = np.abs(commandedAngle[startingPoint,axis,step,direction,axis]-commandedAngle[startingPoint,axis,step+1,direction,axis])
								nonLinInc = np.abs(modelNonLinearity[repetition,startingPoint,axis,step,direction]-modelNonLinearity[repetition,startingPoint,axis,step+1,direction])
								modelNLDerivative[repetition,startingPoint,axis,step,direction] = nonLinInc/angleInc

			#store the model arm length
			if axis == DEFINES.PARAM_AXIS_ALPHA and DEFINES.PARAM_AXIS_BETA in axesToTest:
				modelArmLengths[axis] = np.nanmean(np.ravel(degeneratedMeasuredLengths[:,:,axis,:,:]))
			else:
				modelArmLengths[axis] = np.nanmean(np.ravel(measuredLengths[:,:,axis,:,:]))
			
			#store the offset for the model
			if axis == DEFINES.PARAM_AXIS_ALPHA:
				if DEFINES.PARAM_AXIS_BETA in axesToTest:
					modelOffsets[axis] = np.nanmean(np.ravel(degeneratedNonLinearity[:,:]))
				else:
					modelOffsets[axis] = 0 #Cannot be determined
			if axis == DEFINES.PARAM_AXIS_BETA:
				modelOffsets[axis] = np.nanmean(tempOffset[:,axis])
		
		metrologyToScienceOffset = calibResults[slot].metrologyToScienceOffset

		#modelError #Total, Xerr, Yerr, AcrossErr, AlongErr
		direction = DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER

		meanAlphaMeasures = np.full((nbSteps),np.nan)
		meanBetaMeasures = np.full((nbSteps),np.nan)
		meanAlphaCommand = np.full((nbSteps),np.nan)
		meanBetaCommand = np.full((nbSteps),np.nan)

		for step in range(0,nbSteps):
			meanAlphaMeasures[step] = np.nanmean(np.ravel(measuredAngles[:,:,DEFINES.PARAM_AXIS_ALPHA,step,direction,0]))
			meanBetaMeasures[step] = np.nanmean(np.ravel(measuredAngles[:,:,DEFINES.PARAM_AXIS_BETA,step,direction,0]))
			meanAlphaCommand[step] = np.nanmean(np.ravel(commandedAngle[:,DEFINES.PARAM_AXIS_ALPHA,step,direction,DEFINES.PARAM_AXIS_ALPHA]))
			meanBetaCommand[step] = np.nanmean(np.ravel(commandedAngle[:,DEFINES.PARAM_AXIS_BETA,step,direction,DEFINES.PARAM_AXIS_BETA]))
		
		if len(meanAlphaCommand) < 2 or len(meanBetaCommand) < 2 or len(meanAlphaMeasures) < 2 or len(meanBetaMeasures) < 2:
			raise errors.Error("There must be at least 2 valid points to do an iterpolation")

		#construct the alpha and beta approximators
		alphaIterpolator = interpolate.interp1d(meanAlphaCommand, meanAlphaMeasures, kind='linear', fill_value='extrapolate') #gives the real value out of the command
		betaIterpolator = interpolate.interp1d(meanBetaCommand, meanBetaMeasures, kind='linear', fill_value='extrapolate')

		offsetAlpha_deg = 180*modelOffsets[DEFINES.PARAM_AXIS_ALPHA]/np.pi
		offsetBeta_deg = 180*modelOffsets[DEFINES.PARAM_AXIS_BETA]/np.pi

		params = (	modelCenter[0],modelCenter[1],\
					modelArmLengths[DEFINES.PARAM_AXIS_ALPHA],modelArmLengths[DEFINES.PARAM_AXIS_BETA],\
					modelOffsets[DEFINES.PARAM_AXIS_ALPHA],modelOffsets[DEFINES.PARAM_AXIS_BETA])

		modelFit = mm.rms_model_error(	params,\
										commandedAngle[:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,DEFINES.PARAM_AXIS_ALPHA],commandedAngle[:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,DEFINES.PARAM_AXIS_BETA],\
										alphaIterpolator,betaIterpolator,\
										sortedCentroidsXY[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,0],sortedCentroidsXY[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,1])

		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,1,f'Model fit before optimization: {modelFit:8.3f} [um]')

		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,2,f'Length alpha: {modelArmLengths[DEFINES.PARAM_AXIS_ALPHA]:5.2f} [mm]',removeMsgHeader = False)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,2,f'Length beta : {modelArmLengths[DEFINES.PARAM_AXIS_BETA]+metrologyToScienceOffset:5.2f} [mm]',removeMsgHeader = True)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,2,f'Offset alpha: {offsetAlpha_deg:5.2f} [°]',removeMsgHeader = True)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,2,f'Offset beta : {offsetBeta_deg:5.2f} [°]',removeMsgHeader = True)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,2,f'Center X    : {modelCenter[0]:5.2f} [mm]',removeMsgHeader = True)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,2,f'Center Y    : {modelCenter[1]:5.2f} [mm]',removeMsgHeader = True)

		#optimize the model
		params = mm.optimize_model(	modelCenter[0],modelCenter[1],\
									modelArmLengths[DEFINES.PARAM_AXIS_ALPHA],modelArmLengths[DEFINES.PARAM_AXIS_BETA],\
									modelOffsets[DEFINES.PARAM_AXIS_ALPHA],modelOffsets[DEFINES.PARAM_AXIS_BETA],\
									commandedAngle[:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,DEFINES.PARAM_AXIS_ALPHA],commandedAngle[:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,DEFINES.PARAM_AXIS_BETA],\
									measuredAngles[:,:,DEFINES.PARAM_AXIS_ALPHA,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,0],measuredAngles[:,:,DEFINES.PARAM_AXIS_BETA,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,0],\
									sortedCentroidsXY[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,0],sortedCentroidsXY[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,1])


		# Compute eccentricity parameters
		for axis in axesToTest:
			for startingPoint in range(0,nbStartingPoints):
				modelEccentricity[:,startingPoint,axis,:,:] = np.subtract(measuredLengths[:,startingPoint,axis,:,:],fittedCircles[startingPoint,axis,2])


		(modelCenter[0],modelCenter[1],\
		modelArmLengths[DEFINES.PARAM_AXIS_ALPHA],modelArmLengths[DEFINES.PARAM_AXIS_BETA],\
		modelOffsets[DEFINES.PARAM_AXIS_ALPHA],modelOffsets[DEFINES.PARAM_AXIS_BETA])			= params

		#Compute Model error
		#modelError #Total, Xerr, Yerr, AcrossErr, AlongErr
		direction = DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER

		meanAlphaMeasures = np.full((nbSteps),np.nan)
		meanBetaMeasures = np.full((nbSteps),np.nan)
		meanAlphaCommand = np.full((nbSteps),np.nan)
		meanBetaCommand = np.full((nbSteps),np.nan)

		for step in range(0,nbSteps):
			meanAlphaMeasures[step] = np.nanmean(np.ravel(measuredAngles[:,:,DEFINES.PARAM_AXIS_ALPHA,step,direction,0]))
			meanBetaMeasures[step] = np.nanmean(np.ravel(measuredAngles[:,:,DEFINES.PARAM_AXIS_BETA,step,direction,0]))
			meanAlphaCommand[step] = np.nanmean(np.ravel(commandedAngle[:,DEFINES.PARAM_AXIS_ALPHA,step,direction,DEFINES.PARAM_AXIS_ALPHA]))
			meanBetaCommand[step] = np.nanmean(np.ravel(commandedAngle[:,DEFINES.PARAM_AXIS_BETA,step,direction,DEFINES.PARAM_AXIS_BETA]))
		
		meanAlphaCommand = meanAlphaCommand[~np.isnan(meanAlphaMeasures)]
		meanBetaCommand = meanBetaCommand[~np.isnan(meanBetaMeasures)]
		meanAlphaMeasures = meanAlphaMeasures[~np.isnan(meanAlphaMeasures)]
		meanBetaMeasures = meanBetaMeasures[~np.isnan(meanBetaMeasures)]

		#construct the alpha and beta approximators
		alphaIterpolator = interpolate.interp1d(meanAlphaCommand, meanAlphaMeasures, kind='linear', fill_value='extrapolate') #gives the real value out of the command
		betaIterpolator = interpolate.interp1d(meanBetaCommand, meanBetaMeasures, kind='linear', fill_value='extrapolate')

		modelFit = mm.rms_model_error(	params,\
										commandedAngle[:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,DEFINES.PARAM_AXIS_ALPHA],commandedAngle[:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,DEFINES.PARAM_AXIS_BETA],\
										alphaIterpolator,betaIterpolator,\
										sortedCentroidsXY[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,0],sortedCentroidsXY[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,1])
		
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,1,f'Model fit after optimization: {modelFit:8.3f} [um]')

		offsetAlpha_deg = 180*modelOffsets[DEFINES.PARAM_AXIS_ALPHA]/np.pi
		offsetBeta_deg = 180*modelOffsets[DEFINES.PARAM_AXIS_BETA]/np.pi

		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,2,f'Length alpha: {modelArmLengths[DEFINES.PARAM_AXIS_ALPHA]:5.2f} [mm]',removeMsgHeader = False)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,2,f'Length beta : {modelArmLengths[DEFINES.PARAM_AXIS_BETA]+metrologyToScienceOffset:5.2f} [mm]',removeMsgHeader = True)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,2,f'Offset alpha: {offsetAlpha_deg:5.2f} [°]',removeMsgHeader = True)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,2,f'Offset beta : {offsetBeta_deg:5.2f} [°]',removeMsgHeader = True)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,2,f'Center X    : {modelCenter[0]:5.2f} [mm]',removeMsgHeader = True)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,2,f'Center Y    : {modelCenter[1]:5.2f} [mm]',removeMsgHeader = True)

		#Total, Xerr, Yerr
		(	modelError[:,:,:,:,direction,0],\
			modelError[:,:,:,:,direction,1],\
			modelError[:,:,:,:,direction,2]) 	= mm.model_error(	params,\
																	commandedAngle[:,:,:,direction,DEFINES.PARAM_AXIS_ALPHA],commandedAngle[:,:,:,direction,DEFINES.PARAM_AXIS_BETA],\
																	alphaIterpolator,betaIterpolator,\
																	sortedCentroidsXY[:,:,:,:,direction,0],sortedCentroidsXY[:,:,:,:,direction,1],\
																	True)
		
		#AcrossErr, AlongErr
		for axis in axesToTest:
			for startingPoint in range(0,nbStartingPoints):
				centerX = fittedCircles[startingPoint,axis][0]
				centerY = fittedCircles[startingPoint,axis][1]
				for step in range(0,nbSteps):
					for repetition in range(0,nbRepetitions):
						measureX = sortedCentroidsXY[repetition,startingPoint,axis,step,direction,0]
						measureY = sortedCentroidsXY[repetition,startingPoint,axis,step,direction,1]
						modelX = measureX + modelError[repetition,startingPoint,axis,step,direction,1]
						modelY = measureY + modelError[repetition,startingPoint,axis,step,direction,2]

						#Project XY error on a radius-angle error (along, across)
						angle1 = np.mod(np.arctan2(measureY-modelY,measureX-modelX),2*np.pi) #Angle between Ox, centroid and fittingCenter
						angle2 = np.mod(np.arctan2(measureY-centerY,measureX-centerX),2*np.pi) #Angle between Ox, centroid and model
						angleDiff = angle1-angle2 #Angle between model, centroid and fittingCenter

						if angleDiff > np.pi:
							angleDiff-= 2*np.pi
						elif angleDiff < -np.pi:
							angleDiff+= 2*np.pi

						modelError[repetition,startingPoint,axis,step,direction,3] = modelError[repetition,startingPoint,axis,step,direction,0]*np.sin(angleDiff)
						modelError[repetition,startingPoint,axis,step,direction,4] = modelError[repetition,startingPoint,axis,step,direction,0]*np.cos(angleDiff)

		#Compute repeatability
		#measuredRepeatability #Total, X, Y, Across, Along
		if nbRepetitions > 1:
			for axis in axesToTest:
				for startingPoint in range(0,nbStartingPoints):
					centerX = fittedCircles[startingPoint,axis][0]
					centerY = fittedCircles[startingPoint,axis][1]
					for direction in range(0,nbDirections):
						for step in range(0,nbSteps):
							meanPointX = np.nanmean(sortedCentroidsXY[:,startingPoint,axis,step,direction,0])
							meanPointY = np.nanmean(sortedCentroidsXY[:,startingPoint,axis,step,direction,1])
							for repetition in range(0,nbRepetitions):
								measureX = sortedCentroidsXY[repetition,startingPoint,axis,step,direction,0]
								measureY = sortedCentroidsXY[repetition,startingPoint,axis,step,direction,1]
								repeatabilityX = meanPointX-measureX
								repeatabilityY = meanPointY-measureY
								repeatabilityTotal = np.sqrt(repeatabilityX**2+repeatabilityY**2)

								#Project XY error on a radius-angle error (along, across)
								angle1 = np.mod(np.arctan2(measureY-repeatabilityY,measureX-repeatabilityX),2*np.pi) #Angle between Ox, centroid and fittingCenter
								angle2 = np.mod(np.arctan2(measureY-centerY,measureX-centerX),2*np.pi) #Angle between Ox, centroid and model
								angleDiff = angle1-angle2 #Angle between model, centroid and fittingCenter

								if angleDiff > np.pi:
									angleDiff-= 2*np.pi
								elif angleDiff < -np.pi:
									angleDiff+= 2*np.pi

								measuredRepeatability[repetition,startingPoint,axis,step,direction,0] = repeatabilityTotal
								measuredRepeatability[repetition,startingPoint,axis,step,direction,1] = repeatabilityX
								measuredRepeatability[repetition,startingPoint,axis,step,direction,2] = repeatabilityY
								measuredRepeatability[repetition,startingPoint,axis,step,direction,3] = repeatabilityTotal*np.sin(angleDiff)
								measuredRepeatability[repetition,startingPoint,axis,step,direction,4] = repeatabilityTotal*np.cos(angleDiff)

		mesAlphaLength = modelArmLengths[DEFINES.PARAM_AXIS_ALPHA]
		mesBetaLength = modelArmLengths[DEFINES.PARAM_AXIS_BETA]+metrologyToScienceOffset
		mesRMSModelFit = 1000*mm.nanrms(np.ravel(modelError[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,0]))
		mesRMSRepeatability = 1000*mm.nanrms(np.ravel(measuredRepeatability[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER,0]))
		mesMaxHysteresis = 180*np.nanmax(np.abs(np.ravel(measuredHysteresis[:,:,:,:])))/np.pi
		mesMaxNL = 180*np.nanmax(np.abs(np.ravel(modelNonLinearity[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER])))/np.pi
		mesMaxNLDerivative = np.nanmax(np.ravel(modelNLDerivative[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER]))
		mesRMSAlignmentError = np.nan
		mesMaxAlignmentError = np.nan
		mesMaxRoundnessError = 1000*np.nanmax(np.abs(np.ravel(modelEccentricity[:,:,:,:,DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER])))

		# Store the results
		calibResults[slot].fittedCircles 			= fittedCircles
		calibResults[slot].measuredAngles 			= measuredAngles
		calibResults[slot].measuredLengths 			= measuredLengths
		calibResults[slot].measuredHysteresis 		= measuredHysteresis
		calibResults[slot].measuredRepeatability 	= measuredRepeatability
		calibResults[slot].modelError 				= modelError
		calibResults[slot].modelCenter				= modelCenter
		calibResults[slot].modelOffsets				= modelOffsets
		calibResults[slot].modelArmLengths			= modelArmLengths
		calibResults[slot].modelNonLinearity		= modelNonLinearity
		calibResults[slot].modelNLDerivative		= modelNLDerivative
		calibResults[slot].modelEccentricity 		= modelEccentricity
		calibResults[slot].valuesToRemove			= valuesToRemove
		calibResults[slot].metrologyToScienceOffset = metrologyToScienceOffset
		calibResults[slot].mesAlphaLength.append(		mesAlphaLength)
		calibResults[slot].mesBetaLength.append(		mesBetaLength)
		calibResults[slot].mesRMSModelFit.append(		mesRMSModelFit)
		calibResults[slot].mesRMSRepeatability.append(	mesRMSRepeatability)
		calibResults[slot].mesMaxHysteresis.append(		mesMaxHysteresis)
		calibResults[slot].mesMaxNL.append(				mesMaxNL)
		calibResults[slot].mesMaxNLDerivative.append(	mesMaxNLDerivative)
		calibResults[slot].mesRMSAlignmentError.append(	mesRMSAlignmentError)
		calibResults[slot].mesMaxAlignmentError.append(	mesMaxAlignmentError)
		calibResults[slot].mesMaxRoundnessError.append(	mesMaxRoundnessError)
		calibResults[slot].calcDone 				= True

def update_positioners_model(calibResults, testBench):
	nbSlots = len(calibResults)
	for slot in range(0,nbSlots):

		sortedCentroidsXY = calibResults[slot].sortedCentroidsXY
		nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData = sortedCentroidsXY.shape

		direction = DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER
		if testBench.positioners[slot].ID == calibResults[slot].positionerID:
			meanAlphaMeasures = np.full((nbSteps),np.nan)
			meanBetaMeasures = np.full((nbSteps),np.nan)
			meanAlphaCommand = np.full((nbSteps),np.nan)
			meanBetaCommand = np.full((nbSteps),np.nan)

			for step in range(0,nbSteps):
				meanAlphaMeasures[step] = np.nanmean(np.ravel(calibResults[slot].measuredAngles[:,:,DEFINES.PARAM_AXIS_ALPHA,step,direction,0]))
				meanBetaMeasures[step] = np.nanmean(np.ravel(calibResults[slot].measuredAngles[:,:,DEFINES.PARAM_AXIS_BETA,step,direction,0]))
				meanAlphaCommand[step] = np.nanmean(np.ravel(calibResults[slot].sortedTargetCommand[:,DEFINES.PARAM_AXIS_ALPHA,step,direction,DEFINES.PARAM_AXIS_ALPHA]))
				meanBetaCommand[step] = np.nanmean(np.ravel(calibResults[slot].sortedTargetCommand[:,DEFINES.PARAM_AXIS_BETA,step,direction,DEFINES.PARAM_AXIS_BETA]))
			
			meanAlphaCommand = meanAlphaCommand[~np.isnan(meanAlphaMeasures)]
			meanBetaCommand = meanBetaCommand[~np.isnan(meanBetaMeasures)]
			meanAlphaMeasures = meanAlphaMeasures[~np.isnan(meanAlphaMeasures)]
			meanBetaMeasures = meanBetaMeasures[~np.isnan(meanBetaMeasures)]

			#Construct the correctors for the model
			alphaCorrector = interpolate.interp1d(meanAlphaMeasures, meanAlphaCommand, kind='linear', fill_value='extrapolate') #gives the real value out of the command
			betaCorrector = interpolate.interp1d(meanBetaMeasures, meanBetaCommand, kind='linear', fill_value='extrapolate')
			
			#Update positioner model
			testBench.positioners[slot].model.lengthAlpha			= calibResults[slot].modelArmLengths[DEFINES.PARAM_AXIS_ALPHA]
			testBench.positioners[slot].model.lengthBeta			= calibResults[slot].modelArmLengths[DEFINES.PARAM_AXIS_BETA]
			testBench.positioners[slot].model.offsetAlpha			= calibResults[slot].modelOffsets[DEFINES.PARAM_AXIS_ALPHA]
			testBench.positioners[slot].model.offsetBeta			= calibResults[slot].modelOffsets[DEFINES.PARAM_AXIS_BETA]
			testBench.positioners[slot].model.centerX				= calibResults[slot].modelCenter[0]
			testBench.positioners[slot].model.centerY				= calibResults[slot].modelCenter[1]
			testBench.positioners[slot].model.nonLinearityAlpha 	= calibResults[slot].modelNonLinearity[:,:,DEFINES.PARAM_AXIS_ALPHA,:,:]
			testBench.positioners[slot].model.nonLinearityBeta 		= calibResults[slot].modelNonLinearity[:,:,DEFINES.PARAM_AXIS_BETA,:,:]
			testBench.positioners[slot].model.eccentricityAlpha		= calibResults[slot].modelEccentricity[:,:,DEFINES.PARAM_AXIS_ALPHA,:,:]
			testBench.positioners[slot].model.eccentricityBeta		= calibResults[slot].modelEccentricity[:,:,DEFINES.PARAM_AXIS_BETA,:,:]
			testBench.positioners[slot].model.metrologyToScience 	= calibResults[slot].metrologyToScienceOffset
			testBench.positioners[slot].model.getCorrectedAlpha 	= alphaCorrector
			testBench.positioners[slot].model.getCorrectedBeta		= betaCorrector

			testBench.positioners[slot].calibrated 					= True

def plot(calibResults, config):
	if not config.plotResults:
		return 

	nbSlots = len(calibResults)

	figID = np.array([np.ones((DEFINES.PLOT_CALIB_NB_SUBPLOTS)).astype(np.uint8),np.linspace(1,DEFINES.PLOT_CALIB_NB_SUBPLOTS,DEFINES.PLOT_CALIB_NB_SUBPLOTS).astype(np.uint8)])

	titleFontsize 	= [DEFINES.PLOT_TITLE_FONTSIZE_SINGLE, DEFINES.PLOT_TITLE_FONTSIZE_OVERVIEW]
	labelFontsize 	= [DEFINES.PLOT_AXES_LABEL_FONTSIZE_SINGLE, DEFINES.PLOT_AXES_LABEL_FONTSIZE_OVERVIEW]
	ticksFontsize 	= [DEFINES.PLOT_AXES_TICKS_FONTSIZE_SINGLE, DEFINES.PLOT_AXES_TICKS_FONTSIZE_OVERVIEW]
	figNbRows 		= [DEFINES.PLOT_CALIB_NB_ROW_SUBPLOTS_SINGLE, DEFINES.PLOT_CALIB_NB_ROW_SUBPLOTS_OVERVIEW]
	figNbCols 		= [DEFINES.PLOT_CALIB_NB_COL_SUBPLOTS_SINGLE, DEFINES.PLOT_CALIB_NB_COL_SUBPLOTS_OVERVIEW]
	figKeepOpen 	= [DEFINES.PLOT_KEEP_FIGURE_OPEN_SINGLE, DEFINES.PLOT_KEEP_FIGURE_OPEN_OVERVIEW]
	figSize 		= [DEFINES.PLOT_FIGURE_SIZE_SINGLE, DEFINES.PLOT_FIGURE_SIZE_OVERVIEW]
	lineWidth		= [DEFINES.PLOT_LINEWIDTH_SINGLE, DEFINES.PLOT_LINEWIDTH_OVERVIEW]

	plotProperties	= customPlot.plotProperties
	nbPlotsPerGraph = len(titleFontsize)

	for slot in range(0,nbSlots):
		axesToTest = calibResults[slot].calibrationParameters.axesToTest
		nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData = calibResults[slot].sortedCentroidsXY.shape

		figuresToPlot = []

		overviewPath = config.get_current_overview_folder()
		individualFigurePath = config.get_current_figure_folder(calibResults[slot].positionerID)

		overviewFile = config.get_overwiew_filename(calibResults[slot].positionerID)
		overviewFile += '_calib'+config.overviewExtension
		
		os.makedirs(overviewPath, exist_ok=True)
		os.makedirs(individualFigurePath, exist_ok=True)

		for i in range(0,nbPlotsPerGraph):
			for j in range(0,DEFINES.PLOT_CALIB_NB_SUBPLOTS):
				
				if figNbRows[i] == DEFINES.PLOT_CALIB_NB_ROW_SUBPLOTS_SINGLE and figNbCols[i] == DEFINES.PLOT_CALIB_NB_COL_SUBPLOTS_SINGLE:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Plotting positioner {calibResults[slot].positionerID}, {plotProperties[j][DEFINES.PLOT_TITLE_ID]}')
				else:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Plotting positioner {calibResults[slot].positionerID}, [Overview] {plotProperties[j][DEFINES.PLOT_TITLE_ID]}')

				#Check if we need to recreate a new figure
				if figID[i,j] == 1:
					if figSize[i] == DEFINES.PLOT_MAX_FIGURE_SIZE:
						figuresToPlot.append(plt.figure())
						figManager = plt.get_current_fig_manager()
						figManager.resize(*figManager.window.maxsize())
						figuresToPlot[-1].set_tight_layout(True)
					else:
						figuresToPlot.append(plt.figure(figsize=figSize[i],dpi=DEFINES.PLOT_DPI))

					figuresToPlot[-1].set_tight_layout(True)

				#Create the axis layout
				drawingAxis = figuresToPlot[-1].add_subplot(figNbRows[i],figNbCols[i],figID[i,j])

				drawingAxis.set_title(plotProperties[j][DEFINES.PLOT_TITLE_ID], fontsize=titleFontsize[i])
				drawingAxis.set_xlabel(plotProperties[j][DEFINES.PLOT_LABEL_X_ID], fontsize= labelFontsize[i])
				drawingAxis.set_ylabel(plotProperties[j][DEFINES.PLOT_LABEL_Y_ID], fontsize= labelFontsize[i])
				drawingAxis.tick_params(labelsize = ticksFontsize[i])
				drawingAxis.autoscale(enable=True, axis='both', tight=True)
				
				#Plot the graph
				plotProperties[j][DEFINES.PLOT_FUNC_ID](drawingAxis, lineWidth[i], calibResults[slot])
				
				#Save the previous figure if all the subplots were done
				if len(figuresToPlot) > 0 and (figID[i,j] >= figNbRows[i]*figNbCols[i] or j >= DEFINES.PLOT_CALIB_NB_SUBPLOTS-1):
					
					if figNbRows[i] == DEFINES.PLOT_CALIB_NB_ROW_SUBPLOTS_SINGLE and figNbCols[i] == DEFINES.PLOT_CALIB_NB_COL_SUBPLOTS_SINGLE:
						figureFileName = 'Calib_'+str(i)+str(j)+'_'+plotProperties[j][DEFINES.PLOT_TITLE_ID]+config.figureExtension
						figureFileName=figureFileName.replace(" ", "_")
						figurePath = individualFigurePath

						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName))
					else:
						figurePath = overviewPath
						figureFileName = overviewFile
						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName)) #save in the overviews

						figurePath = individualFigurePath
						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName)) #save in the individual positioner folder

						if calibResults[slot].config.nbTestingLoops > 1:
							figurePath = config.get_current_positioner_folder(calibResults[slot].positionerID, includeLifetimeIteration = False)
							figurePath = os.path.join(figurePath,config.overviewsFolder)
							os.makedirs(figurePath, exist_ok=True)
							figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName)) #save all overviews of a lifetime in a same folder

					# Close all the saved figures or draw them
					if not figKeepOpen[i]:
						for figure in figuresToPlot:
							plt.close(figure)
					else:
						plt.draw()
						plt.pause(1e-17)

def plot_lifetime(calibResults, config):
	if not config.plotResults or config.nbTestingLoops < 2:
		return 

	nbSlots = len(calibResults)

	figID = np.array([np.ones((DEFINES.PLOT_CALIB_NB_SUBPLOTS_LIFETIME)).astype(np.uint8),np.linspace(1,DEFINES.PLOT_CALIB_NB_SUBPLOTS_LIFETIME,DEFINES.PLOT_CALIB_NB_SUBPLOTS_LIFETIME).astype(np.uint8)])

	titleFontsize 	= [DEFINES.PLOT_TITLE_FONTSIZE_SINGLE, DEFINES.PLOT_TITLE_FONTSIZE_LIFETIME]
	labelFontsize 	= [DEFINES.PLOT_AXES_LABEL_FONTSIZE_SINGLE, DEFINES.PLOT_AXES_LABEL_FONTSIZE_LIFETIME]
	ticksFontsize 	= [DEFINES.PLOT_AXES_TICKS_FONTSIZE_SINGLE, DEFINES.PLOT_AXES_TICKS_FONTSIZE_LIFETIME]
	figNbRows 		= [DEFINES.PLOT_CALIB_NB_ROW_SUBPLOTS_SINGLE, DEFINES.PLOT_CALIB_NB_ROW_SUBPLOTS_LIFETIME]
	figNbCols 		= [DEFINES.PLOT_CALIB_NB_COL_SUBPLOTS_SINGLE, DEFINES.PLOT_CALIB_NB_COL_SUBPLOTS_LIFETIME]
	figKeepOpen 	= [DEFINES.PLOT_KEEP_FIGURE_OPEN_SINGLE, DEFINES.PLOT_KEEP_FIGURE_OPEN_LIFETIME]
	figSize 		= [DEFINES.PLOT_FIGURE_SIZE_SINGLE, DEFINES.PLOT_FIGURE_SIZE_LIFETIME]
	lineWidth		= [DEFINES.PLOT_LINEWIDTH_SINGLE, DEFINES.PLOT_LINEWIDTH_LIFETIME]

	plotProperties	= customPlot.plotPropertiesLifetime
	nbPlotsPerGraph = len(titleFontsize)

	for slot in range(0,nbSlots):
		axesToTest = calibResults[slot].calibrationParameters.axesToTest
		nbRepetitions,nbStartingPoints,nbAxes,nbSteps,nbDirections,nbCentroidsData = calibResults[slot].sortedCentroidsXY.shape

		figuresToPlot = []

		individualFigurePath = config.get_current_figure_folder(calibResults[slot].positionerID)
		
		multipleFigureFile = 'Lifetime_'+config.get_overwiew_filename(calibResults[slot].positionerID)
		multipleFigureFile += '_calib'+config.overviewExtension
		
		os.makedirs(individualFigurePath, exist_ok=True)

		for i in range(0,nbPlotsPerGraph):
			for j in range(0,DEFINES.PLOT_CALIB_NB_SUBPLOTS_LIFETIME):
				
				if figNbRows[i] == DEFINES.PLOT_CALIB_NB_ROW_SUBPLOTS_SINGLE and figNbCols[i] == DEFINES.PLOT_CALIB_NB_COL_SUBPLOTS_SINGLE:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Plotting positioner {calibResults[slot].positionerID}, {plotProperties[j][DEFINES.PLOT_TITLE_ID]}')
				else:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Plotting positioner {calibResults[slot].positionerID}, [Lifetime] {plotProperties[j][DEFINES.PLOT_TITLE_ID]}')

				#Check if we need to recreate a new figure
				if figID[i,j] == 1:
					if figSize[i] == DEFINES.PLOT_MAX_FIGURE_SIZE:
						figuresToPlot.append(plt.figure())
						figManager = plt.get_current_fig_manager()
						figManager.resize(*figManager.window.maxsize())
						figuresToPlot[-1].set_tight_layout(True)
					else:
						figuresToPlot.append(plt.figure(figsize=figSize[i],dpi=DEFINES.PLOT_DPI))

					figuresToPlot[-1].set_tight_layout(True)

				#Create the axis layout
				drawingAxis = figuresToPlot[-1].add_subplot(figNbRows[i],figNbCols[i],figID[i,j])

				drawingAxis.set_title(plotProperties[j][DEFINES.PLOT_TITLE_ID], fontsize=titleFontsize[i])
				drawingAxis.set_xlabel(plotProperties[j][DEFINES.PLOT_LABEL_X_ID], fontsize= labelFontsize[i])
				drawingAxis.set_ylabel(plotProperties[j][DEFINES.PLOT_LABEL_Y_ID], fontsize= labelFontsize[i])
				drawingAxis.tick_params(labelsize = ticksFontsize[i])
				drawingAxis.autoscale(enable=True, axis='both', tight=True)
				
				#Plot the graph
				plotProperties[j][DEFINES.PLOT_FUNC_ID](drawingAxis, lineWidth[i], calibResults[slot])
				
				#Save the previous figure if all the subplots were done
				if len(figuresToPlot) > 0 and (figID[i,j] >= figNbRows[i]*figNbCols[i] or j >= DEFINES.PLOT_CALIB_NB_SUBPLOTS_LIFETIME-1):
					if figNbRows[i] == DEFINES.PLOT_CALIB_NB_ROW_SUBPLOTS_SINGLE and figNbCols[i] == DEFINES.PLOT_CALIB_NB_COL_SUBPLOTS_SINGLE:
						figureFileName = 'Lifetime_calib_'+str(i)+str(j)+'_'+plotProperties[j][DEFINES.PLOT_TITLE_ID]+calibResults[slot].config.figureExtension
						figureFileName=figureFileName.replace(" ", "_")
						figurePath = individualFigurePath

						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName))
					else:
						figureFileName = multipleFigureFile
						figurePath = individualFigurePath
						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName)) #save in the individual positioner folder

						if calibResults[slot].config.nbTestingLoops > 1:
							figurePath = config.get_current_positioner_folder(calibResults[slot].positionerID, includeLifetimeIteration = False)
							figurePath = os.path.join(figurePath,config.overviewsFolder)
							os.makedirs(figurePath, exist_ok=True)
							figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName)) #save all overviews of a lifetime in a same folder

					# Close all the saved figures or draw them
					if not figKeepOpen[i]:
						for figure in figuresToPlot:
							plt.close(figure)
					else:
						plt.draw()
						plt.pause(1e-17)
						

def main():
	pass

if __name__ == '__main__':
	main()