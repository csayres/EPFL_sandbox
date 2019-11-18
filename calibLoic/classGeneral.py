#cython: language_level=3
import classTestBench as tb
import classConfig as config
import classPositioners as pos
import classCalibration as calib
import classTest as test
import processManager as proc
import time
from scipy import io
import os
import logger as log
import numpy as np
import miscmath as mm
import mailSender as ms
import DEFINES
import errors

class Status():
	__slots__ = (	'currentState',\
					'currentEtap',\
					'GUIcommandQueue',\
					'GUIlivePlotQueue',\
					'testBenchInitialized',\
					'CANBusInitialized',\
					'threadsInitialized',\
					'positionersInitialized',\
					'positionersIdentified',\
					'calibRunned',\
					'calibLoaded',\
					'calibComputed',\
					'testRunned',\
					'testLoaded',\
					'testComputed',\
					'currentPoint',\
					'totalPoints',\
					'tStart',\
					'tRemaining',\
					'tEnd')

	def __init__(self):
		self.GUIcommandQueue 		= None
		self.GUIlivePlotQueue 		= None

		self.currentState 			= "Stopped"
		self.currentEtap			= "Starting"

		self.testBenchInitialized 	= False
		self.CANBusInitialized 		= False
		self.threadsInitialized 	= False
		self.positionersInitialized = False
		self.positionersIdentified 	= False
		self.calibRunned 			= False
		self.calibLoaded			= False
		self.calibComputed 			= False
		self.testRunned 			= False
		self.testLoaded				= False
		self.testComputed 			= False

		self.currentPoint 			= 0
		self.totalPoints 			= 0
		self.tStart 				= time.time()
		self.tRemaining 			= 0
		self.tEnd 					= self.tStart + self.tRemaining

