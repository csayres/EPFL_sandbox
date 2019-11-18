#cython: language_level=3
import DEFINES
import time
import numpy as np
import computeCentroid as cc
import multiprocessing as mp
from queue import Empty
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import logger as log
import miscmath as mm
import sys
import copy

class ProcessManager:
	__slots__ = (	'nbCentroidProcesses',\
					'centroidProcesses',\
					'centroidQueue',\
					'resultManager',\
					'resultList',\
					'centroidProcessesStarted',\
					'livePlotProcess',\
					'livePlotCommandQueue',\
					'livePlotProcessStarted')

	def __init__(self):
		self.nbCentroidProcesses				= max(min(mp.cpu_count()-1,DEFINES.PROC_MAX_NB_PROCESSES), DEFINES.PROC_MIN_NB_PROCESSES)

		self.centroidProcesses					= []
		self.centroidQueue						= mp.JoinableQueue(2**30)# for i in range(0,self.nbCentroidProcesses)]
		self.resultManager						= mp.Manager()
		self.resultList 						= self.resultManager.list()
		self.centroidProcessesStarted			= False

		self.livePlotProcess					= []
		self.livePlotCommandQueue 				= None
		self.livePlotProcessStarted				= False

	def generate_new_live_plot_queue(self):
		self.livePlotCommandQueue = mp.Queue()
		return self.livePlotCommandQueue

	def start_centroid_processes(self, cameraXYparams = None, cameraTiltparams = None):
		if not self.centroidProcessesStarted:
			# self.nbCentroidProcesses = max(min(mp.cpu_count()-1,DEFINES.PROC_MAX_NB_PROCESSES), DEFINES.PROC_MIN_NB_PROCESSES)

			# self.nbCentroidProcesses = 1

			for i in range(0,self.nbCentroidProcesses):
				self.centroidProcesses.append(mp.Process(	target = centroids_calculation_process,\
															args = (self.centroidQueue,\
																	self.resultList,\
																	log.get_queue_object(),\
																	cameraXYparams,\
																	cameraTiltparams)))
			for p in self.centroidProcesses:
				p.start()

			self.centroidProcessesStarted = True

	def start_livePlot_process(self, xMax, yMax, nbSlots):
		if not self.livePlotProcessStarted and self.livePlotCommandQueue is not None:
			self.livePlotProcess.append(mp.Process(	target = livePlot_process, \
													args = (self.livePlotCommandQueue, \
															self.resultList,\
															xMax, \
															yMax, \
															nbSlots)))
			for p in self.livePlotProcess:
				p.start()

			self.livePlotProcessStarted = True

	def stop_centroid_processes(self):
		if self.centroidProcessesStarted:
			#reclear the queue
			self.centroidQueueClear()

			#Stop the processes
			for i in range(0,self.nbCentroidProcesses):
				self.centroidQueue.put(DEFINES.PROCESSES_POISON_PILL, block = True)
			for p in self.centroidProcesses:
				p.join()

			#reclear the queue
			self.centroidQueueClear()

			#clear the variables
			self.centroidProcesses			= []
			self.centroidProcessesStarted 	= False
			self.restart_manager()

	def stop_livePlot_process(self):
		if self.livePlotProcessStarted:
			#clear the queue
			try:
				while 1:
					self.livePlotCommandQueue.get_nowait()
			except Empty:
				pass

			#stop the process
			self.livePlotCommandQueue.put(DEFINES.PROCESSES_POISON_PILL, block = True)
			for p in self.livePlotProcess:
				p.join()

			#reclear the queue
			try:
				while 1:
					self.livePlotCommandQueue.get_nowait()
			except Empty:
				pass

			#reset the variables
			self.livePlotProcess			= []
			self.livePlotProcessStarted 	= False

	def restart_manager(self):
		if not self.centroidProcessesStarted:
			self.resultManager				= mp.Manager()
			self.resultList 				= self.resultManager.list()

	def get_centroids_result(self, start = 0, end = -1):
		if end == -1:
			return self.resultList[start:]
		else:
			return self.resultList[start:end]

	def clear_centroids_results(self):
		self.resultList[:] = []

	def get_centroid_results_length(self):
		return len(self.resultList)

	def centroidQueuePut(self, args, block = True):
		self.centroidQueue.put(args, block = block)

	def centroidQueueJoin(self):
		self.centroidQueue.join()

	def centroidQueueClear(self):		
		try:
			while 1:
				self.centroidQueue.get_nowait()
				self.centroidQueue.task_done()
		except (Empty, ValueError):
			pass
		
