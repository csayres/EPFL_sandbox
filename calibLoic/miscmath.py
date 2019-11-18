#cython: language_level=3
import time
from scipy import optimize,interpolate,stats
import numpy as np
import matplotlib.pyplot as plt
import logger as log
import copy
import DEFINES

MM_IMG_ID_BITSHIFT_FOR_CENTROID_TYPE		= 0
MM_IMG_ID_BITSHIFT_FOR_DIRECTION			= MM_IMG_ID_BITSHIFT_FOR_CENTROID_TYPE	+ DEFINES.MM_IMG_ID_BITS_FOR_CENTROID_TYPE
MM_IMG_ID_BITSHIFT_FOR_AXIS					= MM_IMG_ID_BITSHIFT_FOR_DIRECTION		+ DEFINES.MM_IMG_ID_BITS_FOR_DIRECTION
MM_IMG_ID_BITSHIFT_FOR_STEP					= MM_IMG_ID_BITSHIFT_FOR_AXIS			+ DEFINES.MM_IMG_ID_BITS_FOR_AXIS
MM_IMG_ID_BITSHIFT_FOR_REPETITION			= MM_IMG_ID_BITSHIFT_FOR_STEP			+ DEFINES.MM_IMG_ID_BITS_FOR_STEP
MM_IMG_ID_BITSHIFT_FOR_STARTING_POINT		= MM_IMG_ID_BITSHIFT_FOR_REPETITION		+ DEFINES.MM_IMG_ID_BITS_FOR_REPETITION
MM_IMG_ID_BITSHIFT_FOR_BENCH_SLOT			= MM_IMG_ID_BITSHIFT_FOR_STARTING_POINT	+ DEFINES.MM_IMG_ID_BITS_FOR_STARTING_POINT
MM_IMG_ID_BITMASK_FOR_CENTROID_TYPE			= (2**DEFINES.MM_IMG_ID_BITS_FOR_CENTROID_TYPE - 1) 	<< MM_IMG_ID_BITSHIFT_FOR_CENTROID_TYPE
MM_IMG_ID_BITMASK_FOR_DIRECTION				= (2**DEFINES.MM_IMG_ID_BITS_FOR_DIRECTION - 1) 		<< MM_IMG_ID_BITSHIFT_FOR_DIRECTION
MM_IMG_ID_BITMASK_FOR_AXIS					= (2**DEFINES.MM_IMG_ID_BITS_FOR_AXIS - 1) 				<< MM_IMG_ID_BITSHIFT_FOR_AXIS
MM_IMG_ID_BITMASK_FOR_STEP					= (2**DEFINES.MM_IMG_ID_BITS_FOR_STEP - 1) 				<< MM_IMG_ID_BITSHIFT_FOR_STEP
MM_IMG_ID_BITMASK_FOR_REPETITION			= (2**DEFINES.MM_IMG_ID_BITS_FOR_REPETITION - 1) 		<< MM_IMG_ID_BITSHIFT_FOR_REPETITION
MM_IMG_ID_BITMASK_FOR_STARTING_POINT		= (2**DEFINES.MM_IMG_ID_BITS_FOR_STARTING_POINT - 1) 	<< MM_IMG_ID_BITSHIFT_FOR_STARTING_POINT
MM_IMG_ID_BITMASK_FOR_BENCH_SLOT			= (2**DEFINES.MM_IMG_ID_BITS_FOR_BENCH_SLOT - 1) 		<< MM_IMG_ID_BITSHIFT_FOR_BENCH_SLOT

def deg2rad(angle):
	return angle*np.pi/180

def rad2deg(angle):
	return angle*180/np.pi

def getETA(startingTime):
	t_current = time.time()

	ETA = (t_current-startingTime)

	ETA_h = int(ETA/3600)
	ETA_m = int((ETA%3600)/60)
	ETA_s = round((ETA%60),1)

	return {'h':ETA_h,'m':ETA_m,'s':ETA_s}