class General:
	__slots__ = (	'status',\
					'config',\
					'testBench',\
					'genericPositioner',\
					'fastCalibrationPar',\
					'calibrationPar',\
					'testPar',\
					'calibrationResults',\
					'testResults',\
					'processManager')

	def __init__(self):
		self.status 			= Status()
		self.config				= config.Config()
		self.testBench 			= tb.TestBench()
		self.genericPositioner  = pos.Positioner()
		self.fastCalibrationPar	= calib.Parameters()
		self.calibrationPar 	= calib.Parameters()
		self.testPar 			= test.Parameters()
		self.calibrationResults = calib.Results()
		self.testResults		= test.Results()
		self.processManager		= proc.ProcessManager()

	def load_config(self):
		self.config.load(self.config.get_config_fileName())

	def load_all_params(self):
		pass

	def init_processes(self):
		if self.config.doLivePlot:
			if self.status.GUIlivePlotQueue is None:
				self.processManager.generate_new_live_plot_queue()
			else:				
				self.processManager.livePlotCommandQueue = self.status.GUIlivePlotQueue
				self.processManager.livePlotProcessStarted = True
			if self.processManager.livePlotProcessStarted == False:
				self.processManager.start_livePlot_process(self.testBench.cameraXY.parameters.maxX*self.testBench.cameraXY.parameters.scaleFactor, self.testBench.cameraXY.parameters.maxY*self.testBench.cameraXY.parameters.scaleFactor, self.testBench.nbSlots)
			
		cameraXYparams = None
		cameraTiltparams = None
		if self.testBench.cameraXY is not None:
			cameraXYparams = self.testBench.cameraXY.parameters
		if self.testBench.cameraTilt is not None:
			cameraTiltparams = self.testBench.cameraTilt.parameters

		self.processManager.start_centroid_processes(cameraXYparams, cameraTiltparams)
		
	def stop_all(self):
		try:
			self.testBench.stop_all_positioners()
		except errors.Error as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,str(e))
		self.processManager.stop_livePlot_process()
		self.processManager.stop_centroid_processes()
		self.testBench.close_handles()

	def run_main(self): #TODO: To delete once the new strucutre works correcly
		try:

			self.processManager	= proc.ProcessManager() #regenerate a new process manager
			self.config.reset_project_time()
			
		###########################################################################################################
			#Load predefined parameters
			t0 = time.perf_counter()
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Starting the program')

			(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t0)
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

		###########################################################################################################
			#Adapt the config
			if self.config.doTestRun or self.config.loadTestRun and not self.config.doCalibRun:
				self.config.loadCalibRun = True

		###########################################################################################################
			if self.config.doFastCalibRun or self.config.doCalibRun or self.config.doTestRun:
				#Load the testBench parameters
				t4 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Loading the test bench parameters')

				self.testBench.load(self.config.get_current_testBench_fileName())

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t4)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

			###########################################################################################################
				#Initialize the handles
			if self.config.doFastCalibRun or self.config.doCalibRun or self.config.doTestRun:
				t3 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Creating the communication and camera handles')

				self.testBench.init_handles(self.config)

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t3)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

			###########################################################################################################
				#Start the positioners
			if self.config.doFastCalibRun or self.config.doCalibRun or self.config.doTestRun:
				t5 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Starting the positioners')

				self.genericPositioner.model.clear(self.genericPositioner.physics)

				self.testBench.init_positioners(self.genericPositioner)

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t5)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

			###########################################################################################################
				#Identify the positioners in the bench
			if self.config.doFastCalibRun or self.config.doCalibRun or self.config.doTestRun:
				t6 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Starting positioner identification in the test bench')
				
				self.testBench.identify_positioners_in_bench()
				
				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t6)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

			###########################################################################################################
				#Preload the model
			if self.config.preloadPositionerModel:
				t7 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Overwriting default positioner model')

				self.config.load_positioners_model(self.testBench)
				self.testBench.reassign_centers_to_positioners()
				for positioner in self.testBench.positioners:
					positioner.calibrated = True

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t7)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

			###########################################################################################################
				#Start the multiprocessing instances
			if self.config.doFastCalibRun or self.config.doCalibRun or self.config.doTestRun:
				t8 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching the multiprocessing instance')

				self.init_processes()

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t8)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Initialization complete in '+str(round(time.perf_counter()-t0,DEFINES.TIME_ROUND_DECIMALS))+' [s]')
				
			#ENDIF

	############################################################################################################
			#Preheat the bench to minimize any thermal dilatation effects

			if self.config.preheatBench:
				
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Preheating the testbench')
				self.testBench.preheat(self.config.preheatBenchTime)

	############################################################################################################
			#Start the internal motor calibrations

			if self.config.calibrateMotor:
				t8 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching the positioners motors calibration')
				
				self.testBench.calibrate_all_motors()

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t8)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {minutes:02d}m{seconds:04.1f}s')

			if self.config.calibrateDatum:
				t8 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching the positioners datum calibration')
				
				self.testBench.calibrate_all_datums()

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t8)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {minutes:02d}m{seconds:04.1f}s')

			if self.config.calibrateCogging:
				t8 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching the positioners cogging torque calibration')
				
				self.testBench.calibrate_all_coggings()

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t8)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {minutes:02d}m{seconds:04.1f}s')


	############################################################################################################
			#Start the small calibration run if necessary
			if self.config.doFastCalibRun:
				fastCalibrationResults = []
				for slot in range(0, self.testBench.nbSlots):
					fastCalibrationResults.append(calib.Results())

				t9 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching fast calibration run')
				
				calib.run(self.testBench, self.fastCalibrationPar, fastCalibrationResults, self.config, self.processManager)
					
				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t9)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {days:02d}d {hours:02d}h{minutes:02d}m{seconds:04.1f}s')
			
				#Start the fast calibration calculation
				t10 = time.perf_counter()
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching fast calibration calculation')

				calib.compute_model(fastCalibrationResults)

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t10)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

				#update the positioners model
				calib.update_positioners_model(fastCalibrationResults, self.testBench)

				#reset the offsets
				if self.fastCalibrationPar.resetOffsetAfterCalib:
					for slot in range(0, self.testBench.nbSlots):
						self.testBench.positioners[slot].set_position_offset(self.testBench.canUSB)
                    		#start all positioners current and set speed
					self.testBench.set_current_all_positioners(100, 100)
					self.testBench.set_speed_all_positioners(4000, 4000)
					self.testBench.move_all_positioners_to_origin()

			#create the results containers
			calibrationResults = []
			testResults = []
			if self.config.doCalibRun:
				for slot in range(0, self.testBench.nbSlots):
					calibrationResults.append(calib.Results())
			elif self.config.loadCalibRun:
				positionerIDs = []

				if len(self.config.IDsToLoad) > 0 and not self.config.doTestRun:
					positionerIDs = self.config.IDsToLoad
				elif self.testBench.canUSB.serHandle is not None:
					positionerIDs = self.testBench.get_connected_positioners_IDs()

				if len(positionerIDs) < 1:
					raise errors.Error("No positioner to load")

				for slot in range(0, len(positionerIDs)):
					calibrationResults.append(calib.Results())

			if self.config.doTestRun:
				for slot in range(0, self.testBench.nbSlots):
					testResults.append(test.Results())
			elif self.config.loadTestRun:
				if not self.config.loadCalibRun:
					positionerIDs = []

					if len(self.config.IDsToLoad) > 0 and not self.config.doTestRun:
						positionerIDs = self.config.IDsToLoad
					elif self.testBench.canUSB.serHandle is not None:
						positionerIDs = self.testBench.get_connected_positioners_IDs()

					if len(positionerIDs) < 1:
						raise errors.Error("No positioner to load")
				
				for slot in range(0, len(positionerIDs)):
					testResults.append(test.Results())


			#start the test the required amount of time
			for lifetimeLoop in range(self.config.currentLifetimeIteration, self.config.nbTestingLoops):

				self.config.currentLifetimeIteration = lifetimeLoop

			############################################################################################################
				#Start the calibration run
				if self.config.doCalibRun:
					for slot in range(0, self.testBench.nbSlots):
						calibrationResults[slot].runDone = False
						calibrationResults[slot].calcDone = False

					if self.config.reloadCalibParEachIter == True:
						self.calibrationPar.load(self.config.get_current_calib_param_fileName())

					t9 = time.perf_counter()
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Launching calibration run (iteration {lifetimeLoop+1}/{self.config.nbTestingLoops})')
					
					calib.run(self.testBench, self.calibrationPar, calibrationResults, self.config, self.processManager)
					
					self.config.save_calib_results(calibrationResults)

					(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t9)
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {days:02d}d {hours:02d}h{minutes:02d}m{seconds:04.1f}s')
					
				#or load a previous calibration
				elif self.config.loadCalibRun:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Launching calibration loading')
					
					self.config.load_calib_results(calibrationResults, positionerIDs, lifetimeLoop)

				if self.config.doCalibRun or self.config.loadCalibRun:
					#Start the calibration calculation
					t10 = time.perf_counter()
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching calibration calculation')

					calib.compute_model(calibrationResults)
					# log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Calibration calculation could not complete properly. Abort program.')
						
					self.config.save_calib_results(calibrationResults)

					(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t10)
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

				if (self.config.doCalibRun or self.config.loadCalibRun) and self.config.plotResults:
					t11 = time.perf_counter()
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching calibration plotting')

					calib.plot(calibrationResults, self.config)
					if lifetimeLoop > 0:
						calib.plot_lifetime(calibrationResults, self.config)

					(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t11)
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {minutes:02d}m{seconds:03.1f}s')

					#update the positioners model and the testbench centers
				if self.config.doCalibRun or self.config.doTestRun:
					calib.update_positioners_model(calibrationResults, self.testBench)

					#reset the offsets
					if self.config.doCalibRun and self.calibrationPar.resetOffsetAfterCalib:
						for slot in range(0, self.testBench.nbSlots):
							self.testBench.positioners[slot].set_position_offset(self.testBench.canUSB)

					self.config.save_positioners_model(self.testBench)

				if self.config.doCalibRun and self.testbench.recalibrateCenters:
					if self.testBench.overwrite_centers_from_positioners():
						self.testBench.save(self.config.get_current_testBench_fileName())

				if self.config.doCalibRun or self.config.loadCalibRun:
					self.config.save_calib_results(calibrationResults)

	################################### DO TEST RUN ##############################

				if self.config.doTestRun:
					self.config.load_positioners_model(self.testBench)

					for slot in range(0, self.testBench.nbSlots):
						testResults[slot].runDone = False
						testResults[slot].calcDone = False

					if self.config.reloadTestParEachIter == True:
						self.testPar.load(self.config.get_current_test_param_fileName())


					t9 = time.perf_counter()
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Launching test run (iteration {lifetimeLoop+1}/{self.config.nbTestingLoops})')
					
					test.run(self.testBench, self.testPar, testResults, self.config, self.processManager)

					self.config.save_test_results(testResults)

					(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t9)
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {days:02d}d {hours:02d}h{minutes:02d}m{seconds:04.1f}s')
				#or load a previous test

				elif self.config.loadTestRun:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Launching test loading')
					
					self.config.load_test_results(testResults, positionerIDs, lifetimeLoop)

				if self.config.doTestRun or self.config.loadTestRun:
					t10 = time.perf_counter()
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching test calculation')
					
					test.calc(testResults)
				
					self.config.save_test_results(testResults)

					(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t10)
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

				if (self.config.doTestRun or self.config.loadTestRun) and self.config.plotResults:
					t11 = time.perf_counter()
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching test plotting')
					
					test.plot(testResults, self.config)
					if lifetimeLoop > 0:
						test.plot_lifetime(testResults, self.config)
					
					(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t11)
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {minutes:02d}m{seconds:03.1f}s')

				if self.config.doTestRun or self.config.loadTestRun:
					self.config.save_test_results(testResults)

				if self.config.sendMail:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Sending results mails')
					ms.send_results(self.config.mailReceivers, calibrationResults, testResults)

				if self.config.saveInQc:
					log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Saving QC results file')
					self.config.save_QC_result(calibrationResults, testResults)

				(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t0)
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'All done in {days:02d}d {hours:02d}h{minutes:02d}m{seconds:04.1f}s')

			#Go to the shipping position
			if self.config.doCalibRun or self.config.doTestRun:
				self.testBench.refold_positioners_for_shipping()

		except errors.Error as e:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL,0,str(e))
		except KeyboardInterrupt:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL,0,'Program was manually interrupted')
		# except Exception as e:
		# 	log.message(DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL,0,str(e))

		self.stop_all()

