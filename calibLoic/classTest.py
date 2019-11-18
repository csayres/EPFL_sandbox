#cython: language_level=3
import json
import numpy.random as rand
import numpy as np
import miscmath as mm
import time
import os
import logger as log
import DEFINES
import matplotlib.pyplot as plt
import testPlot as customPlot
import classConfig
import classPositioners
import errors

class Parameters():
	__slots__ = (	'approachDistance',\
					'cruiseCurrentAlpha',\
					'cruiseCurrentBeta',\
					'motorRpmAlpha',\
					'motorRpmBeta',\
					'correctionCurrentAlpha',\
					'correctionCurrentBeta',\
					'correctionMotorRpmAlpha',\
					'correctionMotorRpmBeta',\
					'waitCurrentAlpha',\
					'waitCurrentBeta',\
					'nbTargets',\
					'numberOfRepetitions',\
					'numberOfCorrections',\
					'stopOnDesiredError',\
					'desiredTargetError',\
					'maxTargetError',\
					'alphaTestRange',\
					'betaTestRange',\
					'workSpaceMargin',\
					'hardstopMargin',\
					'extendedBetaTest',\
					'avoidTargetRandomize',\
					'refoldAfterTarget')
	
	def __init__(self):

		self.approachDistance					= 0.5 		# [deg]
		self.cruiseCurrentAlpha					= 100		# [%]
		self.cruiseCurrentBeta					= 100		# [%]
		self.motorRpmAlpha 						= 4000		# [RPM]
		self.motorRpmBeta 						= 4000		# [RPM]
		self.correctionCurrentAlpha				= 100		# [%]
		self.correctionCurrentBeta				= 100		# [%]
		self.correctionMotorRpmAlpha 			= 4000		# [RPM]
		self.correctionMotorRpmBeta 			= 4000		# [RPM]
		self.waitCurrentAlpha 					= 30 		# [%]
		self.waitCurrentBeta 					= 30 		# [%]
		self.nbTargets							= 100		# Number of targets. Also is the number of different angles for each motor
		self.numberOfRepetitions				= 5			# How many times should each target be used
		self.numberOfCorrections				= 2			# Maximum number of currentMove moves
		self.stopOnDesiredError					= True 		# Stop the currentMove moves when te error is below the required performance 
		self.desiredTargetError					= 5			# Desired target error [um] 
		self.maxTargetError						= 200		# Maximum deviation allowed to perform the currentMove moves [um] 
		self.alphaTestRange						= [0,	360]	# Alpha motor range to test
		self.betaTestRange						= [0,	360]	# Beta motor range to test
		self.workSpaceMargin					= 1/10*self.maxTargetError/1000 		# Margin in mm to the edges of the donut workspace
		self.hardstopMargin						= 2			# Degrees margin for the hardstops
		self.extendedBetaTest					= True 	# Also test the second configuration where beta > 180°
		self.avoidTargetRandomize				= True 		# If true, the target are in the motor command order. Gives a way faster testing time.
		self.refoldAfterTarget					= False		# Shall the positioner return to 0,0 after each target ?

	def load(self,fileName):
		#Load all the data in the file, exculding the fileInfos
		try:
			with open(os.path.join(fileName),'r') as inFile:
				variablesToLoad=json.load(inFile)
				for key in variablesToLoad.keys():
					if key in type(self).__slots__:
						setattr(self, key, variablesToLoad[key])
					else:
						log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING,1,f'Unexpected data was encountered during the loading of the test parameters. Faulty key: {key}')
						if DEFINES.RAISE_ERROR_ON_UNEXPECTED_KEY:
							raise errors.IOError('Unexpected data was encountered during the loading of the test parameters') from None
						
		except OSError:
			raise errors.IOError('The test parameters file could not be found') from None

	def save(self,filePath,fileName):
		variablesToSave = {}
		for slots in [getattr(cls, '__slots__', []) for cls in type(self).__mro__]:
			for attr in slots:
				variablesToSave[attr] = getattr(self, attr)

		os.makedirs(filePath, exist_ok=True)
		with open(os.path.join(filePath, fileName),'w+') as outFile:
			json.dump(variablesToSave, outFile, separators = (',\n',': '))


class Results():
	__slots__ = ( 	'config',\
					'requirements',\
					'testBenchName',\
					'positionerID',\
					'slotID',\
					'positionersArmLengths',\
					'slotsCenters',\
					'testParameters',\
					'targets',\
					'targetsErrors',\
					'sortedCommands',\
					'sortedCentroidsXY',\
					'realAngles',\
					'repeatability',\
					'modelError',\
					'nbCorrections',\
					'mesRMSError1stMove',\
					'mesRMSRepeatability1stMove',\
					'mesTargetConvergeance',\
					'mesMaxNbMoves',\
					'runDone',\
					'completionTime',\
					'calcDone')

	def __init__(self):
		self.config 					= classConfig.Config()
		self.requirements 				= classPositioners.PositionerRequirements()

		self.testBenchName 				= ''
		self.positionerID 				= []
		self.slotID						= []
		self.slotsCenters 				= []
		self.positionersArmLengths 		= []
		self.testParameters				= Parameters()
		self.targets					= []
		self.targetsErrors				= []
		self.sortedCommands				= []
		self.sortedCentroidsXY			= []
		self.realAngles					= []
		self.repeatability				= []
		self.modelError 				= []
		self.nbCorrections 				= []
		self.mesRMSError1stMove 		= []
		self.mesRMSRepeatability1stMove = []
		self.mesTargetConvergeance 		= []
		self.mesMaxNbMoves 				= []

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
							setattr(self, key, np.array(variablesToLoad[key]))
						else:
							setattr(self, key, variablesToLoad[key])
					elif key in type(self.testParameters).__slots__:
						if isinstance(variablesToLoad[key], list):
							setattr(self.testParameters, key, np.array(variablesToLoad[key]))
						else:
							setattr(self.testParameters, key, variablesToLoad[key])
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
						log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING,1,f'Unexpected data was encountered during the loading of the test results. Faulty key: {key}')
						if DEFINES.RAISE_ERROR_ON_UNEXPECTED_KEY:
							raise errors.IOError('Unexpected data was encountered during the loading of the test results') from None
						
		except OSError:
			raise errors.IOError('The test results file could not be found') from None

	def save(self,filePath,fileName):
		variablesToSave = {}
		for slots in [getattr(cls, '__slots__', []) for cls in type(self).__mro__]:
			for attr in slots:
				if isinstance(getattr(self, attr), np.ndarray):
					variablesToSave[attr] = getattr(self, attr).tolist()
				elif attr == 'testParameters':
					for subSlots in [getattr(cls, '__slots__', []) for cls in type(self.testParameters).__mro__]:
						for subAttr in subSlots:
							if isinstance(getattr(self.testParameters, subAttr), np.ndarray):
								variablesToSave[subAttr] = getattr(self.testParameters, subAttr).tolist()
							else:
								variablesToSave[subAttr] = getattr(self.testParameters, subAttr)
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

