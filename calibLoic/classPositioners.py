#cython: language_level=3
import numpy as np
import json
import os
import copy
import DEFINES
import logger as log
from scipy import interpolate
import errors

class PositionerPhysics:
	__slots__ = (	'lengthAlpha',\
					'lengthBeta',\
					'metrologyToScience',\
					'alphaReductionRatio',\
					'betaReductionRatio',\
					'alphaAxisRange',\
					'betaAxisRange',\
					'maxRpmAlpha',\
					'maxRpmBeta',\
					'maxCurrentAlpha',\
					'maxCurrentBeta',\
					'incrementsPerRotation',\
					'movementSafetyDelay')
	
	def __init__(self):
		self.lengthAlpha 						= 7.4			# [mm]
		self.lengthBeta 						= 14.35			# [mm]
		self.metrologyToScience					= 0.65			# [mm]
		self.alphaReductionRatio				= 1024
		self.betaReductionRatio					= 1024

		# self.lengthAlpha 						= 7.4			# [mm]
		# self.lengthBeta 						= 13.00			# [mm]
		# self.metrologyToScience				= 2.00			# [mm]
		# self.alphaReductionRatio				= 879
		# self.betaReductionRatio				= 1024

		self.alphaAxisRange						= [-4, 364] 	# [deg]
		self.betaAxisRange						= [-4, 364] 	# [deg]

		self.maxRpmAlpha						= 4200			# [RPM] #5000
		self.maxRpmBeta							= 4200			# [RPM] #8000
		self.maxCurrentAlpha					= 100 			# [%] 	#70
		self.maxCurrentBeta 					= 100 			# [%]

		self.incrementsPerRotation				= 2**30 		# steps for one rotation at the output
		self.movementSafetyDelay				= 0.03			# [100*%] Additionnal waiting time for a movement to finish
	
	def load(self,fileName):
		if not os.path.exists(fileName):
			return False
			
		#Load all the data in the file, exculding the fileInfos
		with open(os.path.join(fileName),'r') as inFile:
			variablesToLoad=json.load(inFile)
			for key in variablesToLoad.keys():
				if key not in type(self).__slots__:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING,1,'Unexpected data was encountered during the loading of the positioner physics')
					return False
				setattr(self, key, variablesToLoad[key])
				
		return True

	def save(self, filePath, fileName):
		variablesToSave = {}
		for slots in [getattr(cls, '__slots__', []) for cls in type(self).__mro__]:
			for attr in slots:
				variablesToSave[attr] = getattr(self, attr)

		os.makedirs(filePath, exist_ok=True)
		with open(os.path.join(filePath, fileName),'w') as outFile:
			json.dump(variablesToSave, outFile, separators = (',\n',': '))


class PositionerRequirements:
	__slots__ = (	'nominalAlphaLength',\
					'nominalBetaLength',\
					'maxAlphaLengthDeviation',\
					'maxBetaLengthDeviation',\
					'maxPosError',\
					'rmsPosRepeatability',\
					'maxHysteresis',\
					'maxNonLinearity',\
					'maxNonLinearityDerivative',\
					'rmsAlignmentError',\
					'rmsShouldAlignmentError',\
					'maxAlignmentError',\
					'tilts',\
					'maxRoundnessDeviation',\
					'maxShouldRoundnessDeviation',\
					'minHallAccuracy',\
					'minHallRepeatability',\
					'targetConvergeance',\
					'maxNbMoves')

	def __init__(self):
		self.nominalAlphaLength					= 7.4		# [um] nominal length
		self.nominalBetaLength					= 15		# [mm] nominal length
		self.maxAlphaLengthDeviation			= 0.1		# [mm] max, plus and minus
		self.maxBetaLengthDeviation				= 0.1		# [um] max, plus and minus
		self.maxPosError						= 50		# [um] max
		self.rmsPosRepeatability				= 2.5		# [um] rms
		self.maxHysteresis						= 0.3		# [°] max
		self.maxNonLinearity					= 0.6		# [°] max
		self.maxNonLinearityDerivative			= 0.15		# [°out/°commanded] max, plus and minus
		self.rmsAlignmentError					= 0.2		# [deg] allowable rms alignment error
		self.rmsShouldAlignmentError			= 0.1		# [deg] allowable rms alignment error (bonus)
		self.maxAlignmentError					= 0.4		# [deg] allowable max alignment error
		self.tilts								= [0, 0, 0] # [deg] alpha, beta, ferrule
		self.maxRoundnessDeviation				= 15		# [um] max, plus and minus
		self.maxShouldRoundnessDeviation		= 7			# [um] max, plus and minus (bonus)
		self.minHallAccuracy					= 2			# [°]
		self.minHallRepeatability				= 0.5		# [°]
		self.targetConvergeance 				= 100 		# [%] of target to be reached
		self.maxNbMoves							= 3 		# The target must be reached in this amount of moves max

	def load(self,fileName):
		#Load all the data in the file, exculding the fileInfos
		try:
			with open(os.path.join(fileName),'r') as inFile:
				variablesToLoad=json.load(inFile)
				for key in variablesToLoad.keys():
					if key in type(self).__slots__:
						setattr(self, key, variablesToLoad[key])
					else:
						log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING,1,f'Unexpected data was encountered during the loading of the positioner requirements. Faulty key: {key}')
						if DEFINES.RAISE_ERROR_ON_UNEXPECTED_KEY:
							raise errors.IOError('Unexpected data was encountered during the loading of the positioner requirements') from None
						
		except OSError:
			raise errors.IOError('The positioner requirements file could not be found') from None

	def save(self, filePath, fileName):
		variablesToSave = {}
		for slots in [getattr(cls, '__slots__', []) for cls in type(self).__mro__]:
			for attr in slots:
				variablesToSave[attr] = getattr(self, attr)

		os.makedirs(filePath, exist_ok=True)
		with open(os.path.join(filePath, fileName),'w+') as outFile:
			json.dump(variablesToSave, outFile, separators = (',\n',': '))