def main():

	general=General()
	# general.load_config()
	# general.genericPositioner.physics.load(general.config.get_current_positioner_physics_fileName())
	# general.genericPositioner.requirements.load(general.config.get_current_positioner_requirements_fileName())
	# general.fastCalibrationPar.load(general.config.get_current_fast_calib_param_fileName())
	# general.calibrationPar.load(general.config.get_current_calib_param_fileName())		
	# general.testPar.load(general.config.get_current_test_param_fileName())
	general.run_main()

	# general.testBench.load(general.config.get_current_testBench_fileName())
	# general.fastCalibrationPar.load(general.config.get_current_fast_calib_param_fileName())
	# general.calibrationPar.load(general.config.get_current_calib_param_fileName())
	# general.testPar.save(os.path.join(general.config.generalConfigFolder, general.config.testsFolder), general.config.currentTestFile+general.config.testsFileExtension)
	# general.testPar.load(general.config.get_current_test_param_fileName())
	# garbagePositioner = pos.Positioner()
	# garbagePositioner.physics.load(os.path.join(general.config.generalConfigFolder, general.config.positionersFolder, general.config.currentPositionerFile+general.config.positionersFileExtension))
	# garbagePositioner.requirements.load(os.path.join(general.config.generalConfigFolder, general.config.requirementsFolder, general.config.currentRequirementsFile+general.config.requirementsFileExtension))

	# general.config.currentProjectFolder = 'Blackbird'
	# general.config.positionerFolderSuffix = ''
	# general.config.currentTestBenchFile = '04_XY_7bench_1.json'
	# general.config.currentPositionerFile = 'SDSSV.json'
	# general.config.currentRequirementsFile = 'SDSSV.json'
	# general.config.currentFastCalibrationFile = 'fastCalib.json'
	# general.config.currentCalibrationFile = 'MPS_calib.json'
	# general.config.currentTestsFile = ''
	# general.config.save()
	# general.testBench.save(os.path.join(general.config.generalConfigFolder, general.config.testBenchFolder),general.config.currentTestBenchFile)
	# general.fastCalibrationPar.save(os.path.join(general.config.generalConfigFolder, general.config.calibrationsFolder,general.config.currentFastCalibrationFile))
	# general.calibration.save(os.path.join(general.config.generalConfigFolder, general.config.calibrationsFolder),general.config.currentCalibrationFile)
	# garbagePositioner = pos.Positioner()
	# garbagePositioner.physics.save(os.path.join(general.config.generalConfigFolder, general.config.positionersFolder),general.config.currentPositionerFile)
	# garbagePositioner.requirements.save(os.path.join(general.config.generalConfigFolder, general.config.requirementsFolder),general.config.currentRequirementsFile)
	# garbagePositioner.model.save('python_garbage', 'model-test.json')

	# general.config.load(general.config.get_config_fileName())
	
	

if __name__ == '__main__':
	#Allow multiprocessing
	import multiprocessing as mp
	mp.freeze_support()
	np.warnings.filterwarnings('ignore')
	log.init()
	main()
	log.stop()
