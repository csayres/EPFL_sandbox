#cython: language_level=3
import colorama
from tkinter import INSERT, NORMAL, DISABLED, END
import multiprocessing as mp
from queue import Empty
from datetime import datetime
import DEFINES

class _LoggingManager():
	__slots__ = (	'logProcess',\
					'logQueue',\
					'logReady',\
					'guiWindow',\
					'nbMessages',\
					'previousMsgPriority',\
					'previousMsgOverwritable')

	def __init__(self, guiWindow = None):
		self.logProcess	= None		
		self.logQueue	= None
		self.logReady 	= False
		self.guiWindow	= None
		self.nbMessages = 0
		self.previousMsgPriority = DEFINES.LOG_MESSAGE_PRIORITY_INFO
		self.previousMsgOverwritable = True

	def start_logging(self, guiWindow = None):
		if not self.logReady:
			self.logProcess	= None
			if self.logQueue is None:
				self.logQueue	= mp.Queue()
			else:
				self.logQueue.clear()
			self.logProcess = mp.Process(	target = _logging_process,\
											args = (self.logQueue,))

			self.logProcess.start()
			self.logReady = True

		if guiWindow is not None:
			self.guiWindow = guiWindow
			textWidget = self.guiWindow.window['Log_testbench'].Widget
			textWidget.tag_config('DEBUG', foreground=DEFINES.LABEL_MSG_COLOR_DEBUG)
			textWidget.tag_config('INFO', foreground=DEFINES.LABEL_MSG_COLOR_INFO)
			textWidget.tag_config('WARNING', foreground=DEFINES.LABEL_MSG_COLOR_WARNING)
			textWidget.tag_config('CRITICAL', foreground=DEFINES.LABEL_MSG_COLOR_CRITICAL)
			textWidget.tag_config('ERROR', foreground=DEFINES.LABEL_MSG_COLOR_ERROR)

	def stop_logging(self):
		if self.logReady:
			self.logQueue.put(DEFINES.PROCESSES_POISON_PILL)
			self.logProcess.join()
			#clear the queue
			try:
				while 1:
					self.logQueue.get_nowait()
			except Empty:
				pass
		self.guiWindow = None

	def add_log(self, priority = DEFINES.LOG_MESSAGE_PRIORITY_INFO, tabulationLevel = 0, message = '', overwritable = False, removeMsgHeader = False):
		if self.guiWindow is not None:
			self.gui_log(priority, message, overwritable)
		elif self.logReady:
			args = (priority, tabulationLevel, message, overwritable, removeMsgHeader)
			self.logQueue.put(args)

	def get_log_queue(self):
		if self.logReady:
			return self.logQueue
		else:
			return None

	def reset_message_count(self):
		self.nbMessages = 0

	def gui_log(self, priority = DEFINES.LOG_MESSAGE_PRIORITY_INFO, message = '', overwritable = False):
		if priority <= DEFINES.LOG_VERBOSE_LEVEL and self.guiWindow is not None:
			strPriority = ''
			
			# try:
			self.guiWindow.window['Log_testbench'].Update(disabled = False)
			textWidget = self.guiWindow.window['Log_testbench'].Widget

			newLineChar = '\n'
			if self.previousMsgOverwritable == True and priority == self.previousMsgPriority:
				textWidget.delete("end-1l linestart-1c", "end")
				newLineChar = ''

			if self.nbMessages >= DEFINES.GUI_MAX_MESSAGE_BUFFER: #If the maximal amount of messages has been reached, remove the first one
				textWidget.delete("1.0", "2.0")
			else:
				if newLineChar == '\n':
					self.nbMessages += 1

			

			if priority >= DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO:
				strPriority = '[DEBUG]:\t'
				textWidget.insert(END, '\n'+strPriority+message, 'DEBUG')
			elif priority >= DEFINES.LOG_MESSAGE_PRIORITY_INFO:
				strPriority = '[INFO]:\t'
				textWidget.insert(END, '\n'+strPriority+message, 'INFO')
			elif priority >= DEFINES.LOG_MESSAGE_PRIORITY_WARNING:
				strPriority = '[WARNING]:\t'
				textWidget.insert(END, '\n'+strPriority+message, 'WARNING')
			elif priority >= DEFINES.LOG_MESSAGE_PRIORITY_ERROR:
				strPriority = '[ERROR]:\t'
				textWidget.insert(END, '\n'+strPriority+message, 'ERROR')
			elif priority >= DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL:
				strPriority = '[CRITICAL]:\t'
				textWidget.insert(END, '\n'+strPriority+message, 'CRITICAL')

			# textWidget.update()
			self.guiWindow.window['Log_testbench'].Update(disabled = True)
			self.guiWindow.window.Refresh()
			self.guiWindow.check_pause()

			self.previousMsgOverwritable = overwritable
			self.previousMsgPriority = priority
			
			# except:
			# 	pass

