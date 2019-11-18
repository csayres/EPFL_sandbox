import sys
import os
import time
import folderStructure as fs
import programParameters as pp
import multiprocessing as mp
import positionerMovements as pm
import miscmath as mm
import numpy as np
import calibration
import pickle
import matplotlib.pyplot as plt
import logger as log
import DEFINES

def main(testBenchFile = None):
	#Allow multiprocessing
	mp.freeze_support()
	np.warnings.filterwarnings('ignore')

###########################################################################################################
	#Load predefined parameters
	t0 = time.perf_counter()
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Starting the program')
	programParameters = pp.ProgramParameters()

	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t0)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

###########################################################################################################
	#Check if user entered new parameters and overwrite predefined parameters if so
	t1 = time.perf_counter()
	nb_args = len(sys.argv)-1
	if nb_args > 0 or testBenchFile is not None:
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Overwritting default parameters')
		if testBenchFile is not None:
			newParams = []
			newParams.append(testBenchFile)
		else:
			newParams = sys.argv[1:len(sys.argv)]
		programParameters.overwrite_parameters(newParams)

		(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t1)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

###########################################################################################################
	#Check operations to perform and adapt if inconcistencies are found
	t2 = time.perf_counter()
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Check operations to perform')
	if not (programParameters.config.doCalibRun or programParameters.config.doTestRun):
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Nothing to be done. Abort program.')
		return False

	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t2)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

###########################################################################################################
	#Load the testBench parameters
	t4 = time.perf_counter()
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Loading the test bench parameters')
	if not programParameters.init_testBench_parameters():
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Test bench parameters loading failed. Abort Program.')
		return False

	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t4)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')


###########################################################################################################
	#Initialize the handles
	t3 = time.perf_counter()
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Creating the communication and camera handles')
	if not programParameters.init_handles():
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Handles initialization failed. Abort Program.')
		return False

	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t3)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

###########################################################################################################
	#Load the camera distortions
	t4 = time.perf_counter()
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Loading the camera distortion')
	if not programParameters.init_camera_distortion():
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Camera distortion loading failed. Abort Program.')
		programParameters.stop_handles()
		return False

	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t4)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

###########################################################################################################
	#Start the positioners
	t5 = time.perf_counter()
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Starting the positioners')
	if not programParameters.init_positionners():
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Positioners initialization failed. Abort Program.')
		programParameters.stop_positioners()
		programParameters.stop_handles()
		return False

	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t5)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

###########################################################################################################
	#Identify the positioners in the bench
	t6 = time.perf_counter()
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Starting positioner identification in the test bench')
	if not programParameters.identify_positioners_in_bench():
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Positioners identification failed. Abort Program.')
		programParameters.stop_positioners()
		programParameters.stop_handles()
		return False

	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t6)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

###########################################################################################################
	#Create the folder structure

	#TODO CHANGE THE STRUCTURE

	t7 = time.perf_counter()
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Creating the folder structure')
	if not programParameters.init_folders():
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Folder structure spawning could not complete properly. Abort program.')
		programParameters.stop_positioners()
		programParameters.stop_handles()
		return False

	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t7)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

###########################################################################################################
	#Start the multiprocessing instances
	t8 = time.perf_counter()
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching the multiprocessing instance')
	programParameters.init_processes()
	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t8)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Initialization complete in '+str(round(time.perf_counter()-t0,DEFINES.TIME_ROUND_DECIMALS))+' [s]')
	
############################################################################################################
	#Start the small calibration run if necessary
	if programParameters.config.doFastCalibRun:
		fastCalibrationResults = False

		t9 = time.perf_counter()
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching fast calibration run')
		fastCalibrationResults = calibration.run(programParameters, programParameters.smallCalibration)
		if not fastCalibrationResults:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Fast calibration run could not complete properly. Abort program.')
			programParameters.stop_all()
			return False

		(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t9)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {days:02d}d {hours:02d}h{minutes:02d}m{seconds:04.1f}s')

###################################################For testing########################################################
		filename = os.path.join('Python_garbage','smallCalibrationResult.obj')
		if fastCalibrationResults == False:
			with open(filename, 'rb') as fileHandle:
				fastCalibrationResults = pickle.load(fileHandle)
		else:
			with open(filename, 'wb') as fileHandle:
				pickle.dump(fastCalibrationResults,fileHandle)
######################################################################################################################

		#Start the fast calibration calculation
		t10 = time.perf_counter()
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching fast calibration calculation')
		(fastCalibrationResults, programParameters) = calibration.compute_model(fastCalibrationResults, programParameters)
		if not fastCalibrationResults:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Fast calibration calculation could not complete properly. Abort program.')
			programParameters.stop_all()
			return False

		(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t10)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

		if programParameters.smallCalibration.plotResults:
			t11 = time.perf_counter()
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching fast calibration plotting')
			calibration.plot_calib(fastCalibrationResults,programParameters.fileParameters)
			(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t11)
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

###########################################################################################################
	#Start the calibration run 
	if programParameters.config.doCalibRun:
		if programParameters.config.doLivePlot:
			programParameters.processes.livePlotCommandQueue.put(DEFINES.PROCESSES_CLEAR_LIVEPLOT)

		calibrationResults = False

		t9 = time.perf_counter()
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching calibration run')
		calibrationResults = calibration.run(programParameters, programParameters.calibration)
		if not calibrationResults:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Calibration run could not complete properly. Abort program.')
			programParameters.stop_all()
			return False

		(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t9)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {days:02d}d {hours:02d}h{minutes:02d}m{seconds:04.1f}s')
		# Stop the multiprocessing instance and the handles
		programParameters.stop_processes()

###################################################For testing########################################################
		filename = os.path.join('Python_garbage','calibrationResult.obj')
		if calibrationResults == False:
			with open(filename, 'rb') as fileHandle:
				calibrationResults = pickle.load(fileHandle)
		else:
			with open(filename, 'wb') as fileHandle:
				pickle.dump(calibrationResults,fileHandle)
######################################################################################################################

		#Start the calibration calculation
		t10 = time.perf_counter()
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching calibration calculation')
		(calibrationResults, programParameters) = calibration.compute_model(calibrationResults, programParameters)
		if not calibrationResults:
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR,0,'Calibration calculation could not complete properly. Abort program.')
			programParameters.stop_all()
			return False

		(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t10)
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {minutes:02d}m{seconds:04.1f}s')

		if programParameters.calibration.plotResults:
			t11 = time.perf_counter()
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Launching calibration plotting')
			calibration.plot_calib(calibrationResults,programParameters.fileParameters)
			(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t11)
			log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO,0,f'Done in {seconds:5.2f}s')

	#close all handles and multiprocessing instances
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Stopping the program')
	programParameters.stop_all()

	(days, hours, minutes, seconds) = mm.decompose_time(time.perf_counter()-t0)
	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'All done in {days:02d}d {hours:02d}h{minutes:02d}m{seconds:04.1f}s')

	log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Holding for figures display...')
	# plt.show()

	return True

if __name__ == '__main__':
	log.init()
	main()
	log.stop()