from scipy import io
import numpy

import DEFINES
import classConfig
import classCamera as cam

exposure_time = 4748.3
gain = 0.0
black_level = 1.25
gamma = 1.0

DETECT_THRESH = 200 # counts for detection threshold


def getDistortion():
    cam_distortion = io.loadmat("/home/tendo/work/python/EPFL_sandbox/calibLoic/Config/Cameras/camera_22289804.mat")
    cam_distortion = cam_distortion[DEFINES.PC_FILE_DISTORTION_PARAMETERS_NAME]
    # correction matrices are in pixels
    cam_x_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_XCORR_NAME]
    cam_y_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_YCORR_NAME]
    # scale factor is microns per pixel
    cam_scale_factor = cam_distortion[DEFINES.PC_FILE_DISTORTION_SCALE_FACTOR_NAME]
    xCorr = numpy.nan_to_num(cam_x_corr[0,0])
    yCorr = numpy.nan_to_num(cam_y_corr[0,0])
    scale_factor = cam_scale_factor[0,0][0,0]
    return scale_factor, xCorr, yCorr


def getCamera():
    camera = cam.Camera(cameraType = DEFINES.PC_CAMERA_TYPE_XY, compatibleCameraID=22289804) #22942361 #22994237
    camera.setMaxROI()
    config = classConfig.Config()
    camera.setDistortionCorrection(config)
    camera.setProperties(exposure_time, gain, black_level, gamma)
    return camera

SCALE_FACTOR, XCORR, YCORR = getDistortion()
camera = getCamera()