def dist(p1,p2):
	return np.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)

def get_circumcenter(p1,p2,p3):
	ax = p1[0]
	ay = p1[1]
	bx = p2[0]
	by = p2[1]
	cx = p3[0]
	cy = p3[1]
	normA = np.sqrt(ax**2+ay**2)
	normB = np.sqrt(bx**2+by**2)
	normC = np.sqrt(cx**2+cy**2)
	xc = 0
	yc = 0
	Sx = 1/2*(normA**2*by+normB**2*cy+normC**2*ay-normA**2*cy-normB**2*ay-normC**2*by)
	Sy = 1/2*(normA**2*cx+normB**2*ax+normC**2*bx-normA**2*bx-normB**2*cx-normC**2*ax)
	normS = np.sqrt(Sx**2+Sy**2)
	a = (ax*by+bx*cy+cx*ay-ax*cy-bx*ay-cx*by)
	b = (ax*by*normC**2+bx*cy*normA**2+cx*ay*normB**2-ax*cy*normB**2-bx*ay*normC**2-cx*by*normA**2)

	xc = Sx/a
	yc = Sy/a

	radius = np.sqrt(b/a+normS**2/a**2)

	return xc, yc, radius

def get_circle_center_approx(xData, yData):
	circleSection = []
	nbData = len(xData)

	estimatePts = [int(0*nbData/3), int(1*nbData/3), int(2*nbData/3)]

	circleSection.append([xData[0:estimatePts[1]]				, yData[0:estimatePts[1]]])
	circleSection.append([xData[estimatePts[1]:estimatePts[2]]	, yData[estimatePts[1]:estimatePts[2]]])
	circleSection.append([xData[estimatePts[2]:-1]	, yData[estimatePts[2]:-1]])

	medianPoints = []
	medianPoints.append([np.nanmedian(circleSection[0][0]), np.nanmedian(circleSection[0][1])])
	medianPoints.append([np.nanmedian(circleSection[1][0]), np.nanmedian(circleSection[1][1])])
	medianPoints.append([np.nanmedian(circleSection[2][0]), np.nanmedian(circleSection[2][1])])

	(xC, yC, r) = get_circumcenter(	(medianPoints[0][0], medianPoints[0][1]),\
									(medianPoints[1][0], medianPoints[1][1]),\
									(medianPoints[2][0], medianPoints[2][1]))

	return (xC, yC)

def fit_circle(xData,yData):
	#rough approximation of the circle's parameters

	xData = xData[~np.isnan(xData)]
	yData = yData[~np.isnan(yData)]

	nbData = len(xData)
	if nbData>2:
		#get rough estimation of circle using 3 well space points to create the circumcircle
		xData = xData.astype(np.float64)
		yData = yData.astype(np.float64)

		estimate_center = get_circle_center_approx(xData, yData)
		estimate_radius = np.nanmedian(dist((estimate_center[0],estimate_center[1]),(xData,yData)))

		params = (estimate_center[0], estimate_center[1], estimate_radius)

		#optimize
		errorfunction = lambda p: distToCircle(*p)(xData,yData)
		params, success = optimize.leastsq(errorfunction, params, ftol = 1e-30)
	elif nbData == 2:
		params = (np.mean(xData),np.mean(yData),np.sqrt((xData[0]-xData[1])**2+(yData[0]-yData[1])**2))
	else:
		params = (xData,yData,0)

	return params