def centroids_calculation_process(inputQueue, outputList, logQueue, cameraXYparams, cameraTiltparams):
	np.warnings.filterwarnings('ignore')
	# cameraXYparams = copy.deepcopy(cameraXYparams)
	
	try:
		while 1:
			args = inputQueue.get(block = True)

			if args == DEFINES.PROCESSES_POISON_PILL:
				return

			elif args != '':
				image = copy.deepcopy(args[0])
				offsetX = args[1]
				offsetY = args[2]
				imgID = args[3]
				validityCenter = (args[4][0]-offsetX,args[4][1]-offsetY)
				validityRadius = args[5]
				argLen = len(args)

				del args

				(benchSlot, startingPoint, repetition, step, axis, direction, centroidType) =  mm.get_img_ID(np.int64(imgID))

				# result = cc.compute_centroid(image, cameraProps, imageID)
				if centroidType == DEFINES.MM_IMG_ID_XY_IDENTIFIER:
					if argLen>4:
						(image,addedOffsetX,addedOffsetY) = mm.computeValidSoftROI(image, cameraXYparams.maxX, cameraXYparams.maxY, validityCenter, validityRadius)
						offsetX += addedOffsetX
						offsetY += addedOffsetY
					cameraXYparams.ROIoffsetX = offsetX
					cameraXYparams.ROIoffsetY = offsetY
					result = cc.compute_centroid(image,cameraXYparams,imgID)
					# if logQueue is not None:
					# 	logQueue.put((DEFINES.LOG_MESSAGE_PRIORITY_WARNING,0,f'Size in memory: xCorr: {cameraXYparams.xCorr.size*cameraXYparams.xCorr.itemsize} Bytes; yCorr: {cameraXYparams.yCorr.size*cameraXYparams.yCorr.itemsize} Bytes',False,False))
					# else:
					# 	log.message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING,0,f'Size in memory: xCorr: {cameraXYparams.xCorr.size*cameraXYparams.xCorr.itemsize} Bytes; yCorr: {cameraXYparams.yCorr.size*cameraXYparams.yCorr.itemsize} Bytes',False,False)
					
				elif centroidType == DEFINES.MM_IMG_ID_TILT_IDENTIFIER:
					cameraTiltparams.ROIoffsetX = offsetX
					cameraTiltparams.ROIoffsetY = offsetX
					result = cc.compute_centroid(image,cameraTiltparams,imgID)
				else:
					result = (np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,imgID)

				if np.isnan(result[0]) and logQueue is not None:
					logQueue.put((DEFINES.LOG_MESSAGE_PRIORITY_WARNING,0,'No centroid could be found',False,False))

				outputList.append(result)
				
			inputQueue.task_done()

	except KeyboardInterrupt:
		return
	except OSError:
		return	

def livePlot_process(plotQueue, centroidsResults, xMax, yMax, nbSlots):
	#create the live plot instance
	np.warnings.filterwarnings('ignore')

	plt.ion()
	plt.figure(1)
	# win = plt.gcf().canvas.manager.window
	# win.overrideredirect(1) #remove the closing button
	ax = plt.subplot(1,1,1)
	redraw_livePlot_framework(ax, xMax, yMax)
	plt.draw()
	plt.pause(1e-17)

	ptsStorageX = [[] for slot in range(0,nbSlots)] # x
	ptsStorageY = [[] for slot in range(0,nbSlots)] # y
	ptsColor = [[] for slot in range(0,nbSlots)] # color
	ptsCounter = np.zeros((nbSlots), dtype = int)
	firstCentroid = 0
	allCentroids = []

	order = None

	tFrame = time.perf_counter()
	
	while 1:
		try:
			try:
				order = plotQueue.get_nowait()
			except Empty:
				time.sleep(DEFINES.PROCESSES_AUTODRAW_PERIOD/10)
				pass

			tCurrent = time.perf_counter()
			if order == DEFINES.PROCESSES_POISON_PILL:
				return
			elif order == DEFINES.PROCESSES_CLEAR_LIVEPLOT:
				
				redraw_livePlot_framework(ax, xMax, yMax)
				plt.draw()
				plt.pause(1e-17)

				ptsStorageX = [[] for slot in range(0,nbSlots)] # x
				ptsStorageY = [[] for slot in range(0,nbSlots)] # y
				ptsColor = [[] for slot in range(0,nbSlots)] # color
				firstCentroid = 0
				allCentroids = []

			elif order == DEFINES.PROCESSES_DRAW_LIVEPLOT or tCurrent-tFrame >= DEFINES.PROCESSES_AUTODRAW_PERIOD:
				tFrame = tCurrent
							
				t0 = time.perf_counter()

				#get the n last centroids
				try:
					lastCentroid = len(centroidsResults)
					allCentroids = centroidsResults[firstCentroid:lastCentroid]
				except EOFError:
					pass

				firstCentroid = lastCentroid
				
				for centroid in allCentroids:
					(benchSlot, startingPoint, repetition, step, axis, direction, centroidType) =  mm.get_img_ID(np.int64(centroid[7]))
					#If the maximum number of points are reached, remove the oldest point
					if len(ptsColor[benchSlot]) >= DEFINES.PROCESSES_LIVE_PLOT_NB_POINTS:
						ptsColor[benchSlot].pop(0)
						ptsStorageX[benchSlot].pop(0)
						ptsStorageY[benchSlot].pop(0)

					#Add the new point
					if direction == DEFINES.MM_IMG_ID_COUNTERCLOCKWIZE_DIR_IDENTIFIER:
						ptsColor[benchSlot].append(DEFINES.PLOT_COUNTERCLOCKWIZE_COLOR)
					else:
						ptsColor[benchSlot].append(DEFINES.PLOT_CLOCKWIZE_COLOR)

					ptsStorageX[benchSlot].append(centroid[0])
					ptsStorageY[benchSlot].append(centroid[1])
				
				redraw_livePlot_framework(ax, xMax, yMax)
			
				for slot in range(0, nbSlots):
					if len(ptsColor[slot])>0:
						ax.scatter(ptsStorageX[slot], ptsStorageY[slot], c=ptsColor[slot],marker = 'x',s=1)

				plt.draw()
				plt.pause(1e-17)

			order = None

		except KeyboardInterrupt:
			pass
		except OSError:
			return
		# except Exception as e:
		# 	print(str(e))

def redraw_livePlot_framework(ax, xMax, yMax):
	ax.clear()
	ax.set_title('Current positionner position')
	ax.set_xlabel('X [mm]')
	ax.set_ylabel('Y [mm]')
	ax.set_xlim(0, xMax)
	ax.set_ylim(yMax,0)
	ax.set_aspect('equal')

def main():
	pass

if __name__ == '__main__':
	main()