#cython: language_level=3
import smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import numpy as np
import miscmath as mm
import DEFINES

def send_results(recipients = [], calibResults = [], testResults = []):
	if calibResults == [] and testResults == []:
		return False

	if recipients == []:
		return False

	if calibResults is not []:
		nbSlots = len(calibResults)
	else:
		nbSlots = len(testResults)

	for slot in range(0, nbSlots):
		results = []
		if calibResults is not [] and slot < len(calibResults):
			if calibResults[slot].config.nbTestingLoops>1:
				subject = f'Results for positioner {calibResults[slot].positionerID:>04} lifetime iteration {calibResults[slot].config.currentLifetimeIteration+1}/{calibResults[slot].config.nbTestingLoops}'
			else:
				subject = f'Results for positioner {calibResults[slot].positionerID:>04}'

			results.append(f'Tested on {calibResults[slot].testBenchName} slot #{calibResults[slot].slotID:1}')
			results.append( f'Project time: {calibResults[slot].config.currentProjectTime}')
			results.append( f'Positioner ID: {calibResults[slot].positionerID:>04}')
			if calibResults[slot].config.nbTestingLoops>1:
				results.append( f'Lifetime iteration: {calibResults[slot].config.currentLifetimeIteration+1}')
		else:
			if testResults[slot].config.nbTestingLoops>1:
				subject = f'Results for positioner {testResults[slot].positionerID:>04} lifetime iteration {testResults[slot].config.currentLifetimeIteration+1}/{testResults[slot].config.nbTestingLoops}'
			else:
				subject = f'Results for positioner {testResults[slot].positionerID:>04}'

			results.append(f'Tested on {testResults[slot].testBenchName} slot #{testResults[slot].slotID:1}')
			results.append( f'Project time: {testResults[slot].config.currentProjectTime}')
			results.append( f'Positioner ID: {testResults[slot].positionerID:>04}')
			if testResults[slot].config.nbTestingLoops>1:
				results.append( f'Lifetime iteration: {testResults[slot].config.currentLifetimeIteration+1}')

		passed = False
		repeatabilityChecked = False
		hysteresisChecked = False

		if calibResults is not [] and slot < len(calibResults):
			alphaLength = calibResults[slot].mesAlphaLength[-1]
			betaLength = calibResults[slot].mesBetaLength[-1]
			RMSModelFit = calibResults[slot].mesRMSModelFit[-1]
			RMSRepeatability = calibResults[slot].mesRMSRepeatability[-1]
			maxHysteresis = calibResults[slot].mesMaxHysteresis[-1]
			maxNonLinearity = calibResults[slot].mesMaxNL[-1]
			maxNonLinDerivative = calibResults[slot].mesMaxNLDerivative[-1]
			RMSalignmentError = calibResults[slot].mesRMSAlignmentError[-1]
			maxAlignmentError = calibResults[slot].mesMaxAlignmentError[-1]
			roundnessDeviation = calibResults[slot].mesMaxRoundnessError[-1]

			results.append('')
			results.append('-----CALIBRATION-----')
			results.append( f'Alpha length: {round(alphaLength,2):4.2f}\t\t/ {calibResults[slot].requirements.nominalAlphaLength:2.2f} ± {calibResults[slot].requirements.maxAlphaLengthDeviation:1.1f} [mm]')
			results.append( f'Beta length: {round(betaLength,2):4.2f}\t\t/ {calibResults[slot].requirements.nominalBetaLength:2.2f} ± {calibResults[slot].requirements.maxBetaLengthDeviation:1.1f} [mm]')
			results.append( f'RMS model fit: {round(RMSModelFit,2):4.2f}\t\t/ {calibResults[slot].requirements.maxPosError:4.2f} [um]')
			results.append( f'RMS repeatability: {round(RMSRepeatability,2):4.2f}\t\t/ {calibResults[slot].requirements.rmsPosRepeatability:4.2f} [um]')
			results.append( f'Max hysteresis: {round(maxHysteresis,3):4.3f}\t\t/ {calibResults[slot].requirements.maxHysteresis:4.3f} [°]')
			results.append( f'Max non-linearity: {round(maxNonLinearity,3):4.3f}\t/ {calibResults[slot].requirements.maxNonLinearity:4.3f} [°]')
			results.append( f'Max NL derivative: {round(maxNonLinDerivative,3):4.3f}\t/ {calibResults[slot].requirements.maxNonLinearityDerivative:4.3f} [°/°]')
			results.append( f'Max roundness error: {round(roundnessDeviation,2):4.2f}\t/ {calibResults[slot].requirements.maxRoundnessDeviation:4.2f} [um]')

			passed = 	abs(alphaLength-calibResults[slot].requirements.nominalAlphaLength) <= calibResults[slot].requirements.maxAlphaLengthDeviation and \
						abs(betaLength-calibResults[slot].requirements.nominalBetaLength) <= calibResults[slot].requirements.maxBetaLengthDeviation and \
						maxNonLinearity <= calibResults[slot].requirements.maxNonLinearity and\
						maxNonLinDerivative <= calibResults[slot].requirements.maxNonLinearityDerivative and\
						roundnessDeviation <= calibResults[slot].requirements.maxRoundnessDeviation
			if not np.isnan(RMSRepeatability):
				passed = passed and RMSRepeatability <= calibResults[slot].requirements.rmsPosRepeatability
				repeatabilityChecked = True
			if not np.isnan(maxHysteresis):
				passed = passed and maxHysteresis <= calibResults[slot].requirements.maxHysteresis
				hysteresisChecked = True

		if testResults is not [] and slot < len(testResults):
			nbRepetitions, nbTargets, maxNbMoves, nbDims = testResults[slot].targets.shape
			nbPoints = nbTargets*nbRepetitions

			RMSErrorFirstMove 			= testResults[slot].mesRMSError1stMove[-1]
			RMSRepeatabilityFirstMove 	= testResults[slot].mesRMSRepeatability1stMove[-1]
			targetConvergeance 			= testResults[slot].mesTargetConvergeance[-1][-1]
			maxNbMoves 					= testResults[slot].mesMaxNbMoves[-1]

			#Discard the test results for positioner confirmity (maxMoves, positioning error, etc.)

			results.append('')
			results.append('-----TEST-----')
			results.append( f'RMS Error 1st move: {round(RMSErrorFirstMove,2):4.2f} [um]')
			results.append( f'RMS Repeatability 1st move: {round(RMSRepeatabilityFirstMove,2):4.2f} [um]')
			results.append(	f'Target convergeance: {round(targetConvergeance,1):3.1f} [%]')
			results.append(	f'Max moves: {round(maxNbMoves,0):.0f}')

			if not repeatabilityChecked:
				if not np.isnan(RMSRepeatabilityFirstMove):
					passed = passed and RMSRepeatabilityFirstMove <= testResults[slot].requirements.rmsPosRepeatability
				else:
					passed = False


		if passed and repeatabilityChecked and hysteresisChecked:
			subject += ' [PASSED]'
		else:
			subject += ' [FAILED]'

		textMessage = '\n'.join(results)

		# create mail message
		mailMessage = MIMEMultipart()
		mailMessage["From"] = "calibrationTestBench@gmail.com"
	 	# mailMessage["To"] = recipients
		mailMessage["Bcc"] = ", ".join(recipients)
		mailMessage["Subject"] = subject
		mailMessage.attach(MIMEText(textMessage, "plain"))

		attachements = []

		# create the attachements
		for fileName in attachements:
			#Read the binary file
			with open(fileName, "rb") as file:
				part = MIMEBase("application", "octet-stream")
				part.set_payload(file.read())

			# Encode file in ASCII characters to send by email    
			encoders.encode_base64(part)

			# Add header as key/value pair to attachment part
			part.add_header(
				"Content-Disposition",
				f"attachment; filename= {fileName}",
			)

			# Add attachment to message and convert message to string
			mailMessage.attach(part)

		#create the mail server and send the mail
		mailPackage = mailMessage.as_string()
		sslContext = ssl.create_default_context()

		with smtplib.SMTP_SSL("smtp.gmail.com", port = 465, context=sslContext) as mailServer:
			mailServer.login("calibrationtestbench@gmail.com", "1q2w3e4r5t6z7u8i9o0p")
			mailServer.sendmail("calibrationtestbench@gmail.com",recipients,mailPackage)

	return True