def intersect_circles(center1, r1, center2, r2):
	cX1 = center1[0]
	cY1 = center1[1]
	cX2 = center2[0]
	cY2 = center2[1]
	dist = np.sqrt((cX1-cX2)**2+(cY1-cY2)**2)
	intersect = []

	if dist > r1+r2:
		return intersect

	elif dist < abs(r2-r1):
		return intersect

	else:
		d = (r1**2)-(r2**2)-(cX1**2)+(cX2**2)-(cY1**2)+(cY2**2)
		e = 2*(cX1-cX2)
		f = 2*(cY1-cY2)

		if e is not 0 and abs(e)>abs(f): #Equation solvable in x and with the best discriminant factor
			a = (f**2)/(e**2)+1
			b = (2*d*f)/(e**2)+(2*cX1*f)/(e)-(2*cY1)
			c = -((r1**2)-(d**2)/(e**2)-(cX1**2)-(cY1**2)-(2*cX1*d)/(e))

			delta = (b**2)-(4*a*c)
			if delta < 0:
				return intersect

			elif delta==0:
				x = -b/(2*a)
				y = (d+f*x)/(-e)
				intersect.append([x,y])
				return intersect

			else:
				y1 = (-b+np.sqrt(delta))/(2*a)
				y2 = (-b-np.sqrt(delta))/(2*a)
				x1 = (d+f*y1)/(-e)
				x2 = (d+f*y2)/(-e)
				intersect.append([x1,y1])
				intersect.append([x2,y2])
				return intersect

		elif f is not 0: #Equation solvable in y
			a = (e**2)/(f**2)+1
			b = (2*d*e)/(f**2)+(2*cY1*e)/(f)-(2*cX1)
			c = -((r1**2)-(d**2)/(f**2)-(cY1**2)-(cX1**2)-(2*cY1*d)/(f))
			delta = (b**2)-(4*a*c)
			if delta < 0:
				return intersect

			elif delta==0:
				y = -b/(2*a)
				x = (d+e*y)/(-f)
				intersect.append([x,y])
				return intersect

			else:
				x1 = (-b+np.sqrt(delta))/(2*a)
				x2 = (-b-np.sqrt(delta))/(2*a)
				y1 = (d+e*x1)/(-f)
				y2 = (d+e*x2)/(-f)
				intersect.append([x1,y1])
				intersect.append([x2,y2])
				return intersect

		else: #Equation not solvable
			return intersect

def get_model_angles_from_endpoint(center, endpoint, lAlpha, lBeta):
	c1 = (center[1], center[0])
	c2 = [endpoint[1], endpoint[0]]
	r1 = lAlpha
	r2 = lBeta
	intersect = intersect_circles(c1,r1,c2,r2)

	angles = []
	for midpoint in intersect:
		alpha = np.arctan2(midpoint[1]-c1[1], midpoint[0]-c1[0])
		gamma = np.arctan2(c2[1]-midpoint[1], c2[0]-midpoint[0])
		beta = gamma-alpha

		angles.append([np.mod(alpha, 2*np.pi),np.mod(beta, 2*np.pi)])

	return angles

def get_closest(guessesList, targetList):
	dist = []
	# print((guessesList, targetList))
	for guess in guessesList:
		sumDist = 0
		for i in range(0, len(targetList)):
			sumDist += (targetList[i]-guess[i])**2
		dist.append(np.sqrt(sumDist/len(targetList)))
	bestGuess = guessesList[np.argmin(dist)]

	return bestGuess

def get_closest_angle(guessesList, targetList):
	for i in range(0, len(guessesList)):
		for j in range(0, len(targetList)):
			while targetList[j]-guessesList[i][j]<-np.pi:
				guessesList[i][j] -= 2*np.pi
			while targetList[j]-guessesList[i][j]>np.pi:
				guessesList[i][j] += 2*np.pi

	return get_closest(guessesList, targetList)

def isInCircle(coordinate,center,r):
	return bool(dist(coordinate, center) <= r)

def create_circular_mask(height, width, center, radius):
	Y, X = np.ogrid[:height, :width]
	square_dist_from_center = (X - center[0])**2 + (Y-center[1])**2

	mask = square_dist_from_center <= radius**2
	return mask

