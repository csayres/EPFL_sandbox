# import classTestBench as tb
import DEFINES
import classCamera as cam
import matplotlib.image as mpimg
import classConfig

exposure_time = 4748.3 # says the optimal exposure time calculator?
gain = 0.0
black_level = 1.25
gamma = 1.0
filename = "outfile.tiff"

if __name__ == "__main__":
    # camCfgFile = "Config/Cameras/camera_22289804.mat" # this lives on tendo only, it's large
    camera = cam.Camera(cameraType = DEFINES.PC_CAMERA_TYPE_XY, compatibleCameraID=22289804) #22942361 #22994237
    camera.setMaxROI()
    config = classConfig.Config()
    camera.setDistortionCorrection(config)
    # camera.setDistortionCorrection(camCfgFile)
    camera.setProperties(exposure_time, gain, black_level, gamma)
    picture = camera.getImage()
    mpimg.imsave(filename,picture)
    # import pdb; pdb.set_trace()