#cython: language_level=3
import classCamera as cam
import classCanCom as com
import classPositioners as pos
import copy
import computeCentroid as cc
import numpy as np
import os
from scipy import io
import glob
import json
import time
import logger as log
import DEFINES
import errors
from miscmath import decompose_time

class TestBench:
	__slots__ = (	'benchName',\
					'XYCameraID',\
					'TiltCameraID',\
					'canUSBSerialNo',\
					'cameraXY',\
					'cameraTilt',\
					'canUSB',\
					'maxSlots',\
					'nbSlots',\
					'slotIDs',\
					'slotsCenters',\
					'originalSlotsCenters',\
					'positioners',\
					'slotsExposures',\
					'recalibrateCenters')

	def __init__(self):
		self.benchName 			= 'Undefined testbench'

		self.XYCameraID			= None
		self.TiltCameraID		= None
		self.canUSBSerialNo		= ''

		self.cameraXY			= None
		self.cameraTilt			= None
		self.canUSB				= com.COM_handle()

		self.nbSlots 			= 1
		self.maxSlots 			= self.nbSlots
		self.slotsCenters 		= np.zeros((self.nbSlots, 2))
		self.originalSlotsCenters = np.zeros((self.nbSlots, 2))
		self.recalibrateCenters = True
		self.clear_slots()

	def init_cameraXY(self, pathToFile):
		if self.XYCameraID is None:
			return

		try:
			self.cameraXY = cam.Camera(DEFINES.PC_CAMERA_TYPE_XY, self.XYCameraID)
			self.cameraXY.setDistortionCorrection(pathToFile)
		except Exception as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise e from None

	def init_cameraTilt(self, pathToFile):
		if self.TiltCameraID is None:
			return

		try:
			self.cameraTilt = cam.Camera(DEFINES.PC_CAMERA_TYPE_TILT, self.TiltCameraID)
			self.cameraTilt.setDistortionCorrection(pathToFile)
		except Exception as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise e from None

	def init_canUSB(self):
		if self.canUSBSerialNo is '':
			return

		try:
			self.canUSB.init(self.canUSBSerialNo)
		except errors.CANError as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise e from None

	def init_handles(self, config):
		try:
			self.init_cameraXY(config)
			self.init_cameraTilt(config)
			self.init_canUSB()
		except (errors.CANError, errors.CameraError):
			raise errors.Error("Handles initialization failed")

	def close_cameraXY(self):
		if self.cameraXY is not None:
			self.cameraXY.close()

	def close_cameraTilt(self):
		if self.cameraTilt is not None:
			self.cameraTilt.close()

	def close_canUSB(self):
		if self.canUSB is not None:
			self.canUSB.close()

	def close_handles(self):
		self.close_cameraXY()
		self.close_cameraTilt()
		self.close_canUSB()

	def assign_positioner_to_slot(self, slotNumber, positioner):
		if slotNumber < self.nbSlots:
			self.positioners[slotNumber] = positioner

	def del_positioner_in_slot(self, slotNumber):
		if slotNumber < self.nbSlots:
			self.positioners[slotNumber] = -1
	
	def autosearch(self, filePath, testBenchName = '', canUSBSerial = ''):
		# Open every testbench file and search a corresponding testbench. priority is name, then canusb, and finally any connected xy camera

		for fileName in glob.glob(os.path.join(filePath, f'*{DEFINES.PP_TESTBENCH_EXTENSION}')):
			testBenchData 		= io.loadmat(fileName)

			#Check if camera ID in testBench file corresponds to any connected camera
			if testBenchName is not '':
				if testBenchName == testBenchData['benchName']:
					return fileName
			elif canUSBSerial is not '':
				if canUSBSerial == testBenchData['canUSBSerialNo']:
					return fileName
			else:
				if testBenchData['XYCameraID'] in cam.getAvailableCameraIDs():
					return fileName

		return ''

	def load(self,fileName):
		#Load all the data in the file, exculding the fileInfos
		try:
			with open(os.path.join(fileName),'r') as inFile:
				variablesToLoad=json.load(inFile)
				for key in variablesToLoad.keys():
					if key in type(self).__slots__:
						setattr(self, key, variablesToLoad[key])
					else:
						log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING,1,f'Unexpected data was encountered during the loading of the testbench parameters. Faulty key: {key}')
						if DEFINES.RAISE_ERROR_ON_UNEXPECTED_KEY:
							raise errors.IOError('Unexpected data was encountered during the loading of the testbench parameters') from None
			
			self.slotsCenters 			= np.array(self.slotsCenters)
			self.nbSlots 				= len(self.slotsCenters[:,0])
			self.maxSlots 				= copy.deepcopy(self.nbSlots)
			self.originalSlotsCenters 	= copy.deepcopy(self.slotsCenters)

			self.clear_slots()

		except OSError:
			raise errors.IOError('The testbench parameters file could not be found') from None


	def save(self,filePath,fileName):
		variablesToSave = {}
		# for slots in [getattr(cls, '__slots__', []) for cls in type(self).__mro__]:
		# 	for attr in slots:
		# 		print(attr)
		# 		benchParameters[attr] = getattr(self, attr)

		variablesToSave['benchName'] 			= self.benchName
		variablesToSave['XYCameraID'] 			= self.XYCameraID
		variablesToSave['TiltCameraID'] 		= self.TiltCameraID
		variablesToSave['canUSBSerialNo'] 		= self.canUSBSerialNo
		variablesToSave['slotsCenters'] 		= self.slotsCenters.tolist()
		variablesToSave['recalibrateCenters'] 	= self.recalibrateCenters

		os.makedirs(filePath, exist_ok=True)
		with open(os.path.join(filePath, fileName),'w+') as outFile:
			json.dump(variablesToSave, outFile, separators = (',\n',': '))

	def clear_slots(self):
		self.slotIDs 		= np.array(range(1,self.nbSlots+1))
		self.positioners	= []
		self.slotsExposures	= []

	def init_positioners(self, genericPositioner = pos.Positioner()):
		try:
			response = self.canUSB.CAN_write(0,'askID', [])

			for i in range(0,len(response)):
				self.positioners.append(copy.deepcopy(genericPositioner))
				self.positioners[i].init(response[i], self.canUSB, waitInitComplete = False)

			if len(self.positioners) < 1:
				raise errors.PositionerError("No positioner in the bench") from None

			for positioner in self.positioners:
				#manually initialize each positioner's position
				while not positioner.datum_initialized(self.canUSB):
					time.sleep(0.005)

				#Set the current position as the hardstop position
				initial_position = {'Actual_alpha_pos': int(round(positioner.physics.incrementsPerRotation*positioner.model.offsetAlpha*180/np.pi/(DEFINES.DEGREES_PER_ROTATION),0)), \
									'Actual_beta_pos': int(round(positioner.physics.incrementsPerRotation*positioner.model.offsetBeta*180/np.pi/(DEFINES.DEGREES_PER_ROTATION),0))}
				self.canUSB.CAN_write(positioner.ID,'set_actual_position', initial_position)

				positioner.initialized = True

		except (errors.CANError, errors.PositionerError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners initialization failed") from None

	def get_connected_positioners_IDs(self):
		return [self.positioners[i].ID for i in range(0, len(self.positioners)) ]

	def stop_all_positioners(self):
		try:
			for positioner in self.positioners:
				positioner.stop(self.canUSB)
		except errors.CANError as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners could not be stopped. A manual shutdown is recommended") from None

	def set_current_all_positioners(self, alphaCurrent, betaCurrent):
		try:
			for positioner in self.positioners:
				positioner.set_current(self.canUSB, alphaCurrent, betaCurrent)
		except (errors.CANError, errors.PositionerError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners current setting failed") from None

	def set_speed_all_positioners(self, alphaSpeed, betaSpeed):
		try:
			for positioner in self.positioners:
				positioner.set_speed(self.canUSB, alphaSpeed, betaSpeed)
		except (errors.CANError, errors.PositionerError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners speed setting failed") from None

	def move_all_positioners(self, alphaAngle, betaAngle):
		tStart 	= -1
		tEnd 	= 0

		try:
			for positioner in self.positioners:
				movementTime = positioner.goto_position(self.canUSB, alphaAngle, betaAngle)
				if tStart < 0:
					tStart = time.perf_counter() #Start chronometer after the first movemement started
				tEnd = max(time.perf_counter()+movementTime,tEnd)

			#Wait for the movements to finish
			tRemaining = tEnd-time.perf_counter()

			while time.perf_counter()<tEnd:
				time.sleep(0.005)

		except (errors.CANError, errors.PositionerError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners movement failed") from None

	def move_all_positioners_different_angles(self, alphaAngle, betaAngle, approachDistance = 0, isInRad = False):
		if len(alphaAngle) is not self.nbSlots or len(betaAngle) is not self.nbSlots:
			raise errors.PositionerError("Length of input angles does not match the number of positioners") from None

		try:
			if isInRad:
				alphaAngle = 180*alphaAngle/np.pi
				betaAngle = 180*betaAngle/np.pi
				approachDistance = 180*approachDistance/np.pi

			if not approachDistance == 0:
		
				tStart 	= -1
				tEnd 	= 0
				movementTime = 0

				for slot in range(0, self.nbSlots):
					if not np.isnan(alphaAngle[slot]) and not np.isnan(betaAngle[slot]):
						movementTime = self.positioners[slot].goto_position(self.canUSB, alphaAngle[slot]-approachDistance, betaAngle[slot]-approachDistance)
					if tStart < 0:
						tStart = time.perf_counter() #Start chronometer after the first movmement started
					tEnd = max(time.perf_counter()+movementTime,tEnd)

				#Wait for the movement to finish
				tRemaining = tEnd-time.perf_counter()
				while time.perf_counter()<tEnd:
					time.sleep(0.005)

			tStart 	= -1
			tEnd 	= 0
			movementTime = 0

			for slot in range(0, self.nbSlots):
				if not np.isnan(alphaAngle[slot]) and not np.isnan(betaAngle[slot]):
					movementTime = self.positioners[slot].goto_position(self.canUSB, alphaAngle[slot], betaAngle[slot])
				if tStart < 0:
					tStart = time.perf_counter() #Start chronometer after the first movmement started
				tEnd = max(time.perf_counter()+movementTime,tEnd)

			#Wait for the movement to finish
			tRemaining = tEnd-time.perf_counter()
			while time.perf_counter()<tEnd:
				time.sleep(0.005)

		except (errors.CANError, errors.PositionerError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners movement failed") from None

	def move_all_positioners_to_origin(self):
		try:
			tStart 	= -1
			tEnd 	= 0

			for positioner in self.positioners:
				alphaAngle = max(0,positioner.physics.alphaAxisRange[0])
				betaAngle = max(0,positioner.physics.betaAxisRange[0])
				movementTime = positioner.goto_position(self.canUSB, alphaAngle, betaAngle)
				if tStart < 0:
					tStart = time.perf_counter() #Start chronometer after the first movmement started
				tEnd = max(time.perf_counter()+movementTime,tEnd)

			#Wait for the movement to finish
			tRemaining = tEnd-time.perf_counter()
			while time.perf_counter()<tEnd:
				time.sleep(0.005)

		except (errors.CANError, errors.PositionerError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners movement failed") from None

	def move_positioners_to_offset(self, approachDistance):
		try:
			alphaAngles = []
			betaAngles = []

			for positioner in self.positioners:
				alphaAngles.append(-positioner.model.offsetAlpha*180/np.pi)
				betaAngles.append(-positioner.model.offsetBeta*180/np.pi)

			self.move_all_positioners_different_angles(alphaAngles, betaAngles, approachDistance)

		except (errors.CANError, errors.PositionerError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners movement failed") from None

	def calibrate_all_motors(self):
		try:
			# Launch motor calibration
			for positioner in self.positioners:
				positioner.calibrate_motor(self.canUSB)

			# Wait until all the positioners finished their calibration
			finishedIDs = []
			while len(finishedIDs) < len(self.positioners):
				for positioner in self.positioners:
					if positioner.ID in finishedIDs:
						continue
					status = positioner.get_status(self.canUSB)
					if not(status&(canUSB._OPT.STREG.MOTOR_CALIBRATION)):
						finishedIDs.append(positioner.ID)
			# Check the calibration went well
			for positioner in self.positioners:
				result = positioner.get_motor_calibration_error(self.canUSB)
				if abs(result[0]) > DEFINES.CALIBRATION_MOTOR_MAXIMAL_ERROR or abs(result[1]) > DEFINES.CALIBRATION_MOTOR_MAXIMAL_ERROR:
					raise errors.OutOfRangeError(f'Motor calibration error of positioner {positioner.ID:04d} is too big') from None

		except (errors.CANError, errors.PositionerError, errors.OutOfRangeError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners motor calibration failed") from None

	def calibrate_all_datums(self):
		try:
			for positioner in self.positioners:
				positioner.calibrate_datum(self.canUSB)

			# Wait until all the positioners finished their calibration
			finishedIDs = []
			while len(finishedIDs) < len(self.positioners):
				for positioner in self.positioners:
					if positioner.ID in finishedIDs:
						continue
					status = positioner.get_status(self.canUSB)
					if not(status&(canUSB._OPT.STREG.DATUM_CALIBRATION)):
						finishedIDs.append(positioner.ID)

		except (errors.CANError, errors.PositionerError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners datum calibration failed") from None

	def calibrate_all_coggings(self):
		try:
			for positioner in self.positioners:
				positioner.calibrate_cogging_torque(self.canUSB)

			# Wait until all the positioners finished their calibration
			finishedIDs = []
			while len(finishedIDs) < len(self.positioners):
				for positioner in self.positioners:
					if positioner.ID in finishedIDs:
						continue
					status = positioner.get_status(self.canUSB)
					if not(status&(canUSB._OPT.STREG.COGGING_CALIBRATION)):
						finishedIDs.append(positioner.ID)

		except (errors.CANError, errors.PositionerError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
			raise errors.PositionerError("Positioners cogging torque calibration failed") from None

	def stop_handles(self):
		self.close_cameraXY()
		self.close_cameraTilt()
		self.close_canUSB()

	def refold_positioners_for_shipping(self):
		for positioner in self.positioners:
			positioner.set_current(self.canUSB, positioner.physics.maxCurrentAlpha, positioner.physics.maxCurrentBeta)
			positioner.set_speed(self.canUSB, positioner.physics.maxRpmAlpha, positioner.physics.maxRpmBeta)
				
		self.move_all_positioners(DEFINES.POS_SHIPPING_ANGLE_ALPHA, DEFINES.POS_SHIPPING_ANGLE_BETA)
		self.set_current_all_positioners(0,0)

	def preheat(self, preheatTime):
		#set the maximal current on all the positioners to preheat the testbench
		tStart = time.time()
		for positioner in self.positioners:
			positioner.set_current(self.canUSB, positioner.physics.maxCurrentAlpha, positioner.physics.maxCurrentBeta)

		#Wait until the bench is sufficiently hot
		while tStart + preheatTime > time.time():
			time.sleep(1)
			(days, hours, minutes, seconds) = decompose_time(tStart + preheatTime- time.time())
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Preheating the testbench ({hours:02d}h{minutes:02d}m{seconds:04.1f}s remaining)', overwritable = True)

		#shut the current down
		self.set_current_all_positioners(0,0)

	def reassign_centers_to_positioners(self):
		for positioner in self.positioners:
			positioner.model.centerX = self.slotsCenters[positioner.benchSlot,0]
			positioner.model.centerY = self.slotsCenters[positioner.benchSlot,1]

	def overwrite_centers_from_positioners(self):
		self.slotsCenters = self.originalSlotsCenters
		for slot in range(0,self.nbSlots):
			self.slotsCenters[positioner.benchSlot,0] = self.positioners[slot].model.centerX
			self.slotsCenters[positioner.benchSlot,1] = self.positioners[slot].model.centerY
		return True

	def identify_positioners_in_bench(self):
		try:
			#Setup the ROI
			if self.cameraXY.parameters.softROIrequired:
				self.cameraXY.setMaxROI()
				self.cameraXY.setExposure(DEFINES.PC_CAMERA_XY_DEFAULT_EXPOSURE)

			#Set the current and the speed
			for positioner in self.positioners:
				positioner.set_current(self.canUSB, positioner.physics.maxCurrentAlpha, positioner.physics.maxCurrentBeta)
				positioner.set_speed(self.canUSB, positioner.physics.maxRpmAlpha, positioner.physics.maxRpmBeta)
					
			
			#Move back to the origin
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,'Moving back to 0,0')
			self.move_all_positioners(0, 0)
			
			#Shut the current down
			self.set_current_all_positioners(0,0)

			#Get the optimal exposure for all the bench slots and sort out slots without any centroid. If the slot has a centroid, grab it.
			exposure 						= []
			validSlots 						= []
			validSlotsIDs					= []
			identificationCentroidsStart 	= []
			identificationCentroidsEnd		= []
			identificationDistances			= []
			sortedExposures = []
			sortedSlotsCenters = []
			sortedPositioners = []
			ROI 							= np.zeros(5)

			if self.cameraXY.parameters.softROIrequired:
				#Software ROI = get 1 image only. 1 unique exposure for all slots.
				#Set hardware ROI to be the whole image
				self.cameraXY.setMaxROI()
				
				#get exposure and capture 1 image
				completeExposure = self.cameraXY.getOptimalExposure(DEFINES.PC_CAMERA_XY_DEFAULT_EXPOSURE)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Exposure for all slots is '+str(round(completeExposure,0)))

				#if completeExposure >= DEFINES.PC_CAMERA_XY_MAX_EXPOSURE:
					#raise errors.CameraError("No light coming out the fibers") from None
				
				#completeImage = self.cameraXY.getImage()
			
				#treat each possible slot in the bench
				#for i in range(0,self.nbSlots):
					#Do a software crop of the unique image
					#validityCenter = (	self.slotsCenters[i][0]/self.cameraXY.parameters.scaleFactor,\
										#self.slotsCenters[i][1]/self.cameraXY.parameters.scaleFactor)
					#validityRadius = (positioner.physics.lengthAlpha+positioner.physics.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/self.cameraXY.parameters.scaleFactor
					
					#(currentImage,softROIoffsetX,softROIoffsetY) = self.cameraXY.computeValidSoftROI(completeImage, validityCenter, validityRadius)
									
					#self.cameraXY.parameters.ROIoffsetX = softROIoffsetX
					#self.cameraXY.parameters.ROIoffsetY = softROIoffsetY

					#tempImgMax = np.max(currentImage)/DEFINES.PC_CAMERA_MAX_INTENSITY_RAW

					#check validity of slot and get the centroid if valid
					#if tempImgMax >= DEFINES.CC_CENTROID_DETECTION_THRESHOLD:
						#image_ID = i
						#identificationCentroidsStart.append(cc.compute_centroid(currentImage, self.cameraXY.parameters, image_ID))
						#exposure.append(completeExposure)
						#validSlots.append(self.slotsCenters[i])
						#validSlotsIDs.append(self.slotIDs[i])

			#else:
				#for i in range(0,self.nbSlots):
					
					#Set the Slot ROI
					#ROI[0] = self.slotsCenters[i][0]/self.cameraXY.parameters.scaleFactor
					#ROI[1] = self.slotsCenters[i][1]/self.cameraXY.parameters.scaleFactor
					#ROI[2] = 2*(positioner.physics.lengthAlpha+positioner.physics.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/self.cameraXY.parameters.scaleFactor
					#ROI[3] = ROI[2]
					#ROI[4] = ROI[3]/2

					#self.cameraXY.setROI(ROI)
					
					#Get the exposure for the slot
					#tempExposure = self.cameraXY.getOptimalExposure(DEFINES.PC_CAMERA_XY_DEFAULT_EXPOSURE)
					#log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Exposure for slot #'+str(self.slotIDs[i])+' is '+str(round(tempExposure,0)))

					#check validity of slot and get the centroid if valid
					#if tempExposure < DEFINES.PC_CAMERA_XY_MAX_EXPOSURE:
						#image = self.cameraXY.getImage()
						
						#image_ID = i
						#identificationCentroidsStart.append(cc.compute_centroid(image, self.cameraXY.parameters, image_ID))
						#exposure.append(tempExposure)
						#validSlots.append(self.slotsCenters[i])
						#validSlotsIDs.append(self.slotIDs[i])


			#if len(validSlots) < 1:
				#raise errors.CameraError("No light coming out the fibers") from None

			#self.nbSlots = len(validSlots)
			#self.slotsCenters = validSlots
			#self.slotsExposures = exposure
			#self.slotIDs = validSlotsIDs

			#restart the current
			#for positioner in self.positioners:
				#positioner.set_current(self.canUSB, positioner.physics.maxCurrentAlpha, positioner.physics.maxCurrentBeta)
				
			#move each positioner a different amount
			#tEnd = 0
			#tStart = -1
			#currentAngle = DEFINES.PM_ANGLE_INCREMENT
			#theoricIdentificationDistance = []

			#for positioner in self.positioners:
				#alphaAngle = 0
				#betaAngle = currentAngle
				#movementTime = positioner.goto_position(self.canUSB, alphaAngle, betaAngle)
				#theoricIdentificationDistance.append(2*positioner.physics.lengthBeta*np.sin((currentAngle*np.pi/180)/2))
				#currentAngle += DEFINES.PM_ANGLE_INCREMENT
				#if tStart < 0:
					#tStart = time.perf_counter() #Start chronometer after the first movmement started
				#tEnd = max(time.perf_counter()+movementTime,tEnd)

			#tRemaining = tEnd-time.perf_counter()
			#log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Going to ({alphaAngle:7.2f},{betaAngle:7.2f}) in {tRemaining:5.2f} [s]', overwritable = True)
			#while time.perf_counter()<tEnd:
				#time.sleep(0.005)
			#tTaken = time.perf_counter()-tStart
			#log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Went to ({alphaAngle:7.2f},{betaAngle:7.2f}) in {tTaken:5.2f} [s]')
			
			#Shut the current down
			#self.set_current_all_positioners(0,0)

			#get all the final positions of the positioners and compute the distances
			#if self.cameraXY.parameters.softROIrequired:
				#completeImage = self.cameraXY.getImage()
				
				#treat each possible slot in the bench
				#for i in range(0,self.nbSlots):
					#Do a software crop of the unique image
					#validityCenter = (	self.slotsCenters[i][0]/self.cameraXY.parameters.scaleFactor,\
										#self.slotsCenters[i][1]/self.cameraXY.parameters.scaleFactor)
					#validityRadius = (positioner.physics.lengthAlpha+positioner.physics.lengthBeta+DEFINES.PC_IMAGE_SOFT_ROI_MARGIN)/self.cameraXY.parameters.scaleFactor
					
					#(currentImage,softROIoffsetX,softROIoffsetY) = self.cameraXY.computeValidSoftROI(completeImage, validityCenter, validityRadius)
									
					#self.cameraXY.parameters.ROIoffsetX = softROIoffsetX
					#self.cameraXY.parameters.ROIoffsetY = softROIoffsetY

					#image_ID = i
					#identificationCentroidsEnd.append(cc.compute_centroid(currentImage, self.cameraXY.parameters, image_ID))
					#identificationDistances.append(np.sqrt((identificationCentroidsStart[i][0]-identificationCentroidsEnd[i][0])**2+(identificationCentroidsStart[i][1]-identificationCentroidsEnd[i][1])**2))
			#else:
				#for i in range(0,self.nbSlots):
					#Set the Slot ROI
					#ROI[0] = self.slotsCenters[i][0]/self.cameraXY.parameters.scaleFactor
					#ROI[1] = self.slotsCenters[i][1]/self.cameraXY.parameters.scaleFactor
					#ROI[2] = 2*(positioner.physics.lengthAlpha+positioner.physics.lengthBeta+DEFINES.PM_POSITIONER_WORKSPACE_MARGIN)/self.cameraXY.parameters.scaleFactor
					#ROI[3] = ROI[2]
					#ROI[4] = ROI[3]/2

					#self.cameraXY.setROI(ROI)
					#self.cameraXY.setExposure(self.slotsExposures[i])
					#image = self.cameraXY.getImage()
					
					#image_ID = i
					#identificationCentroidsEnd.append(cc.compute_centroid(image, self.cameraXY.parameters, image_ID))
					#identificationDistances.append(np.sqrt((identificationCentroidsStart[i][0]-identificationCentroidsEnd[i][0])**2+(identificationCentroidsStart[i][1]-identificationCentroidsEnd[i][1])**2))
			
			#restart the current
			#restart the current
			#for positioner in self.positioners:
				#positioner.set_current(self.canUSB, positioner.physics.maxCurrentAlpha, positioner.physics.maxCurrentBeta)

			#move all the positioners to 0,0
			#self.move_all_positioners(0,0)

			#stop all positioners
			#self.stop_all_positioners()

			#Compute correlation between the slot and each positioner
			#correlation = np.ones((len(identificationDistances), len(theoricIdentificationDistance)))

			#for slot in range(0,len(identificationDistances)):
				#for positionerIndex in range(0,len(theoricIdentificationDistance)):
					#correlation[slot, positionerIndex] = abs(identificationDistances[slot]/theoricIdentificationDistance[positionerIndex]-1)

			#sortedExposures = []
			#sortedSlotsCenters = []
			#sortedPositioners = []
			#validSlotsIDs = []

			#assignedSlots = 0

			#Assign each positioner to the corresponding slot
			#for slot in range(0,self.nbSlots):
				#positionerIndex = np.argmin(correlation[slot,:])
				#if positionerIndex < len(self.positioners) and identificationDistances[slot] > DEFINES.PM_IDENTIFICATION_MINIMAL_DISPLACEMENT:
					#store the slots
					#sortedSlotsCenters.append(self.slotsCenters[slot])
					#validSlotsIDs.append(self.slotIDs[slot])
					#sortedExposures.append(self.slotsExposures[slot])

					#store the positioner corresponding to the slot
					#self.positioners[positionerIndex].benchSlot 		= assignedSlots
					#self.positioners[positionerIndex].model.centerX 	= sortedSlotsCenters[-1][DEFINES.CC_X_COORDINATE]
					#self.positioners[positionerIndex].model.centerY 	= sortedSlotsCenters[-1][DEFINES.CC_Y_COORDINATE]
					#sortedPositioners.append(self.positioners[positionerIndex])

					#log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Slot #{validSlotsIDs[-1]} contains positioner with ID {sortedPositioners[-1].ID} ({100*(1-correlation[slot,positionerIndex]):.1f}% correlation)')
					#assignedSlots += 1

				#if len(sortedPositioners)>1:
					#for positioner in sortedPositioners[0:-1]:
						#if sortedPositioners[-1].ID == positioner.ID:
							#raise errors.PositionerError(f'Multiple slots contain the same positioner ID ({sortedPositioners[-1].ID})') from None
            
			slot = 1
            
			sortedSlotsCenters.append(self.slotsCenters[slot])
			validSlotsIDs.append(self.slotIDs[slot])
			sortedExposures.append(completeExposure)

			self.positioners[0].benchSlot 		= 0
			self.positioners[0].model.centerX 	= sortedSlotsCenters[-1][DEFINES.CC_X_COORDINATE]
			self.positioners[0].model.centerY 	= sortedSlotsCenters[-1][DEFINES.CC_Y_COORDINATE]
			sortedPositioners.append(self.positioners[0])
            
			self.slotsCenters 		= np.array(sortedSlotsCenters)
			self.slotIDs 			= validSlotsIDs
			self.slotsExposures 	= sortedExposures
			self.positioners 		= sortedPositioners
			self.nbSlots 			= len(sortedExposures)
		
		except (errors.CameraError, errors.PositionerError, errors.CANError) as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,str(e))
			raise errors.PositionerError("Positioners identification failed") from None

def main():
	
	tb = TestBench()
	tb.load('Config\\TestBench_files\\04_XY_7bench_1.mat')
		
	# tb.init_cameraXY('Config\\Cameras')
	# myImage = tb.cameraXY.getImage()
	# print(myImage)

	# tb.init_canUSB()
	# response = tb.canUSB.CAN_write(0,'askID', [])
	# print(response)

	# tb.init_positioners()
	# for positioner in tb.positioners:
	# 	print(positioner.ID)
	# tb.set_current_all_positioners(70, 70)
	# tb.set_speed_all_positioners(1000, 1000)
	# tb.move_all_positioners(0, 0)
	# tb.identify_positioners_in_bench()
	
	# tb.close_cameraXY()
	# tb.close_canUSB()

	# tb.autosearch('Config\\TestBench_files')
	# tb.init_cameraXY('Config\\Cameras')
	# myImage = tb.cameraXY.getImage()
	# print(myImage)

	# tb.init_canUSB()
	# response = tb.canUSB.CAN_write(0,'askID', [])
	# print(response)

	tb.save('Config\\TestBench_files','04_XY_7bench_1.mat')


if __name__ == '__main__':
	log.init()
	main()
	log.stop()