class PositionerModel:
	__slots__ = (	'lengthAlpha',\
					'lengthBeta',\
					'metrologyToScience',\
					'offsetAlpha',\
					'offsetBeta',\
					'centerX',\
					'centerY',\
					'nonLinearityAlpha',\
					'nonLinearityBeta',\
					'eccentricityAlpha',\
					'eccentricityBeta',\
					'getCorrectedAlpha',\
					'getCorrectedBeta')

	def __init__(self, positionerPhysics = PositionerPhysics()):
		self.lengthAlpha 						= copy.deepcopy(positionerPhysics.lengthAlpha)
		self.lengthBeta 						= copy.deepcopy(positionerPhysics.lengthBeta)
		self.metrologyToScience					= copy.deepcopy(positionerPhysics.metrologyToScience)
		self.offsetAlpha 						= -6.1*np.pi/180	# [rad]
		self.offsetBeta 						= -6.8*np.pi/180	# [rad]
		self.centerX							= 0			# [mm]
		self.centerY 							= 0			# [mm]
		self.nonLinearityAlpha 					= np.array([])
		self.nonLinearityBeta 					= np.array([])
		self.eccentricityAlpha					= np.array([])
		self.eccentricityBeta					= np.array([])
		self.getCorrectedAlpha					= None
		self.getCorrectedBeta					= None


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
					elif key == 'alphaCommands':
						alphaCommands = np.array(variablesToLoad[key])
					elif key == 'betaCommands':
						betaCommands = np.array(variablesToLoad[key])
					elif key == 'alphaMeasures':
						alphaMeasures = np.array(variablesToLoad[key])
					elif key == 'betaMeasures':
						betaMeasures = np.array(variablesToLoad[key])
					else:
						log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING,1,f'Unexpected data was encountered during the loading of the positioner model. Faulty key: {key}')
						if DEFINES.RAISE_ERROR_ON_UNEXPECTED_KEY:
							raise errors.IOError('Unexpected data was encountered during the loading of the positioner model') from None
			
			self.getCorrectedAlpha 	= interpolate.interp1d(alphaCommands, alphaMeasures, kind='linear', fill_value='extrapolate')
			self.getCorrectedBeta 	= interpolate.interp1d(betaCommands, betaMeasures, kind='linear', fill_value='extrapolate')
					
		except OSError:
			raise errors.IOError('The positioner model file could not be found') from None

				
	def save(self, filePath, fileName):
		variablesToSave = {}

		variablesToSave['lengthAlpha']			= self.lengthAlpha
		variablesToSave['lengthBeta']			= self.lengthBeta
		variablesToSave['metrologyToScience']	= self.metrologyToScience
		variablesToSave['offsetAlpha']			= self.offsetAlpha
		variablesToSave['offsetBeta']			= self.offsetBeta
		variablesToSave['centerX']				= self.centerX
		variablesToSave['centerY']				= self.centerY
		variablesToSave['nonLinearityAlpha']	= self.nonLinearityAlpha.tolist()
		variablesToSave['nonLinearityBeta']		= self.nonLinearityBeta.tolist()
		variablesToSave['eccentricityAlpha']	= self.eccentricityAlpha.tolist()
		variablesToSave['eccentricityBeta']		= self.eccentricityBeta.tolist()
		variablesToSave['alphaCommands']		= self.getCorrectedAlpha.x.tolist()
		variablesToSave['betaCommands']			= self.getCorrectedBeta.x.tolist()
		variablesToSave['alphaMeasures']		= self.getCorrectedAlpha.y.tolist()
		variablesToSave['betaMeasures']			= self.getCorrectedBeta.y.tolist()

		os.makedirs(filePath, exist_ok=True)
		with open(os.path.join(filePath, fileName),'w+') as outFile:
			json.dump(variablesToSave, outFile, separators = (',\n',': '))

	def clear(self,positionerPhysics = PositionerPhysics()):
		self.lengthAlpha 						= copy.deepcopy(positionerPhysics.lengthAlpha)
		self.lengthBeta 						= copy.deepcopy(positionerPhysics.lengthBeta)
		self.offsetAlpha 						= -6.1*np.pi/180	# [rad]
		self.offsetBeta 						= -6.8*np.pi/180	# [rad]
		self.centerX							= 0			# [mm]
		self.centerY 							= 0			# [mm]
		self.nonLinearityAlpha 					= np.array([])
		self.nonLinearityBeta 					= np.array([])
		self.eccentricityAlpha					= np.array([])
		self.eccentricityBeta					= np.array([])
		self.getCorrectedAlpha					= None
		self.getCorrectedBeta					= None

