#cython: language_level=3
import serial
import time
from serial.tools import list_ports
import DEFINES
import errors

class StatusRegistery:
# 	# Status register bits for system
# 	SYSTEM_INITIALIZED				= 0x0000000000000001
# 	CONFIG_CHANGED					= 0x0000000000000002
# 	BSETTINGS_CHANGED				= 0x0000000000000004
# 	DATA_STREAMING					= 0x0000000000000008

# 	# Status register bits for communication
# 	RECEIVING_TRAJECTORY			= 0x0000000000000010
# 	TRAJECTORY_ALPHA_RECEIVED		= 0x0000000000000020
# 	TRAJECTORY_BETA_RECEIVED		= 0x0000000000000040
# 	LOW_POWER_AFTER_MOVE			= 0x0000000000000080

# 	# Status register bits for positioning
# 	DISPLACEMENT_COMPLETED			= 0x0000000000000100
# 	DISPLACEMENT_COMPLETED_ALPHA	= 0x0000000000000200
# 	DISPLACEMENT_COMPLETED_BETA		= 0x0000000000000400
# 	COLLISION_ALPHA					= 0x0000000000000800
# 	COLLISION_BETA					= 0x0000000000001000
# 	CLOSED_LOOP_ALPHA				= 0x0000000000002000
# 	CLOSED_LOOP_BETA				= 0x0000000000004000
# 	PRECISE_POSITIONING_ALPHA		= 0x0000000000008000
# 	PRECISE_POSITIONING_BETA		= 0x0000000000010000
# 	COLLISION_DETECT_ALPHA_DISABLE	= 0x0000000000020000
# 	COLLISION_DETECT_BETA_DISABLE	= 0x0000000000040000
	
# 	MOTOR_CALIBRATION				= 0x0000000000080000
# 	MOTOR_ALPHA_CALIBRATED			= 0x0000000000100000
# 	MOTOR_BETA_CALIBRATED			= 0x0000000000200000
# 	DATUM_CALIBRATION				= 0x0000000000400000
# 	DATUM_ALPHA_CALIBRATED			= 0x0000000000800000
# 	DATUM_BETA_CALIBRATED			= 0x0000000001000000
# 	DATUM_INITIALIZATION			= 0x0000000002000000
# 	DATUM_ALPHA_INITIALIZED			= 0x0000000004000000
# 	DATUM_BETA_INITIALIZED			= 0x0000000008000000
# 	HALL_ALPHA_DISABLE				= 0x0000000010000000
# 	HALL_BETA_DISABLE				= 0x0000000020000000

	COGGING_CALIBRATION				= 0x0000000040000000
# 	COGGING_ALPHA_CALIBRATED		= 0x0000000080000000
# 	COGGING_BETA_CALIBRATED			= 0x0000000100000000

# 	ESTIMATED_POSITION				= 0x0000000200000000
# 	POSITION_RESTORED				= 0x0000000400000000

	# Status register bits for system */
	SYSTEM_INITIALIZED 				= 0x00000001
	CONFIG_CHANGED 					= 0x00000002
	BSETTINGS_CHANGED 				= 0x00000004
	DATA_STREAMING 					= 0x00000008

	# Status register bits for communication */
	SYSTEM_INITIALIZATION 			= 0x00000001
	RECEIVING_TRAJECTORY 			= 0x00000100
	TRAJECTORY_ALPHA_RECEIVED 		= 0x00000200
	TRAJECTORY_BETA_RECEIVED 		= 0x00000400

	# Status register bits for positioning */
	DATUM_INITIALIZATION 			= 0x00200000
	DATUM_ALPHA_INITIALIZED 		= 0x00400000
	DATUM_BETA_INITIALIZED 			= 0x00800000
	DISPLACEMENT_COMPLETED 			= 0x01000000
	ALPHA_DISPLACEMENT_COMPLETED 	= 0x02000000
	BETA_DISPLACEMENT_COMPLETED 	= 0x04000000
	DATUM_INITIALIZED 				= 0x20000000
	ESTIMATED_POSITION 				= 0x40000000
	POSITION_RESTORED 				= 0x80000000
	
class CAN_Options:
	CAN_BAUDRATE 		= 1000000	#Baud rate
	CAN_BUFFER 			= 2**16		#Data buffer size
	CAN_TIMEOUT 		= 2			#Maximal answer waiting time [s]
	CAN_VCP_PORT		= -1		#Default initialization
	CAN_ID_BIT_SHIFT 	= 18		#Bits to shift to get ID
	CAN_CMD_BIT_SHIFT 	= 10		#Bits to shift to input the command
	TimeChannelSize		= 4			#Data size [byte]
	DataChannelNumel	= 5			#Number of channels
	DataChannelSize		= 4			#Data size [byte]
	PacketSize			= TimeChannelSize + DataChannelNumel*DataChannelSize