def computeValidSoftROI(image, camMaxX, camMaxY, validityCenter, validityRadius):
	if validityRadius == DEFINES.PC_IMAGE_GET_ALL_ROI:
		return image, 0, 0
	else:
		x_min = int(validityCenter[0]-validityRadius)
		x_max = int(validityCenter[0]+validityRadius)
		y_min = int(validityCenter[1]-validityRadius)
		y_max = int(validityCenter[1]+validityRadius)

		#crop ROI while it is not in the image, up to the minimal window allowed
		if x_min < 0:
			x_min = 0
		if x_max-x_min < 1:
			x_max = x_min+1
		if x_max > camMaxX:
			x_max = camMaxX
		if x_max-x_min < 1:
			x_min = x_max-1
		if y_min < 0:
			y_min = 0
		if y_max-y_min < 1:
			y_max = y_min+1
		if y_max > camMaxY:
			y_max = camMaxY
		if y_max-y_min < 1:
			y_min = y_max-1

		image = image[	y_min:y_max,\
						x_min:x_max]

		validityCenter = (validityCenter[0]-x_min, validityCenter[1]-y_min) #Shift the circle center in the new image shape

		circularMask = create_circular_mask(image.shape[0], image.shape[1], validityCenter, validityRadius)
		image[~circularMask] = 0

		return image, x_min, y_min

def cropImage(image, ROI, camMaxX, camMaxY):
	x_min = int(ROI[0]-ROI[2]/2)
	x_max = int(ROI[0]+ROI[2]/2)
	y_min = int(ROI[1]-ROI[3]/2)
	y_max = int(ROI[1]+ROI[3]/2)

	#crop ROI
	if x_min < 0:
		x_min = 0
	if x_max-x_min < 1:
		x_max = x_min+1
	if x_max > camMaxX:
		x_max = camMaxX
	if x_max-x_min < 1:
		x_min = x_max-1
	if y_min < 0:
		y_min = 0
	if y_max-y_min < 1:
		y_max = y_min+1
	if y_max > camMaxY:
		y_max = camMaxY
	if y_max-y_min < 1:
		y_min = y_max-1

	image = copy.deepcopy(image[	y_min:y_max,\
									x_min:x_max])

	return image,x_min,y_min

def nanrms(data):
	data = np.ravel(data)
	if len(data)>0:
		if np.count_nonzero(~np.isnan(data))>0:
			return np.sqrt(np.nanmean(data**2))
		else:
			return np.nan
	else:
		return 0

def rms(data):
	data = np.ravel(data)
	if len(data)>0:
		return np.sqrt(np.mean(data**2))
	else:
		return 0

def rms_err(data):
	data = np.ravel(data)
	meanData = np.nanmean(data)
	if len(data)>0:
		return np.sqrt(np.nanmean((data-meanData)**2))
	else:
		return 0

def get_endpoint(centerX,centerY,lAlpha,lBeta,alphaAngle,betaAngle):
	alphaAngle -= np.pi/2
	targetX = 	(np.cos(alphaAngle)*lAlpha+\
				np.cos(alphaAngle+betaAngle)*lBeta+\
				centerX)

	targetY = 	(-np.sin(alphaAngle)*lAlpha-\
				np.sin(alphaAngle+betaAngle)*lBeta+\
				centerY)

	return targetX, targetY

