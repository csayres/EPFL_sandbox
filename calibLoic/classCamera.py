#cython: language_level=3
#################### Python script grab_image_small.py########################
#   Setups a Basler camera to grab images,
#   calculate the light dot centroid and return it.
#   This script always uses the first camera detected.
#   All the input parameters are optionnal
#INPUT:#######################################################################
#   Output_file:    the name of the file to store the results to.
#   nb_images:      [1;100]. The number of pictures the camera takes to compute one centroid
#   exposure_time:  [35;1600000]. The exposure time of the camera, in us
#   gain:           []. The gain of the camera
#   black_level:    []. The black level of the camera
#   gamma:          []. The gamma parameter of the camera
#   digital_shift:  []. The digital shift of the camera
#OUTPUT:######################################################################
#   Saves the centroid value to the specified output_file
#   Prints the values of the centroid of the light dot
##############################################################################

from pypylon import pylon as pypylon
from pypylon import genicam
import logger as log
import numpy as np
import sys
import os
from scipy import io
from skimage.filters import gaussian as gaussianFilter
import matplotlib.pyplot as plt
import miscmath as mm
import time
import DEFINES
import errors

#REPLACE THIS MODULE WITH THE CLASS
class CameraParameters:
    __slots__ = (   'cameraType',\
                    'maxX',\
                    'maxY',\
                    'xCorr',\
                    'yCorr',\
                    'scaleFactor',\
                    'ROICenter',\
                    'validityRadius',\
                    'ROIoffsetX',\
                    'ROIoffsetY',\
                    'ROIwidth',\
                    'ROIheight',\
                    'minCropWindow',\
                    'nbImagesToGrab',\
                    'ID',\
                    'softROIrequired')

    def __init__(self, cameraType, camHandle= None):
        self.cameraType = cameraType
        if not camHandle == None:
            self.maxX = camHandle.Width.Max
            self.maxY = camHandle.Height.Max
        else:
            self.maxX = 0
            self.maxY = 0

        self.xCorr = np.zeros((self.maxX, self.maxY))
        self.yCorr = np.zeros((self.maxX, self.maxY))

        self.ROICenter = (self.maxX/2,self.maxY/2)
        self.validityRadius = np.sqrt(self.maxX**2+self.maxY**2)
        self.ROIoffsetX = 0
        self.ROIoffsetY = 0
        self.ROIwidth = self.maxX
        self.ROIheight = self.maxY
        self.minCropWindow = max(self.maxX,self.maxY)
        self.nbImagesToGrab = 1

        self.ID = -1
        self.softROIrequired = True

