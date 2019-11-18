#cython: language_level=3
import PySimpleGUI as sg
import tkinter as tk
import os
import multiprocessing as mp
import logger as log
import numpy as np
import miscmath as mm
import classGeneral
import time
import sys
import DEFINES

class MainWindow:
	def __init__(self):
		self.paused = False

		self.general = classGeneral.General()
		self.general.load_config()

		log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, "Configuration unlocked")

		self.general.config.currentPositionerFile = 'Debug'
		self.general.config.currentRequirementsFile = 'Debug'
		self.general.config.currentFastCalibrationFile = 'Debug_fast'
		self.general.config.currentCalibrationFile = 'Debug'
		self.general.config.currentTestFile = 'Debug'

		self.general.genericPositioner.physics.load(self.general.config.get_current_positioner_physics_fileName())
		self.general.genericPositioner.requirements.load(self.general.config.get_current_positioner_requirements_fileName())
		self.general.fastCalibrationPar.load(self.general.config.get_current_fast_calib_param_fileName())
		self.general.calibrationPar.load(self.general.config.get_current_calib_param_fileName())		
		self.general.testPar.load(self.general.config.get_current_test_param_fileName())

		# self.general.config.save()
		# self.general.genericPositioner.physics.save(self.general.config.get_positioner_physics_path(), self.general.config.currentPositionerFile + self.general.config.positionersFileExtension)
		# self.general.genericPositioner.requirements.save(self.general.config.get_positioner_requirements_path(), self.general.config.currentRequirementsFile + self.general.config.requirementsFileExtension)
		# self.general.fastCalibrationPar.save(self.general.config.get_fast_calib_param_path(), self.general.config.currentFastCalibrationFile + self.general.config.calibrationsFileExtension)
		# self.general.calibrationPar.save(self.general.config.get_calib_param_path(), self.general.config.currentCalibrationFile + self.general.config.calibrationsFileExtension)		
		# self.general.testPar.save(self.general.config.get_test_param_path(), self.general.config.currentTestFile + self.general.config.testsFileExtension)

		self.general.config.currentTestBenchFile = DEFINES.GUI_TB1_FILENAME
		# self.general.status.GUIlivePlotQueue = mp.Queue()

