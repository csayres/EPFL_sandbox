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
    cam_x_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_XCORR_NAME]
    cam_y_corr = cam_distortion[DEFINES.PC_FILE_DISTORTION_YCORR_NAME]
    cam_scale_factor = cam_distortion[DEFINES.PC_FILE_DISTORTION_SCALE_FACTOR_NAME]
    xCorr = numpy.nan_to_num(cam_x_corr[0,0])
    yCorr = numpy.nan_to_num(cam_y_corr[0,0])
    scaleFactor = cam_scale_factor[0,0][0,0]
    camera = cam.Camera(cameraType = DEFINES.PC_CAMERA_TYPE_XY, compatibleCameraID=22289804) #22942361 #22994237
    camera.setMaxROI()
    config = classConfig.Config()
    camera.setDistortionCorrection(config)
    camera.setProperties(exposure_time, gain, black_level, gamma)
    imgData = camera.getImage()
    print("imgData shape", imgData.shape)
    hdu = fits.PrimaryHDU(imgData)
    hdu.writeto("img.fits")

    # mpimg.imsave(filename,picture)

def findCentroids(imgData):
    import PyGuide
    CCDInfo = PyGuide.CCDInfo(
        bias = 2,    # image bias, in ADU
        readNoise = 2, # read noise, in e-
        ccdGain = 2,  # inverse ccd gain, in e-/ADU
    )
    # 1598, 1313 measured in ds9 from 0,0 at bottom left
    # img = mpimg.imread("outfile.tiff")
    # print(img.shape)
    # img = img[::-1,:, 0]
    # plt.imshow(img, origin="lower")
    # plt.show()
    mask=None
    ctrDataList, imStats = PyGuide.findStars(
        data = imgData,
        mask = mask,
        satMask = None,
        ccdInfo = CCDInfo,
        verbosity = 0,
        doDS9 = False,
    )[0:2]
    for ctrData in ctrDataList:
        xyCtr = ctrData.xyCtr
        rad = ctrData.rad
        print("star xyCtr=%.2f, %.2f, radius=%s" % (xyCtr[0], xyCtr[1], rad))

if __name__ == "__main__":
    expose()