def run(testBench, testParameters, testResults, config, processManager):
	try:
		if len(testResults) is not testBench.nbSlots:
			raise errors.Error("Test result container has the wrong length")

		rand.seed()
		processManager.clear_centroids_results()

		nbSlots 			= testBench.nbSlots
		nbRepetitions 		= testParameters.numberOfRepetitions
		maxNbCorrections 	= testParameters.numberOfCorrections
		maxNbMoves 			= maxNbCorrections + 1
		approachDistance 	= testParameters.approachDistance * np.pi/180
		hardstopMargin 		= testParameters.hardstopMargin * np.pi/180
		nbTargets 			= testParameters.nbTargets

		changeCurrentCruiseToWait 		= not (testParameters.cruiseCurrentAlpha 	== testParameters.waitCurrentAlpha 			and testParameters.cruiseCurrentBeta 	== testParameters.waitCurrentBeta)
		changeCurrentCruiseToCorrection = not (testParameters.cruiseCurrentAlpha 	== testParameters.correctionCurrentAlpha 	and testParameters.cruiseCurrentBeta 	== testParameters.correctionCurrentBeta)
		changeCurrentCorrectionToWait 	= not (testParameters.waitCurrentAlpha 		== testParameters.correctionCurrentAlpha 	and testParameters.waitCurrentBeta 		== testParameters.correctionCurrentBeta)
		changeRPMCruiseToCorrection 	= not (testParameters.motorRpmAlpha 		== testParameters.correctionMotorRpmAlpha 	and testParameters.motorRpmBeta 		== testParameters.correctionMotorRpmBeta)

		totalNbPoints 		= nbTargets*nbRepetitions
		if totalNbPoints == 0:
			totalPtsDigits = 1
		else:
			totalPtsDigits = int(np.log10(totalNbPoints)+1) #get the number of digits to display

		sortedCommands		= np.full((testBench.nbSlots, nbRepetitions, nbTargets, maxNbMoves, 2),np.nan)
		commandsNonLinearity= np.zeros((testBench.nbSlots, nbTargets, 2))
		sortedCentroidsXY 	= np.full((testBench.nbSlots, nbRepetitions, nbTargets, maxNbMoves, 8),np.nan)
		realAngles			= np.full((testBench.nbSlots, nbRepetitions, nbTargets, maxNbMoves, 2),np.nan)
		nbCorrections		= np.zeros((testBench.nbSlots, nbRepetitions, nbTargets))

		#Generate the targets
		targets		  		= np.full((testBench.nbSlots, nbRepetitions, nbTargets, maxNbMoves, 2),np.nan)
		targetsErrors 		= np.full((testBench.nbSlots, nbRepetitions, nbTargets, maxNbMoves, 3),np.nan)

		for slot in range(0,nbSlots):
			angleGenerated = False

			hadrstopAlphaLow = testBench.positioners[slot].physics.alphaAxisRange[0] * np.pi/180
			hadrstopAlphaHigh = testBench.positioners[slot].physics.alphaAxisRange[1] * np.pi/180
			hadrstopBetaLow = testBench.positioners[slot].physics.betaAxisRange[0] * np.pi/180
			hadrstopBetaHigh = testBench.positioners[slot].physics.betaAxisRange[1] * np.pi/180

			#Check if the angle range is the same as the previous positioner. If it is, do not regenerate the grid
			if slot > 0:
				if 	(testBench.positioners[slot-1].physics.alphaAxisRange[0] == testBench.positioners[slot].physics.alphaAxisRange[0]) and \
					(testBench.positioners[slot-1].physics.alphaAxisRange[1] == testBench.positioners[slot].physics.alphaAxisRange[1]) and \
					(testBench.positioners[slot-1].physics.betaAxisRange[0] == testBench.positioners[slot].physics.betaAxisRange[0]) and \
					(testBench.positioners[slot-1].physics.betaAxisRange[1] == testBench.positioners[slot].physics.betaAxisRange[1]):
					angleGenerated = True
			
			if not angleGenerated:
				alphaMin 	= testParameters.alphaTestRange[0] * np.pi/180+approachDistance+hardstopMargin
				alphaMax 	= testParameters.alphaTestRange[1] * np.pi/180-approachDistance-hardstopMargin
				betaMin 	= testParameters.betaTestRange[0] * np.pi/180+approachDistance+hardstopMargin
				betaMax 	= testParameters.betaTestRange[1] * np.pi/180-approachDistance-hardstopMargin

				#Check that the required axis test range is not exceeding the positioner workspace
				if alphaMin-approachDistance < hadrstopAlphaLow:
					alphaMin = hadrstopAlphaLow+approachDistance
				if alphaMax+approachDistance > hadrstopAlphaHigh:
					alphaMax = hadrstopAlphaHigh-approachDistance
				if betaMin-approachDistance < hadrstopBetaLow:
					betaMin = hadrstopBetaLow+approachDistance
				if betaMax+approachDistance > hadrstopBetaHigh:
					betaMax = hadrstopBetaHigh-approachDistance

				if not testParameters.extendedBetaTest and betaMin < np.pi:
					betaMax = min(betaMax, np.pi)
					testParameters.betaTestRange[1] = int(betaMax*180/np.pi)

				#create evenly distributed targets on alpha and beta
				alphaAngles, alphaStepSize 	= np.linspace(	alphaMin,\
															alphaMax,\
															nbTargets,endpoint = False, retstep = True)

				betaAngles, betaStepSize 	= np.linspace(	betaMin,\
															betaMax,\
															nbTargets,endpoint = False, retstep = True)


				#create a random offset on each axis to have random targets
				alphaAlterationAngle = rand.uniform(low = 0, high = alphaStepSize)
				betaAlterationAngle = rand.uniform(low = 0, high = betaStepSize)

				alphaAngles = np.add(alphaAngles,alphaAlterationAngle)
				betaAngles = np.add(betaAngles,betaAlterationAngle)

				#shuffle the arrays to destroy the linspace order
				if not testParameters.avoidTargetRandomize:
					rand.shuffle(alphaAngles)
					rand.shuffle(betaAngles)

			#transpose the angles into XY targets
			centerX 		= testBench.positioners[slot].model.centerX
			centerY 		= testBench.positioners[slot].model.centerY
			center 			= (centerX, centerY)
			lAlphaTarget 	= testBench.positioners[slot].model.lengthAlpha-testParameters.workSpaceMargin
			lBetaTarget 	= testBench.positioners[slot].model.lengthBeta
			lengthAlpha 	= testBench.positioners[slot].model.lengthAlpha
			lengthBeta 		= testBench.positioners[slot].model.lengthBeta

			#CHECK THE CALCULATION; THE WORKSPACE MARGIN RESULTS IN THE FINAL TARGET ERROR.....
			for target in range(0,nbTargets):
				#Generate the target with a workspace margin
				endpoint = mm.get_endpoint(centerX,centerY,lAlphaTarget,lBetaTarget,alphaAngles[target],betaAngles[target])
				targetAngles = [alphaAngles[target],betaAngles[target]]

				#retrieve the robot arm angles
				armAngles = mm.get_model_angles_from_endpoint(center,endpoint, lengthAlpha, lengthBeta)
				if armAngles == []:
					print(target)
				armAngles = mm.get_closest_angle(armAngles, targetAngles)
				# print((endpoint, armAngles))

				#Check if the target is still inside the workspace of the positioner and re-born the target if necessary
				if armAngles[0]-abs(approachDistance) < hadrstopAlphaLow+hardstopMargin:
					armAngles[0] = hadrstopAlphaLow+abs(approachDistance)+hardstopMargin
				if armAngles[0]+abs(approachDistance) > hadrstopAlphaHigh-hardstopMargin:
					armAngles[0] = hadrstopAlphaHigh-abs(approachDistance)-hardstopMargin
				if armAngles[1]-abs(approachDistance) < hadrstopBetaLow+hardstopMargin:
					armAngles[1] = hadrstopBetaLow+abs(approachDistance)+hardstopMargin
				if armAngles[1]+abs(approachDistance) > hadrstopBetaHigh-hardstopMargin:
					armAngles[1] = hadrstopBetaHigh-abs(approachDistance)-hardstopMargin

				endpoint = mm.get_endpoint(centerX,centerY,lengthAlpha,lengthBeta,armAngles[0],armAngles[1])

				for repetition in range(0,nbRepetitions):
					targets[slot,repetition, target, 0, 0] = endpoint[0]
					targets[slot,repetition, target, 0, 1] = endpoint[1]
																										# L?INTERPOLATEUR EST A L'ENVERS
					sortedCommands[slot,repetition, target,  0, 0] = testBench.positioners[slot].model.getCorrectedAlpha(armAngles[0])-testBench.positioners[slot].model.offsetAlpha
					sortedCommands[slot,repetition, target, 0, 1] = testBench.positioners[slot].model.getCorrectedBeta(armAngles[1])-testBench.positioners[slot].model.offsetBeta
				
				commandsNonLinearity[slot,target, 0] = sortedCommands[slot,repetition, target,  0, 0]-armAngles[0]
				commandsNonLinearity[slot,target, 1] = sortedCommands[slot,repetition, target,  0, 1]-armAngles[1]

		# f=plt.figure()
		# plt.gca().invert_yaxis()
		# plt.scatter(np.ravel(targets[:, 0, :, 0, 0]),np.ravel(targets[:, 0, :, 0, 1]), color = 'red', marker = 'x', s = 1)
		# plt.show()
		# f=plt.figure()
		# plt.scatter(np.ravel(targets[:, 0, :, 0, 0]),np.ravel(targets[:, 0, :, 0, 1]), color = 'red', marker = 'x', s = 1)
		# plt.gca().invert_yaxis()
		# plt.draw()
		# plt.pause(1e-17)

		#Setup the ROI if it is not dynamic
		if testBench.cameraXY.parameters.softROIrequired:
			testBench.cameraXY.setMaxROI()
			testBench.cameraXY.setExposure(testBench.slotsExposures[0])

		#start the positioners
		testBench.set_current_all_positioners(testParameters.cruiseCurrentAlpha, testParameters.cruiseCurrentBeta)
		testBench.set_speed_all_positioners(testParameters.motorRpmAlpha, testParameters.motorRpmBeta)
		testBench.move_all_positioners_to_origin()

		#Change current
		if not changeCurrentCruiseToWait:
			testBench.set_current_all_positioners(testParameters.waitCurrentAlpha, testParameters.waitCurrentBeta)

		imageWindowSize = max(int(testParameters.maxTargetError/testBench.cameraXY.parameters.scaleFactor/1000), DEFINES.PC_CAMERA_XY_TEST_CROP)*1.2

		tStart = time.time()
		currentPoint = 1
		firstCentroid = 0

		#start the moves
		for repetition in range(0,nbRepetitions):
			for target in range(0,nbTargets):
				finishedSlots = []
				for currentMove in range(0, maxNbMoves):
					# Adapt positioner parameters for the next target move
					if currentMove == 0:
						# Adapt positioner parameters for the cruise move (cruise current and cruise speed)
						if (currentPoint == 1 and changeCurrentCruiseToWait) or (currentPoint > 1 and changeCurrentCruiseToWait and not testParameters.refoldAfterTarget):
							testBench.set_current_all_positioners(testParameters.cruiseCurrentAlpha, testParameters.cruiseCurrentBeta)
						if (changeRPMCruiseToCorrection and not testParameters.refoldAfterTarget):
							testBench.set_speed_all_positioners(testParameters.motorRpmAlpha, testParameters.motorRpmBeta)
					else:
						# Adapt positioner parameters for the correction moves (correction current and correction speed)
						if changeCurrentCorrectionToWait:
							testBench.set_current_all_positioners(testParameters.correctionCurrentAlpha, testParameters.correctionCurrentBeta)
						if (currentMove == 1 and changeRPMCruiseToCorrection):
							testBench.set_speed_all_positioners(testParameters.correctionMotorRpmAlpha, testParameters.correctionMotorRpmBeta)

					# plt.scatter(np.ravel(targets[:, repetition, target, currentMove, 0]),np.ravel(targets[:, repetition, target, currentMove, 1]), color = 'green', marker = 'o', s = 1)
					# plt.draw()
					# plt.pause(1e-17)

					# Move to the target
					testBench.move_all_positioners_different_angles(np.ravel(sortedCommands[:, repetition, target, currentMove, 0]), np.ravel(sortedCommands[:, repetition, target, currentMove, 1]), approachDistance, isInRad = True)

					#Adapt the current to wait current
					if (currentMove == 0 and changeCurrentCruiseToWait) or (currentMove > 0 and changeCurrentCorrectionToWait):
						testBench.set_current_all_positioners(testParameters.waitCurrentAlpha, testParameters.waitCurrentAlpha)
					
					# Take the image
					ROI = np.zeros((5))

					if testBench.cameraXY.parameters.softROIrequired:
						completeImage = testBench.cameraXY.getImage()

					for positioner in testBench.positioners:
						if not positioner.benchSlot in finishedSlots:
							imageID = mm.generate_img_ID(positioner.benchSlot, repetition, currentMove, 0, target, 0, DEFINES.MM_IMG_ID_XY_IDENTIFIER)

							(targetX,targetY) = mm.get_endpoint(	positioner.model.centerX,positioner.model.centerY,\
																	positioner.model.lengthAlpha,positioner.model.lengthBeta,\
																	sortedCommands[positioner.benchSlot, repetition, target, currentMove, 0] ,sortedCommands[positioner.benchSlot, repetition, target, currentMove, 1] )
							(targetX,targetY) = (	int(targetX/testBench.cameraXY.parameters.scaleFactor),\
													int(targetY/testBench.cameraXY.parameters.scaleFactor))
							ROI[0] = targetX
							ROI[1] = targetY
							ROI[2] = imageWindowSize
							ROI[3] = imageWindowSize
							ROI[4] = (positioner.model.lengthAlpha+positioner.model.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/testBench.cameraXY.parameters.scaleFactor
							
							if testBench.cameraXY.parameters.softROIrequired:
								#Do a software crop of the approximated model area
								# print(f'\tComputing image {i:>2}/{testBench.nbSlots:2}')

								(image, offsetX, offsetY) = mm.cropImage(completeImage,ROI,testBench.cameraXY.parameters.maxX,testBench.cameraXY.parameters.maxY)
								validityCenter = (positioner.model.centerX/testBench.cameraXY.parameters.scaleFactor,positioner.model.centerY/testBench.cameraXY.parameters.scaleFactor)
								validityRadius = (positioner.model.lengthAlpha+positioner.model.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/testBench.cameraXY.parameters.scaleFactor
								
								processManager.centroidQueuePut((image, offsetX, offsetY, imageID, validityCenter, validityRadius), block = True)
							else:
								#Do a hardware crop of the approximated model area and compute the centroid
								# print(f'\tTaking image {i:>2}/{testBench.nbSlots:2}')
								testBench.cameraXY.setROI(ROI)
								testBench.cameraXY.setExposure(testBench.slotsExposures[positioner.benchSlot])
								testBench.cameraXY.getImage(processManager.centroidQueue,imageID)

					#wait for the centroid computations to finish
					processManager.centroidQueueJoin()

					#retrieve all the centroids and clear the results 
					lastCentroid = processManager.get_centroid_results_length()
					newCentroids = processManager.get_centroids_result(start = firstCentroid, end = lastCentroid)
					firstCentroid = lastCentroid

					for centroid in newCentroids:
						(slotID, repetitionID, currentMoveID, _, targetID, _, cameraTypeID) = mm.get_img_ID(np.int64(centroid[7]))
						sortedCentroidsXY[slotID, repetitionID, targetID, currentMoveID] = centroid

					#compute error
					for slot in range(0, nbSlots):
						#Skip the slots where the correction is not necessary
						if not slot in finishedSlots:
							if np.isnan(sortedCentroidsXY[slot,repetition, target, currentMove,0]) or np.isnan(sortedCentroidsXY[slot,repetition, target, currentMove,1]):
								#If the centroid is invalid, stop the corrections
								finishedSlots.append(slot)
							else:
								#Compute the error
								targetsErrors[slot,repetition, target, currentMove, 0] = sortedCentroidsXY[slot,repetition, target, currentMove,0]-targets[slot,repetition, target, 0, 0]
								targetsErrors[slot,repetition, target, currentMove, 1] = sortedCentroidsXY[slot,repetition, target, currentMove,1]-targets[slot,repetition, target, 0, 1]
								targetsErrors[slot,repetition, target, currentMove, 2] = np.sqrt(targetsErrors[slot,repetition, target, currentMove, 0]**2+targetsErrors[slot,repetition, target, currentMove, 1]**2)
								
								#get the computation variables
								centerX = testBench.positioners[slot].model.centerX
								centerY = testBench.positioners[slot].model.centerY
								center = (centerX, centerY)
								lengthAlpha = testBench.positioners[slot].model.lengthAlpha
								lengthBeta = testBench.positioners[slot].model.lengthBeta
								targetAngles = [sortedCommands[slot,repetition, target, currentMove, 0], sortedCommands[slot,repetition, target, currentMove, 1]]
								
								#Store the real angle of the measure
								endpoint = (sortedCentroidsXY[slot,repetition, target, currentMove,0], sortedCentroidsXY[slot,repetition, target, currentMove,1])
								armAngles = mm.get_model_angles_from_endpoint(center, endpoint, lengthAlpha, lengthBeta)

								if len(armAngles) > 0:
									# print(armAngles)
									armAngles = mm.get_closest_angle(armAngles, targetAngles) 
								else:
									armAngles = [np.nan, np.nan]

								realAngles[slot,repetition, target, currentMove] = armAngles

								#if the error is too big, stop the corrections
								if 1000*targetsErrors[slot,repetition, target, currentMove, 2] > testParameters.maxTargetError: 
									finishedSlots.append(slot)

								elif 1000*targetsErrors[slot,repetition, target, currentMove, 2] > testParameters.desiredTargetError or not testParameters.stopOnDesiredError:
									nbCorrections[slot,repetition,target] = currentMove

									#if we are allowed to perform the next correction, compute the angles
									if currentMove + 1 >= maxNbMoves:
										finishedSlots.append(slot)
									else:
										xCorrected = targets[slot,repetition, target, currentMove, 0]-targetsErrors[slot,repetition, target, currentMove, 0]
										yCorrected = targets[slot,repetition, target, currentMove, 1]-targetsErrors[slot,repetition, target, currentMove, 1]
										endpoint = (xCorrected, yCorrected)

										#retrieve the robot arm angles for the new target
										armAngles = mm.get_model_angles_from_endpoint(center, endpoint, lengthAlpha, lengthBeta)

										if len(armAngles) < 1: #if the endpoint could not be calculated
											finishedSlots.append(slot)

										else:
											armAngles = mm.get_closest_angle(armAngles, targetAngles)
											armAngles = np.add(armAngles, commandsNonLinearity[slot,target,:])

											#If we exceeded the borns, the correction is not accepted
											if 	armAngles[0]-approachDistance < testBench.positioners[slot].physics.alphaAxisRange[0]*np.pi/180 or \
												armAngles[0]+approachDistance > testBench.positioners[slot].physics.alphaAxisRange[1]*np.pi/180 or \
												armAngles[1]-approachDistance < testBench.positioners[slot].physics.betaAxisRange[0]*np.pi/180 or \
												armAngles[1]+approachDistance > testBench.positioners[slot].physics.betaAxisRange[1]*np.pi/180 or \
												armAngles[0] < testBench.positioners[slot].physics.alphaAxisRange[0]*np.pi/180 or \
												armAngles[0] > testBench.positioners[slot].physics.alphaAxisRange[1]*np.pi/180 or \
												armAngles[1] < testBench.positioners[slot].physics.betaAxisRange[0]*np.pi/180 or \
												armAngles[1] > testBench.positioners[slot].physics.betaAxisRange[1]*np.pi/180:
												finishedSlots.append(slot)
											else:
												#Store next target
												targets[slot,repetition, target, currentMove+1, 0] = xCorrected
												targets[slot,repetition, target, currentMove+1, 1] = yCorrected
												sortedCommands[slot,repetition, target, currentMove+1, 0] = armAngles[0]
												sortedCommands[slot,repetition, target, currentMove+1, 1] = armAngles[1]

								elif testParameters.stopOnDesiredError:
									nbCorrections[slot,repetition,target] = currentMove
									finishedSlots.append(slot)

					log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO, 0, 	f'Repetition {(repetition+1):>1}/{nbRepetitions:<1}, target {(target+1):>4}/{nbTargets:<4}, move {(currentMove+1):>2}/{maxNbMoves:<2}',removeMsgHeader = False)
					for slot in range(0,nbSlots):
						log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO, 1, 	f'Slot #{testBench.slotIDs[slot]} error: {1000*targetsErrors[slot,repetition, target, currentMove, 2]:03.3f} [um]',removeMsgHeader = True)

					if len(list(set(finishedSlots))) >= nbSlots:
						break

				#If we have to refold after each target
				if testParameters.refoldAfterTarget:
					# Adapt positioner parameters for the cruise move (cruise current and cruise speed)
					if changeCurrentCruiseToWait:
						testBench.set_current_all_positioners(testParameters.cruiseCurrentAlpha, testParameters.cruiseCurrentBeta)
					if (currentMove > 0 and changeRPMCruiseToCorrection):
						testBench.set_speed_all_positioners(testParameters.motorRpmAlpha, testParameters.motorRpmBeta)

					testBench.move_all_positioners_to_origin()

				completion = currentPoint/totalNbPoints
				(tRemaining, days, hours, minutes, seconds) = mm.get_ETA(tStart,completion)
				completion *= 100
				strETA = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(time.time()+tRemaining))
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'ETA: {strETA} (point {currentPoint:>{totalPtsDigits}}/{totalNbPoints:>{totalPtsDigits}} ({completion:6.2f}%), {days:02d}d {hours:02d}h{minutes:02d}m{seconds:04.1f}s remaining)',overwritable = True)
							
				currentPoint += 1


		#Free the memory
		processManager.clear_centroids_results()

		# Go back to the origin
		if not testParameters.refoldAfterTarget:
			# Adapt positioner parameters for the cruise move (cruise current and cruise speed)
			if changeCurrentCruiseToWait:
				testBench.set_current_all_positioners(testParameters.cruiseCurrentAlpha, testParameters.cruiseCurrentBeta)
			if (currentMove > 0 and changeRPMCruiseToCorrection):
				testBench.set_speed_all_positioners(testParameters.motorRpmAlpha, testParameters.motorRpmBeta)
			testBench.move_all_positioners_to_origin()

		testBench.stop_all_positioners()

		positionersArmLengths = np.zeros((testBench.nbSlots, 2))
		for slot in range(0, testBench.nbSlots):
			positionersArmLengths[slot] = [testBench.positioners[slot].model.lengthAlpha,testBench.positioners[slot].model.lengthBeta]

		#Store the results
		for slot in range(0, nbSlots):
			testResults[slot].testBenchName 		= testBench.benchName
			testResults[slot].positionerID 			= int(testBench.positioners[slot].ID)
			testResults[slot].slotID 				= int(testBench.slotIDs[slot])
			testResults[slot].slotsCenters			= np.array([testBench.positioners[slot].model.centerX, testBench.positioners[slot].model.centerY])
			testResults[slot].positionersArmLengths = positionersArmLengths[slot]
			testResults[slot].targets				= targets[slot]
			testResults[slot].targetsErrors			= targetsErrors[slot]
			testResults[slot].sortedCommands		= sortedCommands[slot]
			testResults[slot].realAngles			= realAngles[slot]
			testResults[slot].sortedCentroidsXY		= sortedCentroidsXY[slot]
			testResults[slot].nbCorrections 		= nbCorrections[slot]
			testResults[slot].testParameters		= testParameters
			testResults[slot].config 				= config
			testResults[slot].requirements 			= testBench.positioners[slot].requirements
			testResults[slot].completionTime 		= time.strftime("%Y-%m-%d-%Hh%Mm%Ss", time.localtime(time.time()))
			testResults[slot].runDone 				= True
	
	except errors.Error as e:
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
		raise errors.CalibrationError("Test run failed")