def model_error(optParams,alphaCommand,betaCommand,alphaIterpolator,betaIterpolator,xData,yData,getFullOutput = False):
	(centerX,centerY,lAlpha,lBeta,offsetAlpha,offsetBeta) = optParams
	# print((centerX,centerY,lAlpha,lBeta,offsetAlpha,offsetBeta))

	#iterate to get all the errors
	valuesToRemove = np.isnan(xData)
	(nbRepetitions,nbStartingPoints,nbAxes,nbSteps) = xData.shape
	totalNbPoints = nbRepetitions*nbStartingPoints*nbAxes*nbSteps
	resErrors = np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps),np.nan)
	errorX = np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps),np.nan)
	errorY = np.full((nbRepetitions,nbStartingPoints,nbAxes,nbSteps),np.nan)

	for repetition in range(0,nbRepetitions):
		for startingPoint in range(0,nbStartingPoints):
			for axis in range(0,nbAxes):
				for step in range(0,nbSteps):
					if not valuesToRemove[repetition,startingPoint,axis,step]:
						#get model angle
						alphaAngle = alphaIterpolator(alphaCommand[startingPoint,axis,step])+offsetAlpha
						betaAngle = betaIterpolator(betaCommand[startingPoint,axis,step])+offsetBeta

						(targetX,targetY) = get_endpoint(centerX,centerY,lAlpha,lBeta,alphaAngle,betaAngle)
						
						errorX[repetition,startingPoint,axis,step] = targetX-xData[repetition,startingPoint,axis,step]
						errorY[repetition,startingPoint,axis,step] = targetY-yData[repetition,startingPoint,axis,step]

						resErrors[repetition,startingPoint,axis,step] = np.sqrt(errorX[repetition,startingPoint,axis,step]**2+errorY[repetition,startingPoint,axis,step]**2)

	if getFullOutput:
		return resErrors,errorX,errorY
	else:
		resErrors = resErrors[~np.isnan(resErrors)]
		return np.ravel(resErrors)

def mean_model_error(optParams,alphaCommand,betaCommand,alphaIterpolator,betaIterpolator,xData,yData):
	allErrors = model_error(optParams,alphaCommand,betaCommand,alphaIterpolator,betaIterpolator,xData,yData,False)
	return np.nanmean(allErrors)*1000

def rms_model_error(optParams,alphaCommand,betaCommand,alphaIterpolator,betaIterpolator,xData,yData):
	allErrors = model_error(optParams,alphaCommand,betaCommand,alphaIterpolator,betaIterpolator,xData,yData,False)
	return nanrms(allErrors)*1000

def optimize_model(centerX,centerY,lAlpha,lBeta,offsetAlpha,offsetBeta,alphaCommand,betaCommand,alphaMeasures,betaMeasures,xData,yData):

	offsetAlpha=np.mod(offsetAlpha+np.pi,2*np.pi)-np.pi
	offsetBeta=np.mod(offsetBeta+np.pi,2*np.pi)-np.pi

	params = (centerX,centerY,lAlpha,lBeta,offsetAlpha,offsetBeta)
	# print(params)
	
	nbSteps = (alphaMeasures.shape)[2]
	meanAlphaMeasures = np.full((nbSteps),np.nan)
	meanBetaMeasures = np.full((nbSteps),np.nan)
	meanAlphaCommand = np.full((nbSteps),np.nan)
	meanBetaCommand = np.full((nbSteps),np.nan)

	for step in range(0,nbSteps):
		meanAlphaMeasures[step] = np.nanmean(np.ravel(alphaMeasures[:,:,step]))
		meanBetaMeasures[step] = np.nanmean(np.ravel(betaMeasures[:,:,step]))
		meanAlphaCommand[step] = np.nanmean(np.ravel(alphaCommand[0,DEFINES.PARAM_AXIS_ALPHA,step]))
		meanBetaCommand[step] = np.nanmean(np.ravel(betaCommand[0,DEFINES.PARAM_AXIS_BETA,step]))
	
	meanAlphaCommand = meanAlphaCommand[~np.isnan(meanAlphaMeasures)]
	meanBetaCommand = meanBetaCommand[~np.isnan(meanBetaMeasures)]
	meanAlphaMeasures = meanAlphaMeasures[~np.isnan(meanAlphaMeasures)]
	meanBetaMeasures = meanBetaMeasures[~np.isnan(meanBetaMeasures)]

	# print((meanAlphaMeasures,meanAlphaCommand))
	# print((meanBetaMeasures,meanBetaCommand))

	#construct the alpha and beta approximators
	alphaIterpolator = interpolate.interp1d(meanAlphaCommand, meanAlphaMeasures, kind='linear', fill_value='extrapolate')
	betaIterpolator = interpolate.interp1d(meanBetaCommand, meanBetaMeasures, kind='linear', fill_value='extrapolate')

	modelFit = rms_model_error(params,alphaCommand,betaCommand,alphaIterpolator,betaIterpolator,xData,yData)
	
	if len(~np.isnan(np.ravel(xData))) >= len(params):
		degenerated_error = lambda params: np.sqrt(model_error(params,alphaCommand,betaCommand,alphaIterpolator,betaIterpolator,xData,yData,False))
		params, success = optimize.leastsq(degenerated_error, params, ftol = DEFINES.MM_MODEL_FIT_OPT_TOLERANCE, maxfev = DEFINES.MM_MODEL_FIT_OPT_MAX_F_EV)
	else:
		log.message(DEFINES.LOG_MESSAGE_PRIORITY_WARNING,1,f'Optimization skipped. Not enough data available.')

	params = np.asarray(params)
	params[4] = np.mod(params[4]+np.pi,2*np.pi)-np.pi
	params[5] = np.mod(params[5]+np.pi,2*np.pi)-np.pi #adapt offsets between -pi and pi

	modelFit = rms_model_error(params,alphaCommand,betaCommand,alphaIterpolator,betaIterpolator,xData,yData)
	
	return params