class Camera:
    __slots__ = (   'connected',\
                    'parameters',\
                    'camHandle')

    def __init__(self, cameraType = None, compatibleCameraID = None):

        self.connected = False
        self.parameters = CameraParameters(cameraType)
        if cameraType is not None:
            self.connect(cameraType, compatibleCameraID)

    def __del__(self):
        if self.connected:
            try:
                self.camHandle.Close()
            except genicam.GenericException:
                pass
            self.parameters = None

    def connect(self, cameraType = None, compatibleCameraID = None):
        if not self.connected or not (self.parameters.cameraType == cameraType) or not (self.parameters.ID == compatibleCameraID) :
            #If we want to change the camera, close the currently connected one
            if self.connected:
                try:
                    self.camHandle.close()
                except genicam.GenericException:
                    pass
            #Connect to the new camera
            try:
                if cameraType == None:
                    raise TypeError

                #initalize the camera
                tlf = pypylon.TlFactory.GetInstance()

                available_cameras = tlf.EnumerateDevices()
                available_ids = np.zeros(len(available_cameras))

                for i in range(0,len(available_cameras)):
                    available_ids[i] = available_cameras[i].GetSerialNumber()
                    if available_ids[i] == compatibleCameraID or compatibleCameraID == None:
                        cameraAlreadyUsed = False
                        try:
                            self.camHandle = pypylon.InstantCamera(tlf.CreateDevice(available_cameras[i]))
                        except genicam.GenericException:
                            cameraAlreadyUsed = True
                            log.message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING, 0, f'Camera {available_ids[i]:.0f} is already used in another application')
                            if not compatibleCameraID == None:
                                raise errors.CameraError("No compatible camera could be found") from None #If this was a specific ID search, break

                        if not cameraAlreadyUsed:
                            self.camHandle.Open()

                            #configure default camera settings
                            self.camHandle.PixelFormat  = DEFINES.PC_CAMERA_PIXEL_FORMAT
                            self.camHandle.OffsetX      = 0
                            self.camHandle.OffsetY      = 0
                            self.camHandle.Width        = self.camHandle.Width.Max
                            self.camHandle.Height       = self.camHandle.Height.Max

                            self.parameters.cameraType = cameraType
                            self.parameters.maxX = self.camHandle.Width.Max
                            self.parameters.maxY = self.camHandle.Height.Max
                            self.parameters.ID = int(available_ids[i])

                            if cameraType == DEFINES.PC_CAMERA_TYPE_XY:
                                self.parameters.nbImagesToGrab      = DEFINES.PC_CAMERA_XY_NB_IMAGES_PER_POINT
                                self.parameters.minCropWindow       = DEFINES.PC_CAMERA_XY_MIN_CROP_WINDOW
                            else:
                                self.parameters.nbImagesToGrab      = DEFINES.PC_CAMERA_TILT_NB_IMAGES_PER_POINT
                                self.parameters.minCropWindow       = DEFINES.PC_CAMERA_FORBID_CROPPING

                            if self.parameters.minCropWindow == DEFINES.PC_CAMERA_FORBID_CROPPING:
                                self.parameters.minCropWindow = np.max(self.parameters.maxX, self.parameters.maxY)

                            if self.camHandle.GetDeviceInfo().GetModelName() == 'acA5472-17um': #Require soft ROI for the acA5472-17um cameras
                                self.parameters.softROIrequired = True

                            self.connected = True
                            return

                if not self.connected:
                    raise errors.CameraError("No compatible camera could be found") from None #If this was a specific ID search, break

            except errors.CameraError as e:
                log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, str(e))
                raise errors.CameraError("Camera initialization failed") from None
            except genicam.GenericException:
                raise errors.CameraError("Camera initialization failed") from None

    def setDistortionCorrection(self,config):
        if self.connected:

            fileName = os.path.join(config.get_camera_path(), 'camera_'+str(self.parameters.ID)+config.cameraFileExtension)

            #load the camera distortion parameters
            try:
                cam_distortion = io.loadmat(fileName)
            except genicam.GenericException:
                raise errors.IOError("Camera distortion file could not be loaded") from None
                return

            try:
                cam_distortion = cam_distortion[DEFINES.PC_FILE_DISTORTION_PARAMETERS_NAME]

                cam_x_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_XCORR_NAME]
                cam_y_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_YCORR_NAME]
                cam_scale_factor = cam_distortion[DEFINES.PC_FILE_DISTORTION_SCALE_FACTOR_NAME]

                self.parameters.xCorr = np.nan_to_num(cam_x_corr[0,0])
                self.parameters.yCorr = np.nan_to_num(cam_y_corr[0,0])
                self.parameters.scaleFactor = cam_scale_factor[0,0][0,0]
            except genicam.GenericException:
                raise errors.IOError("Camera distortion file data is corrupted") from None

            return

        else:
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING, 0, 'Trying to load calibration data of an unconnected camera')

    #ROI: (x_center, y_center, width, heigth, validityRadius)
    def setROI(self, ROI):
        if self.connected:
            if ROI[0] > self.parameters.maxX or ROI[0] < 0 or ROI[1] > self.parameters.maxY or ROI[1] < 0:
                raise errors.OutOfRangeError("Specified camera ROI is out of range")
                return

            try:
                x_min = int(ROI[0]-ROI[2]/2)
                x_max = int(ROI[0]+ROI[2]/2)
                y_min = int(ROI[1]-ROI[3]/2)
                y_max = int(ROI[1]+ROI[3]/2)

                #crop ROI while it is not in the image, up to the minimal window allowed
                if x_min < 0:
                    x_min = 0
                if x_max-x_min < self.parameters.minCropWindow:
                    x_max = x_min+self.parameters.minCropWindow
                if x_max > self.parameters.maxX:
                    x_max = self.parameters.maxX
                if x_max-x_min < self.parameters.minCropWindow:
                    x_min = x_max-self.parameters.minCropWindow
                if y_min < 0:
                    y_min = 0
                if y_max-y_min < self.parameters.minCropWindow:
                    y_max = y_min+self.parameters.minCropWindow
                if y_max > self.parameters.maxY:
                    y_max = self.parameters.maxY
                if y_max-y_min < self.parameters.minCropWindow:
                    y_min = y_max-self.parameters.minCropWindow

                if self.camHandle.GetDeviceInfo().GetModelName() == 'acA5472-17um': #Strangly, the acA5472-17um camera needs a multiple of 4 for Xoffset and width
                    x_min = x_min-x_min%4
                    width = x_max-x_min
                    width = width - width%4
                else:
                    width = x_max-x_min

                height = y_max-y_min

                self.parameters.ROICenter = (ROI[0],ROI[1])
                self.parameters.validityRadius = ROI[4]
                self.parameters.ROIoffsetX = x_min
                self.parameters.ROIoffsetY = y_min
                self.parameters.ROIwidth = width
                self.parameters.ROIheight = height

                #set the ROI properties
                if  self.camHandle.OffsetX.Value + width < self.parameters.maxX:
                    self.camHandle.Width  = width
                    self.camHandle.OffsetX= x_min
                else:
                    self.camHandle.OffsetX= x_min
                    self.camHandle.Width  = width

                if  self.camHandle.OffsetY.Value + height < self.parameters.maxY:
                    self.camHandle.Height = height
                    self.camHandle.OffsetY= y_min
                else:
                    self.camHandle.OffsetY= y_min
                    self.camHandle.Height = height
            except genicam.GenericException:
                self.connected = False
                raise errors.CameraError("Camera communication failed")
        else:
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING, 0, 'Trying to set the ROI of an unconnected camera')

    def setMaxROI(self):
        if self.connected:
            try:
                self.parameters.ROICenter = (self.parameters.maxX,self.parameters.maxY)
                self.parameters.validityRadius = DEFINES.PC_IMAGE_GET_ALL_ROI
                self.parameters.ROIoffsetX = 0
                self.parameters.ROIoffsetY = 0
                self.parameters.ROIwidth = self.parameters.maxX
                self.parameters.ROIheight = self.parameters.maxY
                self.camHandle.OffsetX= 0
                self.camHandle.Width  = self.camHandle.Width.Max
                self.camHandle.OffsetY= 0
                self.camHandle.Height = self.camHandle.Height.Max
            except genicam.GenericException:
                self.connected = False
                raise errors.CameraError("Camera communication failed")
        else:
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING, 0, 'Trying to set the ROI of an unconnected camera')

    def getROI(self):
        if not self.connected:
            raise errors.CameraError("Camera is not connected") from None
        else:
            return self.parameters.ROIoffsetX,self.parameters.ROIoffsetY,self.parameters.ROIwidth,self.parameters.ROIheight

    def computeValidSoftROI(self, image, validityCenter, validityRadius):
        if validityRadius == DEFINES.PC_IMAGE_GET_ALL_ROI:
            return image, 0, 0
        else:
            return mm.computeValidSoftROI(image, self.parameters.maxX, self.parameters.maxY, validityCenter, validityRadius)

    def getImage(self, computationManager = None, imageID = None):
        if not self.connected:
            raise errors.CameraError("Camera is not connected") from None
        else:
            try:
                #Initialize result container
                i = 0
                result = np.zeros((self.camHandle.Height.Value, self.camHandle.Width.Value), dtype = np.uint16);
                #grab images
                # t0 = time.perf_counter()

                self.camHandle.StartGrabbingMax(self.parameters.nbImagesToGrab)
                # t1 = time.perf_counter()
                # print(f'StartGrab\t\t\t{t1-t0:3.3f}')
                while self.camHandle.IsGrabbing():
                    # t2 = time.perf_counter()
                    grabResult = self.camHandle.RetrieveResult(DEFINES.PC_IMAGE_TIMEOUT, pypylon.TimeoutHandling_Return)

                    # t3 = time.perf_counter()

                    if grabResult.GrabSucceeded():
                        result = np.add(grabResult.Array, result)
                        grabResult.Release()
                        i = i+1
                    # t4 = time.perf_counter()
                    # print(f'RetrieveResult\t\t\t{t3-t2:3.3f}')
                    # print(f'Add and release result\t\t{t4-t3:3.3f}')

                # t5 = time.perf_counter()
                # print(f'Total grab\t\t\t{t5-t0:3.3f}')
                #crop validity circle
                if self.parameters.validityRadius != DEFINES.PC_IMAGE_GET_ALL_ROI:
                    validityCenter = (self.parameters.ROICenter[0]-self.camHandle.OffsetX.Value,self.parameters.ROICenter[1]-self.camHandle.OffsetY.Value)
                    circularMask = mm.create_circular_mask(result.shape[0], result.shape[1], validityCenter, self.parameters.validityRadius)

                    result[~circularMask] = 0
                # t6 = time.perf_counter()
                # print(f'Precropping circle\t\t{t6-t5:3.3f}')
                image = np.divide(result, i)
                # t7 = time.perf_counter()
                # print(f'NP Divide image\t\t\t{t7-t6:3.3f}')
                #directly send to computation queue if asked for
                if computationManager is not None:
                    computationManager.put_in_centroid_queue((image, self.parameters.ROIoffsetX, self.parameters.ROIoffsetY, imageID),block = True)
                # t8 = time.perf_counter()
                # print(f'Total execution\t\t\t{t8-t0:3.3f}')
                #return image
                return image
            except (genicam.GenericException, SystemError):
                self.connected = False
                raise errors.CameraError("Camera communication failed during image grabbing")

    def getOptimalExposure(self, initExposure):
        if not self.connected:
            raise errors.CameraError("Camera is not connected")
        else:
            try:
                #init loop
                i = 1
                nbOk = 0
                if self.parameters.cameraType == DEFINES.PC_CAMERA_TYPE_XY:
                    maxExposure = DEFINES.PC_CAMERA_XY_MAX_EXPOSURE
                else:
                    maxExposure = DEFINES.PC_CAMERA_GET_EXPOSURE_EXPOSURE_MAX

                currentExposure = initExposure

                self.camHandle.ExposureTime = currentExposure

                #grab images and adapt exposure
                while i <= DEFINES.PC_CAMERA_GET_EXPOSURE_MAX_ITERATIONS:
                    #get one image

                    image = self.camHandle.GrabOne(DEFINES.PC_IMAGE_TIMEOUT)
                    image = np.divide(image.Array,DEFINES.PC_CAMERA_MAX_INTENSITY_RAW)

                    #crop validity circle

                    validityCenter = (self.parameters.ROICenter[0]-self.camHandle.OffsetX.Value,self.parameters.ROICenter[1]-self.camHandle.OffsetY.Value)
                    image, offsetX, offsetY = self.computeValidSoftROI(image, validityCenter, self.parameters.validityRadius)

                    #filter the image with a gaussian filter
                    if self.parameters.cameraType == DEFINES.PC_CAMERA_TYPE_XY:
                        image = gaussianFilter(image,DEFINES.CC_IMAGE_XY_FILTERING_SIGMA)
                    else:
                        image = gaussianFilter(image,DEFINES.CC_IMAGE_TILT_FILTERING_SIGMA)

                    maxPxIntensity = np.max(image)

                    #Check the stopping criterias
                    if (maxPxIntensity >= DEFINES.PC_CAMERA_GET_EXPOSURE_TARGET_INTENSITY-DEFINES.PC_CAMERA_GET_EXPOSURE_INTENSITY_TOLERANCE and \
                        maxPxIntensity <= DEFINES.PC_CAMERA_GET_EXPOSURE_TARGET_INTENSITY+DEFINES.PC_CAMERA_GET_EXPOSURE_INTENSITY_TOLERANCE) or \
                        currentExposure == DEFINES.PC_CAMERA_GET_EXPOSURE_EXPOSURE_MIN or \
                        currentExposure == maxExposure:
                        nbOk += 1

                    #Check if the stopping condition is reached
                    if nbOk >= DEFINES.PC_CAMERA_GET_EXPOSURE_NB_OK:
                        return currentExposure

                    #Adapt the exposure
                    if maxPxIntensity >= DEFINES.PC_CAMERA_GET_EXPOSURE_SATURED_THRESHOLD:
                        currentExposure = currentExposure * DEFINES.PC_CAMERA_GET_EXPOSURE_TARGET_INTENSITY/maxPxIntensity*DEFINES.PC_CAMERA_GET_EXPOSURE_SATURED_GAIN #if we are satured, decrease exposure faster
                    else:
                        currentExposure = currentExposure * DEFINES.PC_CAMERA_GET_EXPOSURE_TARGET_INTENSITY/maxPxIntensity

                    if currentExposure < DEFINES.PC_CAMERA_GET_EXPOSURE_EXPOSURE_MIN:
                        currentExposure = DEFINES.PC_CAMERA_GET_EXPOSURE_EXPOSURE_MIN
                    elif currentExposure > maxExposure:
                        currentExposure = maxExposure

                    self.camHandle.ExposureTime = currentExposure
                    i = i+1


                return currentExposure
            except genicam.GenericException:
                self.connected = False
                raise errors.CameraError("Camera communication failed during optimal exposure determination")

    def setProperties(self, exposure, gain, blackLevel, gamma):
        if self.connected:
            #modify properties
            try:
                self.camHandle.ExposureTime     = exposure
                self.camHandle.Gain             = gain
                self.camHandle.BlackLevel       = blackLevel
                self.camHandle.Gamma            = gamma
            except genicam.GenericException:
                self.connected = False
                raise errors.CameraError("Camera communication failed")
        else:
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING, 0, 'Trying to set the properties of an unconnected camera')

    def setExposure(self, exposure):
        if self.connected:
            try:
                self.camHandle.ExposureTime     = exposure
            except genicam.GenericException:
                self.connected = False
                raise errors.CameraError("Camera communication failed")
        else:
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_WARNING, 0, 'Trying to set the exposure of an unconnected camera')

    def close(self):
        try:
            self.camHandle.Close()
        except genicam.GenericException:
            pass
        self.connected = False