########MAIN WINDOW###########################################################
		sg.ChangeLookAndFeel('Dark')  

		self.colTB1 = [	[sg.Text('Testbench 1', font = (DEFINES.GUI_DEFAULT_FONT, 20), background_color = 'blue', text_color = 'white', justification='center', size = (20,1), key = 'testbenchText')],
						[sg.Radio('Testbench 1', group_id = 'testbenchChoice', default = True, enable_events = True,  key = 'testbenchChoice1'), sg.Radio('Testbench 2', group_id = 'testbenchChoice', enable_events = True, key = 'testbenchChoice2')],
						[sg.Button('Start', font = (DEFINES.GUI_DEFAULT_FONT, 20), button_color = ('white', 'blue'), key = 'start', size = (20,2), tooltip = 'Start a new calibration on the selected testbench')],
						[sg.Button('Pause', font = (DEFINES.GUI_DEFAULT_FONT, 20), button_color = ('black', 'red'), key = 'pause', size = (20,2), tooltip = 'Pause the current operation', disabled = True)],
						[sg.Checkbox('Lifetime', default=False, key = 'loadLifetime')],
						[sg.Button('Reload', font = (DEFINES.GUI_DEFAULT_FONT, 20), button_color = ('black', 'grey'), key = 'reload', size = (20,2), tooltip = 'Reloads all the configuration files')],
						]
		
		self.layout = [	[sg.Column(self.colTB1, key = 'controlCol'),sg.Frame('Log',[[
													sg.Multiline(size = (100,30), background_color = 'black', autoscroll = True, disabled = True, font = ("Consolas", 11), key='Log_testbench')]])]]

		self.window = sg.Window('SDSS-V Calibration Software [UNLOCKED]', self.layout, grab_anywhere=False, resizable = True)

		self.window.Finalize()

	def run(self):
		while True:
			event, values = self.window.Read()#timeout=10)
			if event is None:
				break
			elif event == 'testbenchChoice1':
				self.window['testbenchText'].Update(value = 'Testbench 1', background_color = 'blue', text_color = 'white')
				self.general.config.currentTestBenchFile = DEFINES.GUI_TB1_FILENAME
				self.window['start'].Update(text = 'Start',button_color = ('white', 'blue'))
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Testbench 1 selected')
			elif event == 'testbenchChoice2':
				self.window['testbenchText'].Update(value = 'Testbench 2', background_color = 'yellow', text_color = 'black')
				self.general.config.currentTestBenchFile = DEFINES.GUI_TB2_FILENAME
				self.window['start'].Update(text = 'Start',button_color = ('black', 'yellow'))
				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Testbench 2 selected')
			elif event == 'start':
				self.window['Log_testbench'].Update(value = "")
				log.reset_message_count()
				self.window['testbenchChoice1'].Update(disabled = True)
				self.window['testbenchChoice2'].Update(disabled = True)
				self.window['start'].Update(disabled = True)
				self.window['pause'].Update(disabled = False)
				self.window['reload'].Update(disabled = True)
				self.window['loadLifetime'].Update(disabled = True)
						
				self.window.Refresh()
				# try:
				self.general.run_main()
				# except KeyboardInterrupt:
				# 	try:
				# 		self.general.stop_all()
				# 	except:
				# 		pass
				# 	log.message(DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL,0,"Program manually interrupted")
				# except Exception as e:
				# 	# print(e)
				# 	log.message(DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL,0,"Program failed")
				# except OSError:
				# 	try:
				# 		self.general.stop_all()
				# 	except:
				# 		pass
				# 	log.message(DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL,0,"Program failed")
				
				self.window.Refresh()
				self.window['testbenchChoice1'].Update(disabled = False)
				self.window['testbenchChoice2'].Update(disabled = False)
				self.window['start'].Update(disabled = False)
				self.window['pause'].Update(text = 'Pause',button_color = ('black', 'red'),disabled = True)
				self.window['reload'].Update(disabled = False)
				self.window['loadLifetime'].Update(disabled = False)
				self.window.Refresh()
		
			# elif event == 'pause':
			# 	self.window['pause'].Update(text = 'Unpause',button_color = ('black', 'green'))
			# 	while True:
			# 		event, values = self.window.Read()#timeout=10)
			# 		if event == 'pause':
			# 			self.window['pause'].Update(text = 'Pause',button_color = ('black', 'red'))
			# 			break
			# 		time.sleep(0.01)

			elif event == 'reload':
				currentBench = self.general.config.currentTestBenchFile
				self.general.load_config()
				self.general.config.currentTestBenchFile = currentBench

				if self.window['loadLifetime'].Get():
					self.general.config.nbTestingLoops = 100
				
					self.general.config.currentPositionerFile = 'MPS'
					self.general.config.currentRequirementsFile = 'SDSSV'
					self.general.config.currentFastCalibrationFile = 'MPS_fast'
					self.general.config.currentCalibrationFile = 'MPS_lifetime'
					self.general.config.currentTestFile = 'MPS_lifetime'
				else:
					self.general.config.currentPositionerFile = 'Debug'
					self.general.config.currentRequirementsFile = 'Debug'
					self.general.config.currentFastCalibrationFile = 'Debug_fast'
					self.general.config.currentCalibrationFile = 'Debug'
					self.general.config.currentTestFile = 'Debug'

				self.general.genericPositioner.physics.load(self.general.config.get_current_positioner_physics_fileName())
				self.general.genericPositioner.requirements.load(self.general.config.get_current_positioner_requirements_fileName())
				self.general.fastCalibrationPar.load(self.general.config.get_current_fast_calib_param_fileName())
				self.general.calibrationPar.load(self.general.config.get_current_calib_param_fileName())		
				self.general.testPar.load(self.general.config.get_current_test_param_fileName())

				log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,'Configuration reloaded')

		self.window.Close()

	def check_pause(self):
		event, values = self.window.Read(timeout=1)
		if event == 'pause':
			self.window['pause'].Update(text = 'Unpause',button_color = ('black', 'green'))
			while True:
				event, values = self.window.Read()#timeout=10)
				if event == 'pause':
					self.window['pause'].Update(text = 'Pause',button_color = ('black', 'red'))
					break
				time.sleep(0.01)

def main():
	log.init()
	
	my_gui = MainWindow()

	log.init(my_gui)
	my_gui.run()
	log.stop()

if __name__ == '__main__':
	main()