# import classTestBench as tb
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from astropy.io import fits
from scipy import io
import numpy

exposure_time = 4748.3 # says the optimal exposure time calculator?
gain = 0.0
black_level = 1.25
gamma = 1.0
baseImg = "img/img"
fileCounter = 0
# camCfgFile = "Config/Cameras/camera_22289804.mat"

##### camera distortion stuff ####################
# import DEFINES
# import classConfig
# import classCamera as cam
# cam_distortion = io.loadmat("Config/Cameras/camera_22289804.mat")
# cam_distortion = cam_distortion[DEFINES.PC_FILE_DISTORTION_PARAMETERS_NAME]
# cam_x_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_XCORR_NAME]
# cam_y_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_YCORR_NAME]
# cam_scale_factor = cam_distortion[DEFINES.PC_FILE_DISTORTION_SCALE_FACTOR_NAME]
# xCorr = numpy.nan_to_num(cam_x_corr[0,0])
# yCorr = numpy.nan_to_num(cam_y_corr[0,0])
# scaleFactor = cam_scale_factor[0,0][0,0]

######### camera controller #########################
# camera = cam.Camera(cameraType = DEFINES.PC_CAMERA_TYPE_XY, compatibleCameraID=22289804) #22942361 #22994237
# camera.setMaxROI()
# config = classConfig.Config()
# camera.setDistortionCorrection(config)
# camera.setProperties(exposure_time, gain, black_level, gamma)

########## PyGuide #####################################


def expose():
    # camCfgFile = "Config/Cameras/camera_22289804.mat" # this lives on tendo only, it's large
    import DEFINES
    import classConfig
    import classCamera as cam
    cam_distortion = io.loadmat("Config/Cameras/camera_22289804.mat")
    cam_distortion = cam_distortion[DEFINES.PC_FILE_DISTORTION_PARAMETERS_NAME]
    # correction matrices are in pixels
    cam_x_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_XCORR_NAME]
    cam_y_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_YCORR_NAME]
    # scale factor is microns per pixel
    cam_scale_factor = cam_distortion[DEFINES.PC_FILE_DISTORTION_SCALE_FACTOR_NAME]
    xCorr = numpy.nan_to_num(cam_x_corr[0,0])
    yCorr = numpy.nan_to_num(cam_y_corr[0,0])
    # invert correlation mats so that 0,0 is bottom left instead of top left
    xCorr = xCorr[::-1,:]
    # multiply xCorrections by -1 because we inverted that axis?
    xCorr = xCorr * -1.0
    yCorr = yCorr[::-1,:]
    scaleFactor = cam_scale_factor[0,0][0,0]
    camera = cam.Camera(cameraType = DEFINES.PC_CAMERA_TYPE_XY, compatibleCameraID=22289804) #22942361 #22994237
    camera.setMaxROI()
    config = classConfig.Config()
    camera.setDistortionCorrection(config)
    camera.setProperties(exposure_time, gain, black_level, gamma)
    imgData = camera.getImage()
    # invert image so that 0,0 is bottom left, ds9 displays
    # things in the way we see it
    imgData = imgData[::-1,:]
    return imgData

def findCentroids(imgData, xyCtrs, roiRadius=50):
    # xyCtrs [[x1,y1], [x2,y2]] pixels
    # roiRadius for making mask, put squares of width roiWidth/2
    # on expected positions of centroids
    import PyGuide
    CCDInfo = PyGuide.CCDInfo(
        bias = 2,    # image bias, in ADU
        readNoise = 2, # read noise, in e-
        ccdGain = 2,  # inverse ccd gain, in e-/ADU
    )

    mask = numpy.zeros(imgData.shape) + 1 # 1 is invalid data
    for xCtr,yCtr in xyCtrs:
        # be careful drawing mask first index is image rows in imgData
        # second index is image columns (x pixels)
        xCtr = int(numpy.floor(xCtr))
        yCtr = int(numpy.floor(yCtr))
        startRow = xCtr - roiRadius
        if startRow < 0:
            startRow = 0
        endRow = xCtr + roiRadius
        if endRow > imgData.shape[1]:
            endRow = imgData.shape[1]

        startCol = yCtr - roiRadius
        if startCol < 0:
            startCol = 0
        endCol = yCtr + roiRadius
        if endCol > imgData.shape[0]:
            endCol = imgData.shape[0]

        mask[startCol:endCol, startRow:endRow] = 0

    ctrDataList, imStats = PyGuide.findStars(
        data = imgData,
        mask = mask,
        satMask = None,
        thresh=200,
        ccdInfo = CCDInfo,
        verbosity = 0,
        doDS9 = False,
    )[0:2]
    return ctrDataList


def writeImg(imgData):
    hdu = fits.PrimaryHDU(imgData)
    hdu.writeto("img.fits", overwrite=True)

if __name__ == "__main__":
    # imgData = expose()
    f = fits.open("img.fits")
    imgData = f[0].data
    f.close()
    # plt.imshow(imgData, origin="lower")
    # plt.plot()
    # plt.show()

    ctrDataList = findCentroids(imgData, [[1356.19, 1334.28]]) #
    # ctrDataList = findCentroids(imgData, [[1356.19, 2720]])

    for ctrData in ctrDataList:
        xyCtr = ctrData.xyCtr
        rad = ctrData.rad
        counts = ctrData.counts
        print("star xyCtr=%.2f, %.2f, radius=%s counts=%.2f" % (xyCtr[0], xyCtr[1], rad, counts))

    # f.close()
    # writeImg(imgData)