def getAvailableCameraIDs():
    try:
        available_cameras = pypylon.TlFactory.GetInstance().EnumerateDevices()
        available_ids = []

        for i in range(0,len(available_cameras)):
            available_ids.append(int(available_cameras[i].GetSerialNumber()))
        return available_ids
    except genicam.GenericException:
        self.connected = False
        raise errors.CameraError("Camera communication failed")

def graph_heating_effect():
    import matplotlib.pyplot as plt
    from computeCentroid import compute_centroid as compute_centroid
    import classGeneral

    centroids_preheat_path = os.path.join('Python_garbage','centroids_preheat_vent.mat')
    loadFromFile = False
    image_ID = 0
    pollPeriod = 0.5 #second between two images. MIN is 0.3
    RMSFilterTimeWindow = 120 #seconds used for the RMS filter window
    preheatTime = 1*60*60 #seconds
    cooldownTime = 0*60 #seconds

    allCentroids = []
    allTimes = []
    RMSFiltered = []
    if loadFromFile:
        previousRun = io.loadmat(centroids_preheat_path)
        allCentroids = previousRun['centroids']
        allTimes = previousRun['time'][0]

    if not loadFromFile:
        log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Loading testBench')
        general = classGeneral.General()
        general.config.currentTestBenchFile = '05_XY_7bench_2'
        general.testBench.load(general.config.get_current_testBench_fileName())
        log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Initializing handles')
        general.testBench.init_handles(general.config)
        log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Initializing positioners')
        general.genericPositioner.model.clear(general.genericPositioner.physics)
        general.testBench.init_positioners(general.genericPositioner)

        log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Configuring camera')
        general.testBench.cameraXY.setMaxROI()
        completeExposure = general.testBench.cameraXY.getOptimalExposure(DEFINES.PC_CAMERA_XY_DEFAULT_EXPOSURE)
        log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Exposure time is: {completeExposure:.1f}')

        log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Setting small ROI around centroid')
        centroid = compute_centroid(general.testBench.cameraXY.getImage(), general.testBench.cameraXY.parameters, image_ID)
        ROI = np.zeros(5, dtype = np.uint16)
        ROI[0] = int(centroid[2])
        ROI[1] = int(centroid[3])
        ROI[2] = general.testBench.cameraXY.parameters.minCropWindow+20
        ROI[3] = general.testBench.cameraXY.parameters.minCropWindow
        ROI[4] = np.sqrt(ROI[2]**2+ROI[3]**2)
        general.testBench.cameraXY.setROI(ROI)

        log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Starting preheat')
        for positioner in general.testBench.positioners:
            positioner.set_current(general.testBench.canUSB, positioner.physics.maxCurrentAlpha, positioner.physics.maxCurrentBeta)

        tStart = time.time()
        #Wait until the bench is sufficiently hot
        while tStart + preheatTime > time.time():
            tSync = time.time()
            allCentroids.append(compute_centroid(general.testBench.cameraXY.getImage(), general.testBench.cameraXY.parameters, image_ID))
            allTimes.append(time.time()-tStart)
            (days, hours, minutes, seconds) = mm.decompose_time(tStart + preheatTime- time.time())
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Running ({hours:02d}h{minutes:02d}m{seconds:04.1f}s remaining)', overwritable = True)
            while tSync+pollPeriod>time.time():
                _=0

        log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Starting cooldown')
        general.testBench.set_current_all_positioners(0,0)

        while tStart + preheatTime + cooldownTime > time.time():
            tSync = time.time()
            allCentroids.append(compute_centroid(general.testBench.cameraXY.getImage(), general.testBench.cameraXY.parameters, image_ID))
            allTimes.append(time.time()-tStart)
            (days, hours, minutes, seconds) = mm.decompose_time(tStart + preheatTime + cooldownTime- time.time())
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO,0,f'Running ({hours:02d}h{minutes:02d}m{seconds:04.1f}s remaining)', overwritable = True)
            while tSync+pollPeriod>time.time():
                _=0

    allCentroids = np.asarray(allCentroids)
    allTimes = np.asarray(allTimes)

    if len(allCentroids) >= RMSFilterTimeWindow / pollPeriod:
        for i in range(0,int(len(allCentroids)-RMSFilterTimeWindow / pollPeriod)):
            mean1 = np.nanmean(allCentroids[i:int(i+RMSFilterTimeWindow / pollPeriod),0])
            mean2 = np.nanmean(allCentroids[i:int(i+RMSFilterTimeWindow / pollPeriod),1])
            err1 = allCentroids[i:int(i+RMSFilterTimeWindow / pollPeriod),0] - mean1
            err2 = allCentroids[i:int(i+RMSFilterTimeWindow / pollPeriod),1] - mean2
            RMSFiltered.append([1000*mm.nanrms(err1),1000*mm.nanrms(err2),allTimes[int(i+RMSFilterTimeWindow / pollPeriod)]])

    RMSFiltered = np.asarray(RMSFiltered)

    if not loadFromFile:
        io.savemat(centroids_preheat_path, \
                {   'centroids': allCentroids,
                    'time': allTimes,
                    'RMSFiltered': RMSFiltered})

        log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Stopping all handles')
        general.stop_all()

    log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Plotting and exiting')

    plt.figure()
    plt.plot(allTimes, allCentroids[:,0], color = 'red')
    plt.figure()
    plt.plot(allTimes, allCentroids[:,1], color = 'green')
    plt.figure()
    plt.plot(allTimes, np.sqrt(allCentroids[:,2]**2+allCentroids[:,3]**2), color = 'darkblue')
    plt.figure()
    plt.plot(RMSFiltered[:,2], RMSFiltered[:,0], color = 'orange')
    plt.figure()
    plt.plot(RMSFiltered[:,2], RMSFiltered[:,1], color = 'orange')

    plt.show()

