class Error(Exception):
	"""Base class for custom errors"""

class IOError(Error):
	"""Error raised if a file reading or writing produces an error"""

class OutOfRangeError(Error):
	"""Error raised if a value passed as argument is out of range"""

class CameraError(Error):
	"""Error raised when the camera encountered an error"""

class CANError(Error):
	"""Error raised when the CAN communication encountered an error"""

class PositionerError(Error):
	"""Error raised when a positioner is in an incorrect state"""

class CalibrationError(Error):
	"""Error raised when a calibration failed"""

class TestError(Error):
	"""Error raised when a test failed"""
