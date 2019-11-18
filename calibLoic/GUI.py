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
		self.general = classGeneral.General()
		
		self.general.config.reloadCalibParEachIter 				= False
		self.general.config.reloadTestParEachIter 				= False
		self.general.fastCalibrationPar.numberOfStartingPoints 	= 1
		self.general.fastCalibrationPar.numberOfRepetitions 	= 1
		self.general.fastCalibrationPar.numberOfStepsPerCircle 	= 10
		self.general.fastCalibrationPar.alphaAxisRange 			= [0, 90]
		self.general.fastCalibrationPar.betaAxisRange 			= [0, 90]
		self.general.fastCalibrationPar.storeHallPositions 		= False
		self.general.fastCalibrationPar.resetOffsetAfterCalib 	= True
		
		self.general.config.currentTestBenchFile = DEFINES.GUI_TB1_FILENAME
		# self.general.status.GUIlivePlotQueue = mp.Queue()

########MAIN WINDOW###########################################################
		sg.ChangeLookAndFeel('Dark')  

		self.colTB1 = [	[sg.Text('Testbench 1', font = (DEFINES.GUI_DEFAULT_FONT, 20), background_color = 'blue', text_color = 'white', justification='center', size = (20,1), key = 'testbenchText')],
						[sg.Radio('Testbench 1', group_id = 'testbenchChoice', default = True, enable_events = True,  key = 'testbenchChoice1'), sg.Radio('Testbench 2', group_id = 'testbenchChoice', enable_events = True, key = 'testbenchChoice2')],
						[sg.Button('Start', font = (DEFINES.GUI_DEFAULT_FONT, 20), button_color = ('white', 'blue'), key = 'start', size = (20,2), tooltip = 'Start a new calibration on the selected testbench')],
						]
		
		self.layout = [	[sg.Column(self.colTB1, key = 'controlCol'),sg.Frame('Log',[[
													sg.Multiline(size = (100,30), background_color = 'black', autoscroll = True, disabled = True, font = ("Consolas", 11), key='Log_testbench')]])]]

		self.window = sg.Window('SDSS-V Calibration Software', self.layout, grab_anywhere=False, resizable = True)
		
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
				self.window['testbenchChoice1'].Update(disabled = True)
				self.window['testbenchChoice2'].Update(disabled = True)
				self.window['start'].Update(disabled = True)
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
				self.window.Refresh()
		
		self.window.Close()

	def check_pause(self):
		pass

def main():
	log.init()
	
	my_gui = MainWindow()

	log.init(my_gui)
	my_gui.run()
	log.stop()

if __name__ == '__main__':
	main()