def threshold(data, min_val, max_val):
	data[data>max_val] = max_val
	data[data<min_val] = min_val
	return data

def threshold1D(data, min_val, max_val):
	if data>max_val:
		data=max_val
	elif data<min_val:
		data=min_val
	return data

def circle(centerX, centerY, radius):
	return lambda alpha: (	centerX + np.cos(np.deg2rad(alpha))*radius,\
							centerY - np.sin(np.deg2rad(alpha))*radius)

def distToCircle(centerX, centerY, radius):
	return lambda x,y: np.sqrt((centerX-x)**2+(centerY-y)**2)-radius

def gaussian(height, center_x, center_y, width_x, width_y, n):
	"""Returns a gaussian function with the given parameters"""
	width_x = float(width_x)
	width_y = float(width_y)

	return lambda x,y: height*np.exp(
				-((((center_x-x)/width_x)**2+(abs(center_y-y)/width_y)**2)/2)**n)

def moments(data,Xin,Yin):
	"""Returns (height, x, y, width_x, width_y)
	the gaussian parameters of a 2D distribution by calculating its
	moments """
	total = np.sum(data)
	X, Y = [Xin,Yin]
	x = np.sum((X*data)/total)
	y = np.sum((Y*data)/total)
	col = data[:, int(y)]
	width_x = np.sqrt(np.abs((np.arange(col.size)-y)**2*col).sum()/col.sum())
	row = data[int(x), :]
	width_y = np.sqrt(np.abs((np.arange(row.size)-x)**2*row).sum()/row.sum())
	height = data.max()
	n = 1
	return height, x, y, width_x, width_y, n

def fitgaussian(data,Xin,Yin,data_min,data_max,optimizerTolerance):
	"""Returns (height, x, y, width_x, width_y)
	the gaussian parameters of a 2D distribution found by a fit"""
	# print(Xin)
	# print(Yin)
	# print(data)
	Xin = Xin.astype(np.float64)
	Yin = Yin.astype(np.float64)
	data = data.astype(np.float64)
	dataShapeX, dataShapeY= data.shape
	estimate = moments(data,Xin,Yin)
	errorfunction = lambda p: np.ravel(threshold(gaussian(*p)(Xin,Yin),data_min,data_max) - data)
	
	if dataShapeX*dataShapeY >= len(estimate):
		estimate, success = optimize.leastsq(errorfunction, estimate, ftol = optimizerTolerance)

	estimate = np.asarray(estimate)

	return estimate