def calc(testResults):
	nbSlots = len(testResults)

	for slot in range(0,nbSlots):
		if (not testResults[slot].runDone) or testResults[slot].calcDone:
			continue

		nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults[slot].targets.shape
		modelError 		= np.full((nbRepetitions, nbTargets, maxNbMoves, 7), np.nan) #Total, X, Y, AcrossAlpha, AlongAlpha, Acrossbeta, AlongBeta
		repeatability 	= np.full((nbTargets, 7), np.nan) #Total, X, Y, AcrossAlpha, AlongAlpha, Acrossbeta, AlongBeta
		totalNbPoints  	= nbTargets*nbRepetitions

		#Compute model error
		#AcrossErr, AlongErr
		centerX 	= testResults[slot].slotsCenters[0]
		centerY 	= testResults[slot].slotsCenters[1]	
		for target in range(0,nbTargets):
			for repetition in range(0,nbRepetitions):
				for move in range(0, maxNbMoves):
					modelError[repetition,target,move,0] = testResults[slot].targetsErrors[repetition,target,move,2]
					modelError[repetition,target,move,1] = testResults[slot].targetsErrors[repetition,target,move,0]
					modelError[repetition,target,move,2] = testResults[slot].targetsErrors[repetition,target,move,1]
					mesX 		= testResults[slot].sortedCentroidsXY[repetition, target, move, 0]
					mesY 		= testResults[slot].sortedCentroidsXY[repetition, target, move, 1]
					errX 		= modelError[repetition, target, move, 1]
					errY 		= modelError[repetition, target, move, 2]

					angleCenterToMes 	= np.arctan2(mesX-centerX, mesY-centerY)
					angleBetaEnd 		= np.mod((testResults[slot].realAngles[repetition, target, move, 0]+testResults[slot].realAngles[repetition, target, move, 1]), 2*np.pi)
					angleMesToErr 		= np.arctan2(errX, errY)

					projectionAngleAlpha = np.mod(angleMesToErr-angleCenterToMes, 2*np.pi)
					projectionAngleBeta = np.mod(angleMesToErr-angleBetaEnd, 2*np.pi)

					#error across and along alpha
					modelError[repetition, target, move, 3] = -modelError[repetition, target, move, 0]*np.cos(projectionAngleAlpha)
					modelError[repetition, target, move, 4] = -modelError[repetition, target, move, 0]*np.sin(projectionAngleAlpha)
					if (angleMesToErr-testResults[slot].realAngles[repetition, target, move, 0]) < 0 and (angleMesToErr-testResults[slot].realAngles[repetition, target, move, 0]) > -np.pi:
						modelError[repetition, target, move, 3] = -modelError[repetition, target, move, 3]
					
					#error across and along beta
					modelError[repetition, target, move, 5] = -modelError[repetition, target, move, 0]*np.cos(projectionAngleBeta)
					modelError[repetition, target, move, 6] = -modelError[repetition, target, move, 0]*np.sin(projectionAngleBeta)

		#Compute repeatability
		#repeatability #Total, X, Y, Across, Along
			if nbRepetitions > 1:
				move = 0
				meanPointX = np.nanmean(testResults[slot].sortedCentroidsXY[:, target, move, 0])
				meanPointY = np.nanmean(testResults[slot].sortedCentroidsXY[:, target, move, 1])

				for repetition in range(0,nbRepetitions):
					mesX 		= testResults[slot].sortedCentroidsXY[repetition, target, move, 0]
					mesY 		= testResults[slot].sortedCentroidsXY[repetition, target, move, 1]

					repeatabilityX = meanPointX-mesX
					repeatabilityY = meanPointY-mesY
					repeatabilityTotal = np.sqrt(repeatabilityX**2+repeatabilityY**2)

					repeatability[target, 0] = repeatabilityTotal
					repeatability[target, 1] = repeatabilityX
					repeatability[target, 2] = repeatabilityY

					angleCenterToMes 	= np.arctan2(mesX-centerX, mesY-centerY)
					angleBetaEnd 		= np.mod((testResults[slot].realAngles[repetition, target, move, 0]+testResults[slot].realAngles[repetition, target, move, 1]), 2*np.pi)
					angleMesToErr 		= np.arctan2(repeatabilityX, repeatabilityY)

					projectionAngleAlpha = np.mod(angleMesToErr-angleCenterToMes, 2*np.pi)
					projectionAngleBeta = np.mod(angleMesToErr-angleBetaEnd, 2*np.pi)

					#error across and along alpha
					repeatability[target, 3] = -repeatability[target, 0]*np.cos(projectionAngleAlpha)
					repeatability[target, 4] = -repeatability[target, 0]*np.sin(projectionAngleAlpha)
					if (angleMesToErr-testResults[slot].realAngles[repetition, target, move, 0]) < 0 and (angleMesToErr-testResults[slot].realAngles[repetition, target, move, 0]) > -np.pi: #check if the solution to take is right-handed or left-handed
						repeatability[target, 3] = -repeatability[target, 3]
					
					#error across and along beta
					repeatability[target, 5] = -repeatability[target, 0]*np.cos(projectionAngleBeta)
					repeatability[target, 6] = -repeatability[target, 0]*np.sin(projectionAngleBeta)
		
		completedTargets = 0
		targetConvergeance = []
		for move in range(0, maxNbMoves):
			for repetition in range(0, nbRepetitions):
				for target in range(0, nbTargets):
					if 1000*modelError[repetition,target,move,0] <= testResults[slot].testParameters.desiredTargetError:
						completedTargets += 1
			targetConvergeance.append(completedTargets/totalNbPoints*100)

		mesRMSError1stMove			= 1000*mm.nanrms(np.ravel(modelError[:,:,0,0]))
		mesRMSRepeatability1stMove 	= 1000*mm.nanrms(np.ravel(repeatability[:,0]))
		mesTargetConvergeance 		= targetConvergeance
		mesMaxNbMoves				= np.max(np.ravel(testResults[slot].nbCorrections[:,:]))+1

		#store the results
		testResults[slot].mesRMSError1stMove.append(		mesRMSError1stMove)
		testResults[slot].mesRMSRepeatability1stMove.append(mesRMSRepeatability1stMove)
		testResults[slot].mesTargetConvergeance.append(		mesTargetConvergeance)
		testResults[slot].mesMaxNbMoves.append(				mesMaxNbMoves)
		testResults[slot].modelError 						= modelError
		testResults[slot].repeatability 					= repeatability
		testResults[slot].calcDone 							= True