class RX_Options:
	# List of commands
	ABORT_ALL						= 0		# abort all
	GET_ID							= 1		# requests positioner ID
	GET_FIRMWARE_VERSION			= 2		# requests actual firmware version of positioner
	GET_STATUS						= 3		# requests for deviceStatus register
	SET_STATUS_LOW					= 4		# set status registers, low bits
	SET_STATUS_HIGH					= 5		# set status registers, high bits
	SEND_TRAJECTORY_NEW				= 10	# request for sending a new trajectory
	SEND_TRAJECTORY_DATA			= 11	# sends trajectory points (int32_t position, uint32_t time)
	SEND_TRAJECTORY_DATA_END		= 12	# sends end trajectory transmission to validate sent trajectories
	SEND_TRAJECTORY_ABORT			= 13	# aborts trajectory transmission, will reset all trajectories stored 
	START_TRAJECTORY				= 14	# starts actual trajectory
	STOP_TRAJECTORY					= 15	# stops actual trajectory
	INIT_DATUM						= 20	# init datums
	INIT_DATUM_ALPHA				= 21	# init datum alpha
	INIT_DATUM_BETA					= 22	# init datum beta
	START_DATUM_CALIBRATION			= 23	# calib datums
	START_DATUM_CALIBRATION_ALPHA	= 24	# calib datum alpha
	START_DATUM_CALIBRATION_BETA	= 25	# calib datum beta
	START_MOTOR_CALIBRATION			= 26	# 
	START_MOTOR_CALIBRATION_ALPHA	= 27	# 
	START_MOTOR_CALIBRATION_BETA	= 28	# 
	GOTO_POSITION_ABSOLUTE			= 30	# goto absolute position
	GOTO_POSITION_RELATIVE			= 31	# goto absolute position
	GET_ACTUAL_POSITION				= 32	# requests actual position
	SET_ACTUAL_POSITION				= 33	# sets the actual position
	GET_OFFSET						= 34
	SET_OFFSET						= 35
	START_PRECISE_MOVE				= 36	# start precise maneuver
	START_PRECISE_MOVE_ALPHA		= 37	# start precise maneuver alpha
	START_PRECISE_MOVE_BETA			= 38	# start precise maneuver beta
	SET_SPEED						= 40	# sets movement speed in rpm
	SET_CURRENT						= 41	# sets the open loop current
	GET_MOTOR_HALL_POS				= 44	# hall 
	GET_MOTOR_CALIBRATION_ERROR		= 45	# get hall calibration error
	RESET_All_POSITIONS				= 46	# set all positions to 0: offset, actualposition, commandedposition hardstop_offset
	START_COGGING_CALIBRATION		= 47	# 
	START_COGGING_CALIBRATION_ALPHA	= 48	# 
	START_COGGING_CALIBRATION_BETA	= 49	# 

	STOP_DATA_STREAMING				= 51	# stops the data stream

	#list of return codes
	COMMAND_ACCEPTED				= 0		# command accepted
	VALUE_OUT_OF_RANGE				= 1		# value out of range
	INVALID_TRAJECTORY				= 2		# invalid trajectory
	ALREADY_IN_MOTION				= 3		# already in motion
	NOT_INITIALIZED					= 4		# not initialized
	INCORRECT_AMOUNT_OF_DATA		= 5		# incorrect amount of data received
	INVALID_BROADCAST_COMMAND		= 10	# invalid broadcast command
	INVALID_BOOTLOADER_COMMAND		= 11	# invalid bootloader command
	INVALID_COMMAND					= 12	# invalid command
	UNKNOWN_COMMAND					= 13	# unknown command
	
class COM_Options:
	COM	= CAN_Options()
	RX	= RX_Options()
	STREG	= StatusRegistery()