class Positioner:
	__slots__ = (	'ID',\
					'benchSlot',\
					'model',\
					'physics',\
					'requirements',\
					'initialized',\
					'calibrated')

	def __init__(self, model = PositionerModel(), physics = PositionerPhysics(), requirements = PositionerRequirements()):
		self.ID 								= None
		self.benchSlot							= None
		self.model 								= copy.deepcopy(model)
		self.physics 							= copy.deepcopy(physics)
		self.requirements 						= copy.deepcopy(requirements)
		self.initialized						= False
		self.calibrated							= False

	def change_model(self, newModel):
		self.model = copy.deepcopy(newModel)

	def change_physics(self, newPhysics):
		self.physics = copy.deepcopy(newPhysics)

	def change_requirements(self, newRequirements):
		self.requirements = copy.deepcopy(newRequirements)

	def init(self, ID, canComHandle, waitInitComplete):
		self.ID = ID

		#init the datums
		canComHandle.CAN_write(self.ID,'initdatum', [])

		if waitInitComplete:
			#wait until the initialization is complete
			while not self.datum_initialized:
				time.sleep(0.005)

			#Set the current position as the hardstop position
			initial_position = {'Actual_alpha_pos': int(round(self.physics.incrementsPerRotation*self.model.offsetAlpha*180/np.pi/(DEFINES.DEGREES_PER_ROTATION),0)), \
								'Actual_beta_pos': int(round(self.physics.incrementsPerRotation*self.model.offsetBeta*180/np.pi/(DEFINES.DEGREES_PER_ROTATION),0))}
			canComHandle.CAN_write(self.ID,'set_actual_position', initial_position)

			self.initialized = True

	def stop(self, canComHandle):
		if self.ID == None or self.initialized == False:
			return

		#stop the trajectory
		canComHandle.CAN_write(self.ID,'stoptrajectory', [])

		#Stop the current
		current = {'currentAlpha': int(0), 'currentBeta': int(0)}
		canComHandle.CAN_write(self.ID,'setopenloopcurrent', current)

	def is_moving(self, canComHandle):
		if self.ID == None or self.initialized == False:
			return False

		status	= canComHandle.CAN_write(self.ID,'statusrequest', [])
		return not bool(status[0]&canComHandle._OPT.STREG.DISPLACEMENT_COMPLETED)

	def datum_initialized(self, canComHandle):
		if self.ID == None:
			return False

		status	= canComHandle.CAN_write(self.ID,'statusrequest', [])
		return bool(status[0]&canComHandle._OPT.STREG.DATUM_INITIALIZED)

	def start_init_datum(self,canComHandle):
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to initialize the datums on an uninitialized positioner")

		canComHandle.CAN_write(self.ID,'initdatum', [])

	def set_speed(self, canComHandle, speedAlpha, speedBeta, respectPhysics = True):
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to set speed on an uninitialized positioner")

		#Set the speed
		if 	respectPhysics and \
			(speedAlpha < 0 or speedAlpha > self.physics.maxRpmAlpha or\
			speedBeta < 0 or speedBeta > self.physics.maxRpmBeta):
			raise error.OutOfRangeError("Trying to set out of range speed on positioner {self.ID:04d}")

		motor_rpm = {'SpeedAlpha': int(speedAlpha), 'SpeedBeta': int(speedBeta)}
	
		canComHandle.CAN_write(self.ID,'set_speed', motor_rpm)

	def set_current(self, canComHandle, currentAlpha, currentBeta, respectPhysics = True):
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to set current on an uninitialized positioner")

		#Set the current
		if 	respectPhysics and \
			(currentAlpha < 0 or currentAlpha > self.physics.maxCurrentAlpha or\
			currentBeta < 0 or currentBeta > self.physics.maxCurrentBeta):
			raise error.OutOfRangeError("Trying to set out of range current on positioner {self.ID:04d}")

		current = {'currentAlpha': int(currentAlpha), 'currentBeta': int(currentBeta)}
	
		canComHandle.CAN_write(self.ID,'setopenloopcurrent', current)

	def goto_position(self, canComHandle, angleAlpha, angleBeta, respectPhysics = True): #Angles in degrees
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to move an uninitialized positioner")

		if 	respectPhysics and \
			(angleAlpha < self.physics.alphaAxisRange[0] or angleAlpha > self.physics.alphaAxisRange[1] or\
			angleBeta < self.physics.betaAxisRange[0] or angleBeta > self.physics.betaAxisRange[1]):
			raise error.OutOfRangeError("Trying to go to an out of range position on positioner {self.ID:04d}")

		#Go to the specified position. Returns the time taken by the positioner to perform the move.
		data={'R1Steps': int(round(self.physics.incrementsPerRotation*angleAlpha/(DEFINES.DEGREES_PER_ROTATION),0)), 'R2Steps': int(round(self.physics.incrementsPerRotation*angleBeta/(DEFINES.DEGREES_PER_ROTATION),0))}
		
		response=canComHandle.CAN_write(self.ID,'gotoposition_speed', data)
		return max(response)*(1+self.physics.movementSafetyDelay)

	def set_position(self, canComHandle, angleAlpha, angleBeta):
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to set position on an uninitialized positioner")

		#Go to the specified position. Returns the time taken by the positioner to perform the move.
		initial_position = {'Actual_alpha_pos': int(round(self.physics.incrementsPerRotation*angleAlpha/(DEFINES.DEGREES_PER_ROTATION),0)), 'Actual_beta_pos': int(round(self.physics.incrementsPerRotation*angleBeta/(DEFINES.DEGREES_PER_ROTATION),0))}

		canComHandle.CAN_write(self.ID,'set_actual_position', initial_position)

	def set_position_offset(self, canComHandle):
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to set offset on an uninitialized positioner")

		# if self.model.getCorrectedAlpha is not None and self.model.getCorrectedBeta is not None:
		#Get the offsets
		targetAlpha = self.model.offsetAlpha
		targetBeta = self.model.offsetBeta

		#Set the new reference position
		initial_position = {'Actual_alpha_pos': int(round(self.physics.incrementsPerRotation*targetAlpha*180/np.pi/(DEFINES.DEGREES_PER_ROTATION),0)), 'Actual_beta_pos': int(round(self.physics.incrementsPerRotation*targetBeta*180/np.pi/(DEFINES.DEGREES_PER_ROTATION),0))}
		canComHandle.CAN_write(self.ID,'set_actual_position', initial_position)

		#Update the model parameters
		# self.model.getCorrectedAlpha.y = np.subtract(self.model.getCorrectedAlpha.y, targetAlpha)
		# self.model.nonLinearityAlpha = np.subtract(self.model.nonLinearityAlpha, targetAlpha)
		self.model.offsetAlpha = 0

		# self.model.getCorrectedBeta.y = np.subtract(self.model.getCorrectedBeta.y, targetBeta)
		# self.model.nonLinearityBeta = np.subtract(self.model.nonLinearityBeta, targetBeta)
		self.model.offsetBeta = 0

	def get_hall_position(self, canComHandle):
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to retreive hall position from an uninitialized positioner")

		#Get the current position
		response = canComHandle.CAN_write(self.ID,'get_pos_hall', [])
		return np.divide(response,self.physics.incrementsPerRotation/DEFINES.DEGREES_PER_ROTATION)

	def get_steps_from_angle(self, canComHandle, angle):
		return self.physics.incrementsPerRotation*angle/DEFINES.DEGREES_PER_ROTATION

	def get_angle_from_steps(self, canComHandle, steps):
		return DEFINES.DEGREES_PER_ROTATION*steps/self.physics.incrementsPerRotation

	def get_status(self, canComHandle):
		pass
	
	def calibrate_motor(self, canComHandle):
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to start motor calibration on an uninitialized positioner")

		#Start the motor calibration
		response = canComHandle.CAN_write(self.ID,'start_motor_calibration', [])
		
	def get_motor_calibration_error(self, canComHandle):
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to retreive motor calibration error from an uninitialized positioner")

		#Get the motor calibration error
		response = canComHandle.CAN_write(self.ID,'get_motor_calibration_error', [])
		return np.divide(response,self.physics.incrementsPerRotation/DEFINES.DEGREES_PER_ROTATION)

	def calibrate_cogging_torque(self, canComHandle):
		if self.ID == None or self.initialized == False:
			raise error.PositionerError("Trying to start cogging torque calibration on an uninitialized positioner")

		#Start the cogging calibration
		canComHandle.CAN_write(self.ID,'start_cogging_calibration', [])