def plot(testResults, config):
	if not config.plotResults:
		return 

	nbSlots = len(testResults)

	figID = np.array([np.ones((DEFINES.PLOT_TEST_NB_SUBPLOTS)).astype(np.uint8),np.linspace(1,DEFINES.PLOT_TEST_NB_SUBPLOTS,DEFINES.PLOT_TEST_NB_SUBPLOTS).astype(np.uint8)])

	titleFontsize 	= [DEFINES.PLOT_TITLE_FONTSIZE_SINGLE, DEFINES.PLOT_TITLE_FONTSIZE_OVERVIEW]
	labelFontsize 	= [DEFINES.PLOT_AXES_LABEL_FONTSIZE_SINGLE, DEFINES.PLOT_AXES_LABEL_FONTSIZE_OVERVIEW]
	ticksFontsize 	= [DEFINES.PLOT_AXES_TICKS_FONTSIZE_SINGLE, DEFINES.PLOT_AXES_TICKS_FONTSIZE_OVERVIEW]
	figNbRows 		= [DEFINES.PLOT_TEST_NB_ROW_SUBPLOTS_SINGLE, DEFINES.PLOT_TEST_NB_ROW_SUBPLOTS_OVERVIEW]
	figNbCols 		= [DEFINES.PLOT_TEST_NB_COL_SUBPLOTS_SINGLE, DEFINES.PLOT_TEST_NB_COL_SUBPLOTS_OVERVIEW]
	figKeepOpen 	= [DEFINES.PLOT_KEEP_FIGURE_OPEN_SINGLE, DEFINES.PLOT_KEEP_FIGURE_OPEN_OVERVIEW]
	figSize 		= [DEFINES.PLOT_FIGURE_SIZE_SINGLE, DEFINES.PLOT_FIGURE_SIZE_OVERVIEW]
	lineWidth		= [DEFINES.PLOT_LINEWIDTH_SINGLE, DEFINES.PLOT_LINEWIDTH_OVERVIEW]

	plotProperties	= customPlot.plotProperties
	nbPlotsPerGraph = len(titleFontsize)

	for slot in range(0,nbSlots):
		nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults[slot].targets.shape

		figuresToPlot = []

		overviewPath = config.get_current_overview_folder()
		individualFigurePath = config.get_current_figure_folder(testResults[slot].positionerID)

		
		overviewFile = config.get_overwiew_filename(testResults[slot].positionerID)
		overviewFile += '_test'+config.overviewExtension
		
		os.makedirs(overviewPath, exist_ok=True)
		os.makedirs(individualFigurePath, exist_ok=True)

		for i in range(0,nbPlotsPerGraph):
			for j in range(0,DEFINES.PLOT_TEST_NB_SUBPLOTS):
				
				if figNbRows[i] == DEFINES.PLOT_TEST_NB_ROW_SUBPLOTS_SINGLE and figNbCols[i] == DEFINES.PLOT_TEST_NB_COL_SUBPLOTS_SINGLE:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Plotting positioner {testResults[slot].positionerID}, {plotProperties[j][DEFINES.PLOT_TITLE_ID]}')
				else:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Plotting positioner {testResults[slot].positionerID}, [Overview] {plotProperties[j][DEFINES.PLOT_TITLE_ID]}')

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
				plotProperties[j][DEFINES.PLOT_FUNC_ID](drawingAxis, lineWidth[i], testResults[slot])
				
				#Save the previous figure if all the subplots were done
				if len(figuresToPlot) > 0 and (figID[i,j] >= figNbRows[i]*figNbCols[i] or j >= DEFINES.PLOT_TEST_NB_SUBPLOTS-1):
					if figNbRows[i] == DEFINES.PLOT_TEST_NB_ROW_SUBPLOTS_SINGLE and figNbCols[i] == DEFINES.PLOT_TEST_NB_COL_SUBPLOTS_SINGLE:
						figureFileName = 'Test_'+str(i)+str(j)+'_'+plotProperties[j][DEFINES.PLOT_TITLE_ID]+testResults[slot].config.figureExtension
						figureFileName=figureFileName.replace(" ", "_")
						figurePath = individualFigurePath

						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName))
					else:
						figurePath = overviewPath
						figureFileName = overviewFile
						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName)) #save in the overviews

						figurePath = individualFigurePath
						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName)) #save in the individual positioner folder

						if testResults[slot].config.nbTestingLoops > 1:
							figurePath = config.get_current_positioner_folder(testResults[slot].positionerID, includeLifetimeIteration = False)
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

