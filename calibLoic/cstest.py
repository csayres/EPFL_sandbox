import classTestBench as tb
import DEFINES
import classCamera as cam

if __name__ == "__main__":
    camCfgFile = "Config/Cameras/camera_22289804.mat" # this lives on tendo only, it's large
    camera = cam.Camera(DEFINES.PC_CAMERA_TYPE_XY)
    camera.setDistortionCorrection(camCfgFile)
    import pdb; pdb.set_trace()