def send_mail(recipients = [], subject = '', textMessage = '', htmlMessage = '', attachements = []):
	if recipients == []:
		return False

	# create mail message
	mailMessage = MIMEMultipart()
	mailMessage["From"] = "calibrationTestBench@gmail.com"
 	# mailMessage["To"] = recipients
	mailMessage["Bcc"] = ", ".join(recipients)
	mailMessage["Subject"] = subject
	mailMessage.attach(MIMEText(textMessage, "plain"))
	if htmlMessage is not '':
		mailMessage.attach(MIMEText(htmlMessage, "html"))

	# create the attachements
	for fileName in attachements:
		#Read the binary file
		with open(fileName, "rb") as file:
			part = MIMEBase("application", "octet-stream")
			part.set_payload(file.read())

		# Encode file in ASCII characters to send by email    
		encoders.encode_base64(part)

		# Add header as key/value pair to attachment part
		part.add_header(
			"Content-Disposition",
			f"attachment; filename= {fileName}",
		)

		# Add attachment to message and convert message to string
		mailMessage.attach(part)

	#create the mail server and send the mail
	mailPackage = mailMessage.as_string()
	sslContext = ssl.create_default_context()

	with smtplib.SMTP_SSL("smtp.gmail.com", port = 465, context=sslContext) as mailServer:
		mailServer.login("calibrationtestbench@gmail.com", "1q2w3e4r5t6z7u8i9o0p")
		mailServer.sendmail("calibrationtestbench@gmail.com",recipients,mailPackage)

	return True

def main():
	recipients 		= []
	attachements 	= []

	recipients.append("loic.grossen@epfl.ch")
	# recipients.append("luzius.kronig@epfl.ch")
	# attachements.append("python_garbage\\garbage.png")

	send_mail(	recipients = recipients, 
				subject = "testSubject",
				textMessage = "testBody", 
				attachements = attachements)

	# dummyMail()

if __name__ == "__main__":
	main()