def plot_lifetime(testResults, config):
	if not config.plotResults or config.nbTestingLoops < 2:
		return 

	nbSlots = len(testResults)

	figID = np.array([np.ones((DEFINES.PLOT_TEST_NB_SUBPLOTS_LIFETIME)).astype(np.uint8),np.linspace(1,DEFINES.PLOT_TEST_NB_SUBPLOTS_LIFETIME,DEFINES.PLOT_TEST_NB_SUBPLOTS_LIFETIME).astype(np.uint8)])

	titleFontsize 	= [DEFINES.PLOT_TITLE_FONTSIZE_SINGLE, DEFINES.PLOT_TITLE_FONTSIZE_LIFETIME]
	labelFontsize 	= [DEFINES.PLOT_AXES_LABEL_FONTSIZE_SINGLE, DEFINES.PLOT_AXES_LABEL_FONTSIZE_LIFETIME]
	ticksFontsize 	= [DEFINES.PLOT_AXES_TICKS_FONTSIZE_SINGLE, DEFINES.PLOT_AXES_TICKS_FONTSIZE_LIFETIME]
	figNbRows 		= [DEFINES.PLOT_TEST_NB_ROW_SUBPLOTS_SINGLE, DEFINES.PLOT_TEST_NB_ROW_SUBPLOTS_LIFETIME]
	figNbCols 		= [DEFINES.PLOT_TEST_NB_COL_SUBPLOTS_SINGLE, DEFINES.PLOT_TEST_NB_COL_SUBPLOTS_LIFETIME]
	figKeepOpen 	= [DEFINES.PLOT_KEEP_FIGURE_OPEN_SINGLE, DEFINES.PLOT_KEEP_FIGURE_OPEN_LIFETIME]
	figSize 		= [DEFINES.PLOT_FIGURE_SIZE_SINGLE, DEFINES.PLOT_FIGURE_SIZE_LIFETIME]
	lineWidth		= [DEFINES.PLOT_LINEWIDTH_SINGLE, DEFINES.PLOT_LINEWIDTH_LIFETIME]

	plotProperties	= customPlot.plotPropertiesLifetime
	nbPlotsPerGraph = len(titleFontsize)

	for slot in range(0,nbSlots):
		nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults[slot].targets.shape

		figuresToPlot = []

		individualFigurePath = config.get_current_figure_folder(testResults[slot].positionerID)

		
		multipleFigureFile = 'Lifetime_'+config.get_overwiew_filename(testResults[slot].positionerID)
		multipleFigureFile += '_test'+config.overviewExtension
		
		os.makedirs(individualFigurePath, exist_ok=True)

		for i in range(0,nbPlotsPerGraph):
			for j in range(0,DEFINES.PLOT_TEST_NB_SUBPLOTS_LIFETIME):
				
				if figNbRows[i] == DEFINES.PLOT_TEST_NB_ROW_SUBPLOTS_SINGLE and figNbCols[i] == DEFINES.PLOT_TEST_NB_COL_SUBPLOTS_SINGLE:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Plotting positioner {testResults[slot].positionerID}, {plotProperties[j][DEFINES.PLOT_TITLE_ID]}')
				else:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Plotting positioner {testResults[slot].positionerID}, [Lifetime] {plotProperties[j][DEFINES.PLOT_TITLE_ID]}')

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
				plotProperties[j][DEFINES.PLOT_FUNC_ID](drawingAxis, lineWidth[i], testResults[slot])
				
				#Save the previous figure if all the subplots were done
				if len(figuresToPlot) > 0 and (figID[i,j] >= figNbRows[i]*figNbCols[i] or j >= DEFINES.PLOT_TEST_NB_SUBPLOTS_LIFETIME-1):
					if figNbRows[i] == DEFINES.PLOT_TEST_NB_ROW_SUBPLOTS_SINGLE and figNbCols[i] == DEFINES.PLOT_TEST_NB_COL_SUBPLOTS_SINGLE:
						figureFileName = 'Lifetime_test_'+str(i)+str(j)+'_'+plotProperties[j][DEFINES.PLOT_TITLE_ID]+testResults[slot].config.figureExtension
						figureFileName=figureFileName.replace(" ", "_")
						figurePath = individualFigurePath

						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName))
					else:
						figureFileName = multipleFigureFile
						figurePath = individualFigurePath
						figuresToPlot[-1].savefig(os.path.join(figurePath,figureFileName)) #save in the individual positioner folder

						if testResults[slot].config.nbTestingLoops > 1:
							figurePath = config.get_current_positioner_folder(testResults[slot].positionerID, includeLifetimeIteration = False)
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