def main():
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt
    from computeCentroid import compute_centroid as compute_centroid
    import classConfig

    # try:
    #   try:
    #       raise OSError
    #   except OSError:
    #       raise errors.CameraError("error1")

    #   try:
    #       raise OSError
    #   except OSError:
    #       raise errors.CameraError("error2")
    # except Exception as e:
    #   print(e)

    #Set the default values
    im_path = os.path.join('Python_garbage','garbage.png')

    nbCentroidsLoop = 1000
    ncComputationsPerCentroid = 1
    centroids_txt_path = os.path.join('Python_garbage','centroids.mat')

    image_ID = 1
    exposure_time = 250
    gain = 0.0
    black_level = 1.25
    gamma = 1.0

    ROI = np.zeros(5, dtype = np.uint16)

    #python grab_image.py "" "..\41000-Matlab-Calibration_and_test\calibration_data_cam1_XY.mat" 1 12345 4 11111 2 2.5 1.5 1.5
    nb_args = len(sys.argv)-1

    if nb_args > 0:
        im_path = sys.argv[1]
    if nb_args > 1:
        cam_path = sys.argv[2]
    if nb_args > 2:
        camera_ID = int(sys.argv[3])
    if nb_args > 3:
        image_ID = int(sys.argv[4])
    if nb_args > 4:
        nb_images = int(sys.argv[5])
    if nb_args > 5:
        exposure_time = float(sys.argv[6])
    if nb_args > 6:
        gain = float(sys.argv[7])
    if nb_args > 7:
        black_level = float(sys.argv[8])
    if nb_args > 8:
        gamma = float(sys.argv[9])

    if im_path != '' or image_ID > -1:
        centroid = (0,0,0,0,0,0,0,0)

        try:
            #create camera instance
            camera = Camera(cameraType = DEFINES.PC_CAMERA_TYPE_XY, compatibleCameraID=22289804) #22942361 #22994237

            #_=os.system('echo Taking picture')
            camera.setMaxROI()
            exposure_time = camera.getOptimalExposure(exposure_time)
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0, f'Exposure time is: {exposure_time:.1f}')
            if exposure_time >= DEFINES.PC_CAMERA_XY_MAX_EXPOSURE:
                log.message(DEFINES.LOG_MESSAGE_PRIORITY_ERROR, 0, f'Max exposure was reached')
                camera.close()
                return
            camera.setProperties(exposure_time, gain, black_level, gamma)

            if image_ID > -1:
                config = classConfig.Config()
                camera.setDistortionCorrection(config)

            centroids = np.zeros((nbCentroidsLoop,3))
            minimum = 1000000*np.ones(2)
            maximum = 0*np.ones(2)
            mean = 0*np.ones(2)
            std = 0*np.ones(2)

            #Get first centroid to set ROI
            picture = camera.getImage()

            #Save the image
            if im_path != '':
                mpimg.imsave(im_path,picture)

            #compute the centroid
            if image_ID > -1:
                centroid = compute_centroid(picture, camera.parameters, image_ID)

            if np.isnan(centroid[0]):
                log.message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING, 0, "No centroid detected")
                return

            ROI[0] = int(centroid[2])
            ROI[1] = int(centroid[3])
            ROI[2] = camera.parameters.minCropWindow+20
            ROI[3] = camera.parameters.minCropWindow
            ROI[4] = np.sqrt(ROI[2]**2+ROI[3]**2)

            camera.setROI(ROI)
                        print("camera params", camera.parameters)

            for i in range(0,nbCentroidsLoop):
                currentComputation = []
                for j in range(0,ncComputationsPerCentroid):
                    t0 = time.perf_counter()
                    picture = camera.getImage()

                    #Save the image
                    if im_path != '':
                        mpimg.imsave(im_path,picture)

                    #compute the centroid
                    t1 = time.perf_counter()
                    if image_ID > -1:
                        currentComputation.append(compute_centroid(picture, camera.parameters, image_ID))

                    # log.message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING, 0, f'Image: {t1-t0:4.3f} s. Centroid: {time.perf_counter()-t1:4.3f} s')

                    if np.isnan(centroid[0]):
                        log.message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING, 0, "No centroid detected")
                        raise errors.CameraError("Fiber light went out")

                currentComputation = np.array(currentComputation)
                # print(currentComputation)
                # print(currentComputation[0])
                # print(currentComputation[0,0])

                centroid = (np.mean(currentComputation[:,0]),\
                            np.mean(currentComputation[:,1]),\
                            np.mean(currentComputation[:,2]),\
                            np.mean(currentComputation[:,3]),\
                            np.mean(currentComputation[:,4]),\
                            np.mean(currentComputation[:,5]),\
                            np.mean(currentComputation[:,6]),\
                            currentComputation[0,7])

                centroids[i,2] = i
                for j in range(0,2):
                    centroids[i,j] = centroid[j]
                    if centroid[j]<minimum[j]:
                        minimum[j] = centroid[j]
                    if centroid[j]>maximum[j]:
                        maximum[j] = centroid[j]
                    mean[j] = np.mean(centroids[0:(i+1),j])
                    std[j] = np.std(centroids[0:(i+1),j])

                log.message(DEFINES.LOG_MESSAGE_PRIORITY_INFO, 0,   f'{centroid[0]:.6f},{centroid[1]:.6f},{centroid[6]:.6f}'+\
                                                                    f' Centroid {i+1:4}/{nbCentroidsLoop:4}'+\
                                                                    f' Max diff: {maximum[0]-minimum[0]:.6f},{maximum[1]-minimum[1]:.6f}'+\
                                                                    f' Mean: {mean[0]:.6f},{mean[1]:.6f}'+\
                                                                    f' STD: {std[0]:.6f},{std[1]:.6f}')


            centroids[:,0] = centroids[:,0]-np.nanmean(centroids[:,0])
            centroids[:,1] = centroids[:,1]-np.nanmean(centroids[:,1])

        except errors.CameraError as e:
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL, 0, str(e))
            log.stop()
            return

        try:
            io.savemat(centroids_txt_path, \
                {'centroids': centroids})
        except OSError as e:
            log.message(DEFINES.LOG_MESSAGE_PRIORITY_CRITICAL, 0, str(e))
            log.stop()
            return

        camera.close()

        plt.figure()

        plt.scatter(centroids[:,0], centroids[:,1], color = 'red',marker = 'x', s = 1)
        plt.show()

if __name__ == '__main__':
    log.init()
    #graph_heating_effect()
    main()
    log.stop()