def get_img_ID(image_ID):
	centroidType = 		(image_ID & MM_IMG_ID_BITMASK_FOR_CENTROID_TYPE)	>> MM_IMG_ID_BITSHIFT_FOR_CENTROID_TYPE
	direction = 		(image_ID & MM_IMG_ID_BITMASK_FOR_DIRECTION)		>> MM_IMG_ID_BITSHIFT_FOR_DIRECTION
	axis = 				(image_ID & MM_IMG_ID_BITMASK_FOR_AXIS)				>> MM_IMG_ID_BITSHIFT_FOR_AXIS
	step = 				(image_ID & MM_IMG_ID_BITMASK_FOR_STEP)				>> MM_IMG_ID_BITSHIFT_FOR_STEP
	repetition = 		(image_ID & MM_IMG_ID_BITMASK_FOR_REPETITION)		>> MM_IMG_ID_BITSHIFT_FOR_REPETITION
	startingPoint = 	(image_ID & MM_IMG_ID_BITMASK_FOR_STARTING_POINT)	>> MM_IMG_ID_BITSHIFT_FOR_STARTING_POINT
	benchSlot = 		(image_ID & MM_IMG_ID_BITMASK_FOR_BENCH_SLOT)		>> MM_IMG_ID_BITSHIFT_FOR_BENCH_SLOT

	return benchSlot, repetition, startingPoint, axis, step, direction, centroidType

def generate_img_ID(benchSlot, repetition, startingPoint, axis, step, direction, centroidType):
	return 	np.int64(	(centroidType 	<< MM_IMG_ID_BITSHIFT_FOR_CENTROID_TYPE) +\
						(direction		<< MM_IMG_ID_BITSHIFT_FOR_DIRECTION) + \
						(axis			<< MM_IMG_ID_BITSHIFT_FOR_AXIS) + \
						(step			<< MM_IMG_ID_BITSHIFT_FOR_STEP) + \
						(repetition		<< MM_IMG_ID_BITSHIFT_FOR_REPETITION) + \
						(startingPoint 	<< MM_IMG_ID_BITSHIFT_FOR_STARTING_POINT) + \
						(benchSlot 		<< MM_IMG_ID_BITSHIFT_FOR_BENCH_SLOT))
						
def get_ETA(tStart, completion):
	tNow = time.time()
	tRemaining = (tNow-tStart)/completion-(tNow-tStart)
	(days, hours, minutes, seconds) = decompose_time(tRemaining)

	return tRemaining, days, hours, minutes, seconds

def decompose_time(time):
	days, restSeconds = divmod(time,24*60*60)
	hours, restSeconds = divmod(restSeconds,60*60)
	minutes, seconds = divmod(restSeconds,60)

	return int(days), int(hours), int(minutes), seconds

def main():
	circle1 = (32.95,42.87,7.45)
	xData = circle(circle1[0],circle1[1],circle1[2])(np.linspace(0,10,15, endpoint=False))[0]
	yData = circle(circle1[0],circle1[1],circle1[2])(np.linspace(0,10,15, endpoint=False))[1]
	xData = list(xData)
	yData = list(yData)

	xData.append(15)
	yData.append(25)
	valuesToDrop = [False for i in range(0,len(xData))]

	center = get_circle_center_approx(xData, yData)

	plt.scatter(center[0], center[1], color = 'red')
	plt.draw()
	plt.pause(1e-17)
	print(center)
	dist = [np.sqrt((center[0]-xData[i])**2 + (center[0]-yData[i])**2) for i in range(0,len(xData))]
	zn = np.abs(stats.zscore(dist))

	# a = generate_img_ID(1,25,34,1,43523,1,0)
	# print(get_img_ID(a))
	# print(get_circumcenter((0,2),(2,0),(0,0)))
	# circle1 = (32.95,42.87,7.45)
	# print(fit_circle((circle(circle1[0],circle1[1],circle1[2])(np.linspace(0,2,3, endpoint=False)))[0],(circle(circle1[0],circle1[1],circle1[2])(np.linspace(0,2,3, endpoint=False)))[1]))

	# print(get_ETA(time.time()-86345.22,0.5))
	# print(get_endpoint(25,40,10,10,np.pi/2,np.pi/2)) #x, y, l1, l2, a, b

if __name__ == '__main__':
	main()