class COM_handle:
	__slots__	= (	'_OPT',\
					'serHandle',\
					'serialNo',\
					'initialized')

	def __init__(self):
		self._OPT	= COM_Options()
		self.serHandle	= None
		self.serialNo	= []

	def get_all_serial_no(self):
		"""Returns all the available connected CAN-USB transievers serial numbers"""
		#Get available COM ports
		serialNumbers	= []
		serial_list	= list(list_ports.comports())
		if not serial_list:
			return serialNumbers

		serialHandle = None

		#Get COM port which description corresponds to 'USB' that are not already opened
		for port_no, description, device in serial_list:
			if 'USB' in description:
				try:
					serialHandle	= serial.Serial(port_no)
				except serial.SerialException:
					pass
				
				if serialHandle is not None:
					try:
						#Retrieve the serial number
						serialHandle.reset_input_buffer()
						serialHandle.write('N\r'.encode())
						time.sleep(0.5)
						input_buffer	= serialHandle.readline(serialHandle.inWaiting())
						#store the serial number
						if len(input_buffer.decode())	== 6:
							result	= str(input_buffer[1:5].decode())
							serialNumbers.append(result)

						serialHandle.close()
					except serial.SerialException:
						pass

		return serialNumbers

	def init(self, desiredSerial	= ''):
		#Reset values
		if self.serHandle is None or not (self.serialNo	== desiredSerial):
			#If a CAN-USB is already connected, close the connexion
			if self.serHandle is not None:
				self.close()			

			#Get available COM ports
			serial_list	= list(list_ports.comports())
			if not serial_list:
				raise errors.CANError("No COM port available") from None

			#Get COM port which description corresponds to 'USB' and with the desired serial number
			for port_no, description, device in serial_list:
				if 'USB' in description:
					try:
						self.serHandle	= serial.Serial(port_no)
					except serial.SerialException:
						self.serHandle	= None

					if self.serHandle is not None: #If the connexion was successful
						try:
							serialNo	= self.CAN_write(0,'getserialnumber',[])
						except errors.CANError as e:
							self.close()
							# raise e from None
						else:
							if serialNo[0]	== desiredSerial or desiredSerial	== '':
								self.serialNo	= serialNo[0]
								self._OPT.COM.CAN_VCP_PORT	= port_no
								break
							self.close()		

			#If no device matches the description, exit
			if self.serHandle is None:
				raise errors.CANError("CAN initialization could not connect to the requested device") from None

			#Initialize the serial port parameters
			try:
				self.serHandle.baudrate	= self._OPT.COM.CAN_BAUDRATE
				self.serHandle.bytesize	= serial.EIGHTBITS
				self.serHandle.timeout	= self._OPT.COM.CAN_TIMEOUT

				#flush all the buffers
				self.CAN_write(0,'clearbuffer',[])

				#Initialize the CAN bus
				self.CAN_write(0,'init',[])
			except errors.CANError as e:
				self.close()
				raise e from None

	#Closes the CAN communication
	def close(self):
		if self.serHandle is not None:
			try:
				self.serHandle.close()
			except serial.SerialException:
				pass
		self.serHandle	= None
		self.serialNo	= ''

	#Sends a command via the CAN bus
	#Returns the received data
	def CAN_write(self, ID, command, data):
		Output	= []

		try:
			if self.serHandle is not None:		
				#command is not case sensitive
				command	= command.lower()
				#Convert ID to usable adress
				positionerID	= ID
				ID	= ID<<self._OPT.COM.CAN_ID_BIT_SHIFT

				if command	== 'init':#-------------------------------------------------------
					self.serHandle.reset_input_buffer()

					#Close the CAN channel
					self.serHandle.write('C\r'.encode())#C\r
					time.sleep(0.1)
					self.serHandle.reset_input_buffer()
					#Set the Baud rate to 1Mb/s
					self.serHandle.write('S8\r'.encode())#S8\r

					time.sleep(0.1)

					input_buffer	= self.serHandle.readline(self.serHandle.inWaiting())
					if input_buffer.decode() != '\r':
						raise errors.CANError('CAN could not configure the baud rate') from None
					else:
						#Reopen CAN channel
						self.serHandle.reset_input_buffer()
						self.serHandle.write('O\r'.encode())#O\r
						time.sleep(0.1)
						#Check for correct communication
						input_buffer	= self.serHandle.readline(self.serHandle.inWaiting())
						if input_buffer.decode() != '\r':
							raise errors.CANError('CAN channel could not be reopened') from None
				
				elif command	== 'getserialnumber':#----------------------------------------
					self.serHandle.reset_input_buffer()
					#Retrieve the serial number
					self.serHandle.write('N\r'.encode())#C\r
					time.sleep(0.5)
					input_buffer	= self.serHandle.readline(self.serHandle.inWaiting())
					if not len(input_buffer.decode())	== 6:
						raise errors.CANError("CAN could not retrieve the transceiver's serial number") from None
					else:
						Output.append(str(input_buffer[1:5].decode()))

				elif command	== 'askid':#---------------------------------------------------
					self.serHandle.reset_input_buffer()
					#Ask for ID
					#t(ID)l(OPT)\r

					txCmd	= (self._OPT.RX.GET_ID<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#T(ID<<18+OPT<<8)\r
					#self.serHandle.write(('7400010F0D').encode())#t(ID)1(OPT)\r
					
					time.sleep(0.5)			

					input_buffer=self.serHandle.read(self.serHandle.inWaiting())#get whole input buffer

					if not ((len(input_buffer.decode())-2)%19	== 0):
						raise errors.CANError('CAN AskID received a wrong response')
					# elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
					# 	raise errors.CANError('CAN AskID command was not accepted by the positioner')
					else:
						#treat the CAN frame to extract the IDs
						start	= 12 #response is in the form b'T(ID)4(data). We extract the data.
						for i in range(0,int((len(input_buffer)-2)/19)):
							current_Byte	= start + i*19
							if not int(input_buffer[current_Byte-2:current_Byte-1],16)	== self._OPT.RX.COMMAND_ACCEPTED:
								raise errors.CANError('CAN AskID command was not accepted') from None
							else:
								Output.append(swapInt32(int(input_buffer[current_Byte:(current_Byte+8)],16)))

				elif command == 'initdatum':
					self.serHandle.reset_input_buffer()

					txCmd	= (self._OPT.RX.INIT_DATUM<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#T(txCmd)\r

					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting())#get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN InitDatum received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN InitDatum command was not accepted by the positioner with ID {positionerID:04d}') from None

				elif command	== 'starttrajectory':#-----------------------------------------
					self.serHandle.reset_input_buffer()

					txCmd	= (self._OPT.RX.START_TRAJECTORY<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#T(txCmd)\r

					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting())#get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN StartTrajectory received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError('CAN StartTrajectory command was not accepted by the positioner with ID {positionerID:04d}') from None

				elif command	== 'stoptrajectory':#------------------------------------------
					self.serHandle.reset_input_buffer()

					txCmd	= (self._OPT.RX.STOP_TRAJECTORY<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#T(txCmd)\r

					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting())#get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN StopTrajectory received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN StopTrajectory command was not accepted by the positioner with ID {positionerID:04d}') from None
						
				
				elif command	== 'statusregrequest' or command	== 'statusrequest':#----------
					self.serHandle.reset_input_buffer()

					txCmd	= (self._OPT.RX.GET_STATUS<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#T(txCmd)\r

					#FOR 64b REGISTER OF v4
					# #time.sleep(0.025)
					# watchdog	= time.perf_counter()
					# while self.serHandle.inWaiting()<29 and time.perf_counter()-0.1 < watchdog:
					# 	_=1

					# input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					# if not len(input_buffer.decode())	== 29:
					# 	raise errors.CANError(f'CAN StatutRequest received a wrong response from positioner {positionerID:04d}') from None
					# elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
					# 	raise errors.CANError(f'CAN StatutRequest command was not accepted by the positioner with ID {positionerID:04d}') from None
					# else:
					# 	Output.append(swapInt64(int(input_buffer[12:28],16)))

					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<21 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting())#get whole input buffer
					if not len(input_buffer.decode())	== 21:
						raise errors.CANError(f'CAN StatutRequest received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN StatutRequest command was not accepted by the positioner with ID {positionerID:04d}') from None
					else:
						Output.append(swapInt32(int(input_buffer[12:20],16)))

				elif command	== 'clearbuffer':#---------------------------------------------
					self.serHandle.reset_input_buffer()
					self.serHandle.reset_output_buffer()
				
				elif command	== 'readbuffer' or command	== 'readdata':#---------------------
					input_buffer=self.serHandle.read(self.serHandle.inWaiting())
					Output.append(input_buffer)
				
				elif command	== 'set_speed':#--------------------------------------
					self.serHandle.reset_input_buffer()

					#unsign the command
					data['SpeedAlpha'] 	= data['SpeedAlpha']%(2**32)
					data['SpeedBeta'] 	= data['SpeedBeta']%(2**32)

					#cast to hex
					alphaSpeedCommand 	= '%0.8X' % swapInt32((data['SpeedAlpha']))
					betaSpeedCommand 	= '%0.8X' % swapInt32((data['SpeedBeta']))
					#Create command
					txCmd	= (self._OPT.RX.SET_SPEED<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'8'+alphaSpeedCommand+betaSpeedCommand+'\r').encode())#t(ID)4(data)\r
					
					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN SetSpeed received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN SetSpeed command was not accepted by the positioner with ID {positionerID:04d}') from None
											
				elif command	== 'set_position' or command	== 'set_actual_position':#--------------------------------------
					self.serHandle.reset_input_buffer()

					#unsign the command
					data['Actual_alpha_pos']	= data['Actual_alpha_pos']%(2**32)
					data['Actual_beta_pos']	= data['Actual_beta_pos']%(2**32)

					#cast to hex
					alphaRefCommand	= '%0.8X' % (swapInt32(data['Actual_alpha_pos']))
					betaRefCommand	= '%0.8X' % (swapInt32(data['Actual_beta_pos']))

					#Create command
					txCmd	= (self._OPT.RX.SET_ACTUAL_POSITION<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'8'+alphaRefCommand+betaRefCommand+'\r').encode())#t(ID)4(data)\r

					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN SetPosition received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						print(int(input_buffer[10:11],16))
						raise errors.CANError(f'CAN SetPosition command was not accepted by the positioner with ID {positionerID:04d}') from None
					
				elif command	== 'gotoposition_speed':#--------------------------------------
					self.serHandle.reset_input_buffer()

					#unsign the command
					data['R1Steps']	= data['R1Steps']%(2**32)
					data['R2Steps']	= data['R2Steps']%(2**32)

					#cast to hex
					R1StepsCommand	= '%0.8X' % (swapInt32(data['R1Steps']))
					R2StepsCommand	= '%0.8X' % (swapInt32(data['R2Steps']))

					#Create command
					txCmd	= (self._OPT.RX.GOTO_POSITION_ABSOLUTE<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'8'+R1StepsCommand+R2StepsCommand+'\r').encode())#t(ID)4(data)\r

					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<29 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 29:
						raise errors.CANError(f'CAN GoToPosition received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN GoToPosition command was not accepted by the positioner with ID {positionerID:04d}') from None
					else:
						Output.append(swapInt32(int(input_buffer[12:20],16))/DEFINES.CANCOM_FIRMWARE_CONTROL_LOOP_FREQUENCY) #Time needed for movement of axis alpha. 2000[Hz] is the frequency of the control loop.
						Output.append(swapInt32(int(input_buffer[20:28],16))/DEFINES.CANCOM_FIRMWARE_CONTROL_LOOP_FREQUENCY) #Time needed for movement of axis beta. 2000[Hz] is the frequency of the control loop.
				
				elif command	== 'get_position' or command	== 'get_actual_position':#--------------------------------------
					self.serHandle.reset_input_buffer()

					#Create command
					txCmd	= (self._OPT.RX.GET_ACTUAL_POSITION<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#t(ID)4(data)\r

					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<29 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 29:
						raise errors.CANError(f'CAN GetPosition received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN GetPosition command was not accepted by the positioner with ID {positionerID:04d}') from None
					else:
						R1_steps	= swapInt32(int(input_buffer[12:20],16))
						R2_steps	= swapInt32(int(input_buffer[20:28],16))
						if R1_steps > 2**31:
							R1_steps -= 2**32
						if R2_steps > 2**31:
							R2_steps -= 2**32
						Output.append(R1_steps) #R1 steps
						Output.append(R2_steps) #R2 steps

				elif command	== 'get_pos_hall':#--------------------------------------
					self.serHandle.reset_input_buffer()

					#Create command
					txCmd	= (self._OPT.RX.GET_MOTOR_HALL_POS<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#t(ID)4(data)\r

					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<29 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 29:
						raise errors.CANError(f'CAN GetHallPosition received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN GetHallPosition command was not accepted by the positioner with ID {positionerID:04d}') from None
					else:
						R1_steps	= swapInt32(int(input_buffer[12:20],16))
						R2_steps	= swapInt32(int(input_buffer[20:28],16))
						if R1_steps > 2**31:
							R1_steps -= 2**32
						if R2_steps > 2**31:
							R2_steps -= 2**32
						Output.append(R1_steps) #R1 steps
						Output.append(R2_steps) #R2 steps

				elif command	== 'setopenloopcurrent':#--------------------------------------
					self.serHandle.reset_input_buffer()

					if data['currentAlpha'] < 0:
						data['currentAlpha']	= 0
					elif data['currentAlpha'] > 1024:
						data['currentAlpha']	= 1024
					if data['currentBeta'] < 0:
						data['currentBeta']	= 0
					elif data['currentBeta'] > 1024:
						data['currentBeta']	= 1024

					txCmd	= (self._OPT.RX.SET_CURRENT<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					alphaCurrentCommand	= '%0.8X' % (swapInt32(data['currentAlpha'])) #convert to hex
					betaCurrentCommand	= '%0.8X' % (swapInt32(data['currentBeta']))

					self.serHandle.write(('T'+txCmd+'8'+alphaCurrentCommand+betaCurrentCommand+'\r').encode())#t(ID)1(OPT)\r
					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting())#get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN SetCurrent received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN SetCurrent command was not accepted by the positioner with ID {positionerID:04d}') from None
					
				elif command	== 'start_motor_calibration':
					self.serHandle.reset_input_buffer()

					#Create command
					txCmd	= (self._OPT.RX.START_MOTOR_CALIBRATION<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#t(ID)4(data)\r
					
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN StartMotorCalibration received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN StartMotorCalibration command was not accepted by the positioner with ID {positionerID:04d}') from None

				elif command	== 'get_motor_calibration_error':
					self.serHandle.reset_input_buffer()

					#Create command
					txCmd	= (self._OPT.RX.GET_MOTOR_CALIBRATION_ERROR<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#t(ID)4(data)\r

					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<29 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 29:
						raise errors.CANError(f'CAN GetMotorCalibrtionError received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN GetMotorCalibrtionError command was not accepted by the positioner with ID {positionerID:04d}') from None
					else:
						R1_steps	= swapInt32(int(input_buffer[12:20],16))
						R2_steps	= swapInt32(int(input_buffer[20:28],16))
						if R1_steps > 2**31:
							R1_steps -= 2**32
						if R2_steps > 2**31:
							R2_steps -= 2**32
						Output.append(R1_steps) #R1 steps
						Output.append(R2_steps) #R2 steps

				elif command	== 'start_datum_calibration':
					self.serHandle.reset_input_buffer()

					#Create command
					txCmd	= (self._OPT.RX.START_DATUM_CALIBRATION<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#t(ID)4(data)\r
					
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN StartDatumCalibration received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN StartDatumCalibration command was not accepted by the positioner with ID {positionerID:04d}') from None
					
				elif command	== 'start_cogging_calibration':
					self.serHandle.reset_input_buffer()

					#Create command
					txCmd	= (self._OPT.RX.START_COGGING_CALIBRATION<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#t(ID)4(data)\r
					
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN StartCoggingCalibration received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN StartCoggingCalibration command was not accepted by the positioner with ID {positionerID:04d}') from None
										
				elif command	== 'get_offset':
					self.serHandle.reset_input_buffer()

					#Create command
					txCmd	= (self._OPT.RX.GET_OFFSET<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'0'+'\r').encode())#t(ID)4(data)\r

					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<29 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 29:
						raise errors.CANError(f'CAN GetOffset received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN GetOffset command was not accepted by the positioner with ID {positionerID:04d}') from None
					
					else:
						R1_steps	= swapInt32(int(input_buffer[12:20],16))
						R2_steps	= swapInt32(int(input_buffer[20:28],16))
						if R1_steps > 2**31:
							R1_steps -= 2**32
						if R2_steps > 2**31:
							R2_steps -= 2**32
						Output.append(R1_steps) #R1 steps
						Output.append(R2_steps) #R2 steps

				elif command	== 'set_offset':
					self.serHandle.reset_input_buffer()

					#unsign the command
					data['alpha_offset']	= data['alpha_offset']%(2**32)
					data['beta_offset']	= data['beta_offset']%(2**32)

					#cast to hex
					alphaRefCommand	= '%0.8X' % (swapInt32(data['alpha_offset']))
					betaRefCommand	= '%0.8X' % (swapInt32(data['beta_offset']))

					#Create command
					txCmd	= (self._OPT.RX.SET_OFFSET<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					txCmd	= '%0.8X' % txCmd

					#send command
					self.serHandle.write(('T'+txCmd+'8'+alphaRefCommand+betaRefCommand+'\r').encode())#t(ID)4(data)\r

					#time.sleep(0.025)
					watchdog	= time.perf_counter()
					while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
						_=1

					input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					if not len(input_buffer.decode())	== 13:
						raise errors.CANError(f'CAN SetOffset received a wrong response from positioner {positionerID:04d}') from None
					elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
						raise errors.CANError(f'CAN SetOffset command was not accepted by the positioner with ID {positionerID:04d}') from None

				elif command	== 'enable_closed_loop':
					# self.serHandle.reset_input_buffer()

					# #cast to hex
					# regSet	= 0x00000000 | self._OPT.STREG.CLOSED_LOOP_ALPHA | self._OPT.STREG.CLOSED_LOOP_BETA
					# regClear	= 0x00000000

					# regSetCommand	= '%0.8X' % (swapInt32(regSet))
					# regClearCommand	= '%0.8X' % (swapInt32(regClear))

					# #Create command
					# txCmd	= (self._OPT.RX.SET_STATUS_LOW<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					# txCmd	= '%0.8X' % txCmd

					# #send command
					# self.serHandle.write(('T'+txCmd+'8'+regSetCommand+regClearCommand+'\r').encode())#t(ID)4(data)\r

					# #time.sleep(0.025)
					# watchdog	= time.perf_counter()
					# while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
					# 	_=1

					# input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					# if not len(input_buffer.decode())	== 13:
					# 	raise errors.CANError(f'CAN EnableClosedLoop received a wrong response from positioner {positionerID:04d}') from None
					# elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
					# 	raise errors.CANError(f'CAN EnableClosedLoop command was not accepted by the positioner with ID {positionerID:04d}') from None
					pass

				elif command	== 'disable_closed_loop':
					# self.serHandle.reset_input_buffer()

					# #cast to hex
					# regSet	= 0x00000000
					# regClear	= 0x00000000 | self._OPT.STREG.CLOSED_LOOP_ALPHA | self._OPT.STREG.CLOSED_LOOP_BETA

					# regSetCommand	= '%0.8X' % (swapInt32(regSet))
					# regClearCommand	= '%0.8X' % (swapInt32(regClear))

					# #Create command
					# txCmd	= (self._OPT.RX.SET_STATUS_LOW<<self._OPT.COM.CAN_CMD_BIT_SHIFT) + ID
					# txCmd	= '%0.8X' % txCmd

					# #send command
					# self.serHandle.write(('T'+txCmd+'8'+regSetCommand+regClearCommand+'\r').encode())#t(ID)4(data)\r

					# #time.sleep(0.025)
					# watchdog	= time.perf_counter()
					# while self.serHandle.inWaiting()<13 and time.perf_counter()-0.1 < watchdog:
					# 	_=1

					# input_buffer=self.serHandle.read(self.serHandle.inWaiting()) #get whole input buffer

					# if not len(input_buffer.decode())	== 13:
					# 	raise errors.CANError(f'CAN EnableClosedLoop received a wrong response from positioner {positionerID:04d}') from None
					# elif not int(input_buffer[10:11],16)	== self._OPT.RX.COMMAND_ACCEPTED:
					# 	raise errors.CANError(f'CAN EnableClosedLoop command was not accepted by the positioner with ID {positionerID:04d}') from None
					pass

				else:
					raise errors.CANError('CAN unknown command') from None
					Output	= []
			else:
				raise errors.CANError('CAN transceiver is disconnected') from None

		except serial.SerialException:
			self.close()
			raise errors.CANError('CAN transceiver is disconnected') from None
		except errors.CANError as e:
			raise e from None

		return Output

def swapInt32(number):
	return (((number << 24) & 0xFF000000) | \
			((number << 8) 	& 0x00FF0000) | \
			((number >> 8) 	& 0x0000FF00) | \
			((number >> 24) & 0x000000FF))

def swapInt64(number):
	return (((number << 56) & 0xFF00000000000000) | \
			((number << 40) & 0x00FF000000000000) | \
			((number << 24) & 0x0000FF0000000000) | \
			((number << 8) 	& 0x000000FF00000000) | \
			((number >> 8) 	& 0x00000000FF000000) | \
			((number >> 24) & 0x0000000000FF0000) | \
			((number >> 40) & 0x000000000000FF00) | \
			((number >> 56) & 0x00000000000000FF))

#TESTING SECTION------------------------------------------------------
def main():
	import numpy as np

##############################################################################################################################
	
	initDatum 			= False
	overwritePosition 	= False				# If true, will set the current motor positions to those specified in initPositions
	initPositions 		= (0	,	0	)	# [°], 		(alpha, beta).	Specifies the current motor positions if initDatum is true, useless otherwise
	targetPositions		= (0	,	0	)	# [°], 		(alpha, beta).	The target positions
	motorSpeed			= (4000	,	4000)	# [RPM], 	(alpha, beta).	The speed of the motors
	motorCurrent		= (90	,	90	)	# [%], 		(alpha, beta).	The current fed to each motor
	canSerial			= 'E351'			# The serial number of the CANUSB device. Leave blank to connect any device. B1:K547 B2:J857 BCollision: E351
	shutdownCurrent 	= False
	
##############################################################################################################################
	
	try:
		Communication_handler = COM_handle()

		print(Communication_handler.get_all_serial_no())

		Communication_handler.init(canSerial) #J857 #K547

		serialNo	= Communication_handler.CAN_write(0,'getserialnumber', [])
		print('Serial No:'+str(serialNo))

		posIDs=Communication_handler.CAN_write(0,'askID', [])
		# posIDs	= [13]
		nbPositioners	= len(posIDs)
		print('Nb positioners:'+str(nbPositioners))
		print()

		for i in range(0,nbPositioners):
			positionner_ID	= posIDs[i]
			print('ID:'+str(positionner_ID))

			R1Steps	= int(round(2**30/360*targetPositions[0],0))
			R2Steps	= int(round(2**30/360*targetPositions[1],0))
			alphaInitPos	= int(round(2**30/360*initPositions[0],0))
			betaInitPos	= int(round(2**30/360*initPositions[1],0))
			motor_rpm_a	= int(motorSpeed[0])
			motor_rpm_b	= int(motorSpeed[1])
			currentAlpha	= int(motorCurrent[0])
			currentBeta	= int(motorCurrent[1])

			if not positionner_ID in posIDs:
				print('Error: specified positioner is not connected')

			if initDatum:
				print('Init datum')
				Communication_handler.CAN_write(positionner_ID,'initdatum', [])

				status	= Communication_handler.CAN_write(positionner_ID,'statusrequest', [])
				while not bool(status[0]&Communication_handler._OPT.STREG.DATUM_INITIALIZED):
					status	= Communication_handler.CAN_write(positionner_ID,'statusrequest', [])

				data = {'Actual_alpha_pos': int(round(2**30/360*(-6.1),0)), 'Actual_beta_pos':int(round(2**30/360*(-6.8),0))}
				Communication_handler.CAN_write(positionner_ID,'set_position', data)
				
				print('Init datum complete')

			status=Communication_handler.CAN_write(positionner_ID,'statusRequest', [])
			print('status:'+str(bin(status[0])))

			data={'R1Steps': R1Steps, 'R2Steps': R2Steps, 'currentAlpha': currentAlpha, 'currentBeta': currentBeta, 'SpeedAlpha': motor_rpm_a, 'SpeedBeta': motor_rpm_b,'Actual_alpha_pos':alphaInitPos, 'Actual_beta_pos':betaInitPos}
			
			print('data:'+str((R1Steps,R2Steps,motor_rpm_a, motor_rpm_b ,alphaInitPos,betaInitPos)))

			if overwritePosition:
				Communication_handler.CAN_write(positionner_ID,'set_position', data)

			Communication_handler.CAN_write(positionner_ID,'set_speed', data)

			Communication_handler.CAN_write(positionner_ID,'setopenloopcurrent', data)

			for i in range(0,1):
				# backForthIncrement = [0	,	20]
				# if int(i)%2:
				# 	data['R1Steps'] -= int(2**30/360*backForthIncrement[0])
				# 	data['R2Steps'] -= int(2**30/360*backForthIncrement[1])
				# else:
				# 	data['R1Steps'] -= int(2**30/360*backForthIncrement[0])
				# 	data['R2Steps'] += int(2**30/360*backForthIncrement[1])

				movementTime=Communication_handler.CAN_write(positionner_ID,'GoToPosition_Speed', data)
				movement_start	= time.perf_counter()
				print('goto_pos:'+str(movementTime))
				movement_time	= max(movementTime)
				movement_safety_delay	= 2;

				status	= Communication_handler.CAN_write(positionner_ID,'statusrequest', data)
				print('status:'+str(bin(status[0])))

				print('movement complete:'+str(bool(status[0]&Communication_handler._OPT.STREG.DISPLACEMENT_COMPLETED)))

				# time.sleep(1)
				# Communication_handler.CAN_write(positionner_ID,'stoptrajectory', [])

				while movement_start+movement_time+movement_safety_delay>time.perf_counter():
					status=Communication_handler.CAN_write(positionner_ID,'statusrequest', data)
					if status[0] & Communication_handler._OPT.STREG.DISPLACEMENT_COMPLETED:
						break
					else:
						print(f'Waiting for movement: {movement_start+movement_time-time.perf_counter():.1f} [s]'+'\033[K', end="\r")
				print(f'Movement complete in {time.perf_counter()-movement_start:.1f} [s]'+'\033[K')
			
			getPos=Communication_handler.CAN_write(positionner_ID,'get_actual_position', data)
			print('get_pos:'+str(getPos))
			print('get_pos[°]:'+str(np.divide(getPos,2**30)*360))

			getPosHall=Communication_handler.CAN_write(positionner_ID,'get_pos_hall', data)
			print('get_hall_pos:'+str(getPosHall))
			print('get_hall_pos[°]:'+str(np.divide(getPosHall,2**30)*360))

			if shutdownCurrent:
				data={'currentAlpha': 0, 'currentBeta': 0}
				Communication_handler.CAN_write(positionner_ID,'setopenloopcurrent', data)
				print('Current shut down')

			print()
	
	except errors.CANError as e:
		print(str(e))
	finally:
		Communication_handler.close()

if __name__	== '__main__':
	main()