#The process that manages the logging in the console
def _logging_process(inputQueue):
	colorama.init()

	previousMsgPriority = DEFINES.LOG_MESSAGE_PRIORITY_INFO
	previousMsgOverwritable = False

	try:
		while 1:
			
			args = inputQueue.get()
			if args == DEFINES.PROCESSES_POISON_PILL:
				return

			priority 			= args[0]
			tabulationLevel 	= args[1]
			message 			= args[2]
			overwritable 		= args[3]
			removeMsgHeader 	= args[4]

			if priority <= DEFINES.LOG_VERBOSE_LEVEL:
				
				#if the message is overwritable, return to the start of the line
				if overwritable == True:
					endChar = '\r'
				else:
					endChar = '\n'

				tNow = datetime.now()
				strTabulation = ''
				strPriority = ''
				strColor = DEFINES.MSG_COLOR_DEFAULT
				strTime = tNow.strftime("%a %d/%m/%Y %H:%M:%S")
				startChar = ''

				#Set the tabulations to insert
				for i in range(0,tabulationLevel):
					strTabulation += '\t'

				if priority >= DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO:
					strPriority = '[DEBUG]:\t'
					strColor = DEFINES.MSG_COLOR_DEBUG
				elif priority >= DEFINES.LOG_MESSAGE_PRIORITY_INFO:
					strPriority = '[INFO]: \t'
					strColor = DEFINES.MSG_COLOR_INFO
				elif priority >= DEFINES.LOG_MESSAGE_PRIORITY_WARNING:
					strPriority = '[WARNING]:\t'
					strColor = DEFINES.MSG_COLOR_WARNING
				elif priority >= DEFINES.LOG_MESSAGE_PRIORITY_ERROR:
					strPriority = '[ERROR]:\t'
					strColor = DEFINES.MSG_COLOR_ERROR
				elif priority >= DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL:
					strPriority = '[CRITICAL]:\t'
					strColor = DEFINES.MSG_COLOR_CRITICAL

				if previousMsgOverwritable == True and previousMsgPriority != priority:
					startChar = '\n'

				if removeMsgHeader == False:
					print(startChar+DEFINES.MSG_COLOR_DEFAULT+strTime+' '+strColor+strPriority+strTabulation+message+DEFINES.MSG_COLOR_DEFAULT+'\033[K',end = endChar)
				else:
					print(startChar+strColor+'\t\t\t\t\t'+strTabulation+message+DEFINES.MSG_COLOR_DEFAULT+'\033[K',end = endChar)

				previousMsgPriority = priority
				previousMsgOverwritable = overwritable
	except KeyboardInterrupt:
		pass
	except OSError:
		return

#Callable functions

_logManager = _LoggingManager()

def init(guiWindow = None):
	global _logManager
	_logManager.start_logging(guiWindow)

def stop():
	global _logManager
	_logManager.stop_logging()

def get_queue_object():
	global _logManager
	return _logManager.get_log_queue()

def message(priority = DEFINES.LOG_MESSAGE_PRIORITY_INFO, tabulationLevel = 0, message = '', overwritable = False, removeMsgHeader = False):
	global _logManager
	_logManager.add_log(priority, tabulationLevel, message, overwritable, removeMsgHeader)

def reset_message_count():
	_logManager.reset_message_count()
	
def main():
	init()
	message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO, 0, "This is a debug")
	message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, "This is an information")
	message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING, 0, "This is a warning")
	message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, "This is an error")
	message(DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL, 0, "This is a critical error")

if __name__ == '__main__':
	main()