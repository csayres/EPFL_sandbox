#cython: language_level=3
import logger as log
import numpy as np
import miscmath as mm
import copy
from skimage.measure import label, regionprops
from skimage.filters import gaussian as gaussian_filter
import matplotlib.pyplot as plt
import DEFINES

#Get the exact location of the centroid
def compute_centroid_old(image, cameraProps, result_ID):
	col_corr = cameraProps.yCorr
	row_corr = cameraProps.xCorr
	# col_corr = cameraProps.xCorr
	# row_corr = cameraProps.yCorr
	# col_corr = np.multiply(cameraProps.xCorr,0)
	# row_corr = np.multiply(cameraProps.yCorr,0)
	col_offset = cameraProps.ROIoffsetX
	row_offset = cameraProps.ROIoffsetY
	scale_factor = cameraProps.scaleFactor
	test_bench = cameraProps.cameraType
	image_shape = image.shape
	col_corr = col_corr[(row_offset):(row_offset+image_shape[DEFINES.CC_ROW_COORDINATE]),\
						(col_offset):(col_offset+image_shape[DEFINES.CC_COL_COORDINATE])]
	row_corr = row_corr[(row_offset):(row_offset+image_shape[DEFINES.CC_ROW_COORDINATE]),\
						(col_offset):(col_offset+image_shape[DEFINES.CC_COL_COORDINATE])]				
	image = np.divide(image, DEFINES.PC_CAMERA_MAX_INTENSITY_RAW).astype(np.float_)
	image = np.nan_to_num(image)

	# Filter the 2D image
	image = gaussian_filter(image,DEFINES.CC_IMAGE_XY_FILTERING_SIGMA)

	#Check if the image is sufficiently bright
	if np.max(image) < DEFINES.CC_CENTROID_DETECTION_THRESHOLD:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

	#Check if the image is sufficiently big
	if test_bench == DEFINES.PC_CAMERA_TYPE_XY:
		if image_shape[0] < DEFINES.CC_CENTROID_XY_MAX_DIAMETER*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY or image_shape[1] < DEFINES.CC_CENTROID_XY_MAX_DIAMETER*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY:
			return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]
	elif test_bench == DEFINES.PC_CAMERA_TYPE_TILT:
		if image_shape[0] < DEFINES.CC_CENTROID_TILT_MAX_DIAMETER*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT or image_shape[1] < DEFINES.CC_CENTROID_TILT_MAX_DIAMETER*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT:
			return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]
	else:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]
	#Get connected points of the image
	if test_bench == DEFINES.PC_CAMERA_TYPE_XY:
		label_img = label(image > DEFINES.CC_CENTROID_DETECTION_THRESHOLD_XY_RATIO*np.max(image))
	elif test_bench == DEFINES.PC_CAMERA_TYPE_TILT:
		label_img = label(image > DEFINES.CC_CENTROID_DETECTION_THRESHOLD_TILT_RATIO*np.max(image))
	else:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

	props = regionprops(label_img, intensity_image=image, coordinates='rc')

	if len(props) < 1:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

	#search the first big dot in the properties. This avoids most reflectance artifacts.
	for i in range(0,len(props)+1):
		if i >= len(props):
			# for i in range(0,len(props)):
			# 	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO, 1, f'Diameter {props[i].equivalent_diameter:.2f}')
			return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

		diameter  = props[i].equivalent_diameter
		intensity = props[i].max_intensity
		if 	((diameter > DEFINES.CC_CENTROID_XY_MIN_DIAMETER and diameter < DEFINES.CC_CENTROID_XY_MAX_DIAMETER and test_bench == DEFINES.PC_CAMERA_TYPE_XY) or \
			(diameter > DEFINES.CC_CENTROID_TILT_MIN_DIAMETER and diameter < DEFINES.CC_CENTROID_TILT_MAX_DIAMETER and test_bench == DEFINES.PC_CAMERA_TYPE_TILT)) and \
			intensity >= DEFINES.CC_CENTROID_DETECTION_THRESHOLD: #filter diameter
			centroids = props[i].centroid
			if len(centroids) >= 2:
				if centroids[DEFINES.CC_ROW_COORDINATE] >= 0 and centroids[DEFINES.CC_ROW_COORDINATE] <= (image.shape)[DEFINES.CC_ROW_COORDINATE] \
				and centroids[DEFINES.CC_COL_COORDINATE] >= 0 and centroids[DEFINES.CC_COL_COORDINATE] <= (image.shape)[DEFINES.CC_COL_COORDINATE]:
					break

	#crop the image
	if test_bench == DEFINES.PC_CAMERA_TYPE_XY:
		crop_size_row_min = -int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_ROW_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY)
		crop_size_row_max = int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_ROW_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY)
		crop_size_col_min = -int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_COL_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY)
		crop_size_col_max = int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_COL_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY)
	elif test_bench == DEFINES.PC_CAMERA_TYPE_TILT:
		crop_size_row_min = -int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_ROW_RATIO_TILT*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT)
		crop_size_row_max = int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_ROW_RATIO_TILT*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT)
		crop_size_col_min = -int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_COL_RATIO_TILT*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT)
		crop_size_col_max = int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_COL_RATIO_TILT*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT)
	else:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]
	
	row_centroid = int(centroids[DEFINES.CC_ROW_COORDINATE])
	col_centroid = int(centroids[DEFINES.CC_COL_COORDINATE])

	#Check that the crop remains in the image
	if row_centroid+crop_size_row_min<0:
		crop_size_row_min = -row_centroid
	if row_centroid+crop_size_row_max>image_shape[DEFINES.CC_ROW_COORDINATE]:
		crop_size_row_max = image_shape[DEFINES.CC_ROW_COORDINATE]-row_centroid
	if col_centroid+crop_size_col_min<0:
		crop_size_col_min = -col_centroid
	if col_centroid+crop_size_col_max>image_shape[DEFINES.CC_COL_COORDINATE]:
		crop_size_col_max = image_shape[DEFINES.CC_COL_COORDINATE]-col_centroid

	image_small = image[	(row_centroid+crop_size_row_min):(row_centroid+crop_size_row_max),\
							(col_centroid+crop_size_col_min):(col_centroid+crop_size_col_max)]

	col_corr_small = col_corr[	(row_centroid+crop_size_row_min):(row_centroid+crop_size_row_max),\
								(col_centroid+crop_size_col_min):(col_centroid+crop_size_col_max)]
	row_corr_small = row_corr[	(row_centroid+crop_size_row_min):(row_centroid+crop_size_row_max),\
								(col_centroid+crop_size_col_min):(col_centroid+crop_size_col_max)]

	#Apply the correction on the cropped image. Arrays are [ROW,COL] instead of [x,y]
	rowIn = np.array([np.mgrid[0:crop_size_row_max-crop_size_row_min],]*(crop_size_col_max-crop_size_col_min)).transpose()
	colIn = np.array([np.mgrid[0:crop_size_col_max-crop_size_col_min],]*(crop_size_row_max-crop_size_row_min))
	
	rowIn = np.add(rowIn, row_corr_small)
	colIn = np.add(colIn, col_corr_small)
	
	data_min = DEFINES.CC_IMAGE_THRESHOLD_MIN
	data_max = DEFINES.CC_IMAGE_THRESHOLD_MAX_RATIO*np.max(image_small)

	mm.threshold(image_small,data_min,data_max)

	#Fit the 2D gaussian in several iterations
	#initialize the iteration variables
	current_image = image_small.copy()
	current_colIn = colIn.copy()
	current_rowIn = rowIn.copy()

	i = 0
	crop_row_min = crop_col_min = 0
	(crop_row_max, crop_col_max) = (current_image.shape[DEFINES.CC_ROW_COORDINATE]-1,current_image.shape[DEFINES.CC_COL_COORDINATE]-1)
	center_is_moving = True

	min_col = []
	min_row = []
	max_col = []
	max_row = []

	min_col.append(crop_col_min)
	min_row.append(crop_row_min)
	max_col.append(crop_col_max)
	max_row.append(crop_row_max)

	#begin the iterations. 
	#a) get center
	#b) calculate crop
	#c) check if crop didn't happen in the past
	#d) crop or exit
	#e) iterate while exit condition or max iterations are not reached
	while i<DEFINES.CC_COMPUTATION_MAX_ITERATION and center_is_moving:

		#Fit a 2D mm.gaussian
		if cameraProps.cameraType == DEFINES.PC_CAMERA_TYPE_XY:
			params = mm.fitgaussian(current_image,current_colIn,current_rowIn,data_min,data_max, DEFINES.CC_OPTIMIZER_TOLERANCE_XY)
		else:
			params = mm.fitgaussian(current_image,current_colIn,current_rowIn,data_min,data_max, DEFINES.CC_OPTIMIZER_TOLERANCE_TILT)
		(height, center_col, center_row, width_col, width_row, n) = params

		# plt.figure()
		# plt.pcolormesh(current_colIn, current_rowIn, current_image, cmap=plt.cm.viridis)
		# plt.scatter(center_col,center_row,marker ='x',c='red')
		# plt.draw()
		# plt.pause(1e-17)
		# plt.show()

		width_col = abs(width_col)
		width_row = abs(width_row)

		undistorted_center_row = min_row[-1]+center_row-rowIn[int(round(min_row[-1]+center_row)),int(round(min_col[-1]+center_col))]+int(round(min_row[-1]+center_row))
		undistorted_center_col = min_col[-1]+center_col-colIn[int(round(min_row[-1]+center_row)),int(round(min_col[-1]+center_col))]+int(round(min_col[-1]+center_col))

		#if center is out of the image, break
		if undistorted_center_col < crop_col_min or undistorted_center_col > crop_col_max or undistorted_center_row < crop_row_min or undistorted_center_row > crop_row_max:
			break

		#On the line passing by the center, get the crop limits
		if test_bench == DEFINES.PC_CAMERA_TYPE_XY:
			col_margin = width_col*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY
			row_margin = width_row*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY
		elif test_bench == DEFINES.PC_CAMERA_TYPE_TILT:
			col_margin = width_col*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT
			row_margin = width_row*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT
		else:
			return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

		min_col.append(int(round(max(crop_col_min, undistorted_center_col-col_margin))))
		max_col.append(int(round(min(crop_col_max, undistorted_center_col+col_margin))))
		min_row.append(int(round(max(crop_row_min, undistorted_center_row-row_margin))))
		max_row.append(int(round(min(crop_row_max, undistorted_center_row+row_margin))))

		#check if the crop didn't happen in the past. if yes, exit
		for j in range(0,len(min_col)-1):
			if 	abs(min_col[j]-min_col[-1])<DEFINES.CC_COMPUTATION_PIXEL_TOLERANCE_XY and \
				abs(max_col[j]-max_col[-1])<DEFINES.CC_COMPUTATION_PIXEL_TOLERANCE_XY and \
				abs(min_row[j]-min_row[-1])<DEFINES.CC_COMPUTATION_PIXEL_TOLERANCE_XY and \
				abs(max_row[j]-max_row[-1])<DEFINES.CC_COMPUTATION_PIXEL_TOLERANCE_XY:
				center_is_moving = False
				break

		if center_is_moving:
			#crop the image for the next iteration
			current_image = image_small[min_col[-1]:max_col[-1],min_row[-1]:max_row[-1]]
			current_colIn = np.subtract(colIn[min_col[-1]:max_col[-1],min_row[-1]:max_row[-1]],min_col[-1])
			current_rowIn = np.subtract(rowIn[min_col[-1]:max_col[-1],min_row[-1]:max_row[-1]],min_row[-1])

		i += 1

	#rescale the result
	center_col = center_col+crop_size_col_min+min_col[-2]
	center_row = center_row+crop_size_row_min+min_row[-2]

	col_out = col_centroid+center_col+col_offset # Add centroid offset and Region of Interest offset
	row_out = row_centroid+center_row+row_offset
	
	return (col_out*scale_factor,row_out*scale_factor,col_out,row_out,width_col,width_row,height,result_ID)


#Get the exact location of the centroid
def compute_centroid(image, cameraProps, result_ID):
	col_corr = copy.deepcopy(cameraProps.yCorr)
	row_corr = copy.deepcopy(cameraProps.xCorr)
	# col_corr = cameraProps.xCorr
	# row_corr = cameraProps.yCorr
	# col_corr = np.multiply(cameraProps.xCorr,0)
	# row_corr = np.multiply(cameraProps.yCorr,0)
	col_offset = cameraProps.ROIoffsetX
	row_offset = cameraProps.ROIoffsetY
	scale_factor = cameraProps.scaleFactor
	test_bench = cameraProps.cameraType
	image_shape = image.shape
	col_corr = col_corr[(row_offset):(row_offset+image_shape[DEFINES.CC_ROW_COORDINATE]),\
						(col_offset):(col_offset+image_shape[DEFINES.CC_COL_COORDINATE])]
	row_corr = row_corr[(row_offset):(row_offset+image_shape[DEFINES.CC_ROW_COORDINATE]),\
						(col_offset):(col_offset+image_shape[DEFINES.CC_COL_COORDINATE])]				
	image = np.divide(image, DEFINES.PC_CAMERA_MAX_INTENSITY_RAW).astype(np.float_)
	image = np.nan_to_num(image)

	# Filter the 2D image
	image = gaussian_filter(image,DEFINES.CC_IMAGE_XY_FILTERING_SIGMA)

	#Check if the image is sufficiently bright
	if np.max(image) < DEFINES.CC_CENTROID_DETECTION_THRESHOLD:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

	#Check if the image is sufficiently big
	if test_bench == DEFINES.PC_CAMERA_TYPE_XY:
		if image_shape[0] < DEFINES.CC_CENTROID_XY_MAX_DIAMETER*DEFINES.CC_SMALL_IMAGE_CROP_ROW_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY or image_shape[1] < DEFINES.CC_CENTROID_XY_MAX_DIAMETER*DEFINES.CC_SMALL_IMAGE_CROP_COL_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY:
			return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]
	elif test_bench == DEFINES.PC_CAMERA_TYPE_TILT:
		if image_shape[0] < DEFINES.CC_CENTROID_TILT_MAX_DIAMETER*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT or image_shape[1] < DEFINES.CC_CENTROID_TILT_MAX_DIAMETER*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT:
			return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]
	else:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

	#Get connected points of the image
	if test_bench == DEFINES.PC_CAMERA_TYPE_XY:
		label_img = label(image > DEFINES.CC_CENTROID_DETECTION_THRESHOLD_XY_RATIO*np.max(image))
	elif test_bench == DEFINES.PC_CAMERA_TYPE_TILT:
		label_img = label(image > DEFINES.CC_CENTROID_DETECTION_THRESHOLD_TILT_RATIO*np.max(image))
	else:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

	props = regionprops(label_img, intensity_image=image, coordinates='rc')

	if len(props) < 1:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

	#search the first big dot in the properties. This avoids most reflectance artifacts.
	for i in range(0,len(props)+1):
		if i >= len(props):
			# for i in range(0,len(props)):
			# 	log.message(DEFINES.LOG_MESSAGE_PRIORITY_DEBUG_INFO, 1, f'Diameter {props[i].equivalent_diameter:.2f}')
			return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

		diameter  = props[i].equivalent_diameter
		intensity = props[i].max_intensity
		if 	((diameter > DEFINES.CC_CENTROID_XY_MIN_DIAMETER and diameter < DEFINES.CC_CENTROID_XY_MAX_DIAMETER and test_bench == DEFINES.PC_CAMERA_TYPE_XY) or \
			(diameter > DEFINES.CC_CENTROID_TILT_MIN_DIAMETER and diameter < DEFINES.CC_CENTROID_TILT_MAX_DIAMETER and test_bench == DEFINES.PC_CAMERA_TYPE_TILT)) and \
			intensity >= DEFINES.CC_CENTROID_DETECTION_THRESHOLD or True: #filter diameter
			centroids = props[i].centroid
			if len(centroids) >= 2:
				if centroids[DEFINES.CC_ROW_COORDINATE] >= 0 and centroids[DEFINES.CC_ROW_COORDINATE] <= (image.shape)[DEFINES.CC_ROW_COORDINATE] \
				and centroids[DEFINES.CC_COL_COORDINATE] >= 0 and centroids[DEFINES.CC_COL_COORDINATE] <= (image.shape)[DEFINES.CC_COL_COORDINATE]:
					break
	#crop the image
	if test_bench == DEFINES.PC_CAMERA_TYPE_XY:
		crop_size_row_min = -int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_ROW_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY)
		crop_size_row_max = int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_ROW_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY)
		crop_size_col_min = -int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_COL_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY)
		crop_size_col_max = int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_COL_RATIO_XY*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_XY)
	elif test_bench == DEFINES.PC_CAMERA_TYPE_TILT:
		crop_size_row_min = -int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_ROW_RATIO_TILT*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT)
		crop_size_row_max = int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_ROW_RATIO_TILT*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT)
		crop_size_col_min = -int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_COL_RATIO_TILT*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT)
		crop_size_col_max = int(diameter*DEFINES.CC_SMALL_IMAGE_CROP_COL_RATIO_TILT*DEFINES.CC_COMPUTATION_SIGMA_CROP_RATIO_TILT)
	else:
		return [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,result_ID]

	row_centroid = int(centroids[DEFINES.CC_ROW_COORDINATE])
	col_centroid = int(centroids[DEFINES.CC_COL_COORDINATE])

	#Check that the crop remains in the image
	if row_centroid+crop_size_row_min<0:
		crop_size_row_min = -row_centroid
	if row_centroid+crop_size_row_max>image_shape[DEFINES.CC_ROW_COORDINATE]:
		crop_size_row_max = image_shape[DEFINES.CC_ROW_COORDINATE]-row_centroid
	if col_centroid+crop_size_col_min<0:
		crop_size_col_min = -col_centroid
	if col_centroid+crop_size_col_max>image_shape[DEFINES.CC_COL_COORDINATE]:
		crop_size_col_max = image_shape[DEFINES.CC_COL_COORDINATE]-col_centroid

	image_small = image[	(row_centroid+crop_size_row_min):(row_centroid+crop_size_row_max),\
							(col_centroid+crop_size_col_min):(col_centroid+crop_size_col_max)]

	col_corr_small = col_corr[	(row_centroid+crop_size_row_min):(row_centroid+crop_size_row_max),\
								(col_centroid+crop_size_col_min):(col_centroid+crop_size_col_max)]
	row_corr_small = row_corr[	(row_centroid+crop_size_row_min):(row_centroid+crop_size_row_max),\
								(col_centroid+crop_size_col_min):(col_centroid+crop_size_col_max)]

	#Apply the correction on the cropped image. Arrays are [ROW,COL] instead of [x,y]
	rowIn = np.array([np.mgrid[0:crop_size_row_max-crop_size_row_min],]*(crop_size_col_max-crop_size_col_min)).transpose()
	colIn = np.array([np.mgrid[0:crop_size_col_max-crop_size_col_min],]*(crop_size_row_max-crop_size_row_min))
	
	rowIn = np.add(rowIn, row_corr_small)
	colIn = np.add(colIn, col_corr_small)
	
	data_min = DEFINES.CC_IMAGE_THRESHOLD_MIN
	data_max = DEFINES.CC_IMAGE_THRESHOLD_MAX_RATIO*np.max(image_small)

	mm.threshold(image_small,data_min,data_max)

	current_image = image_small.copy()
	current_colIn = colIn.copy()
	current_rowIn = rowIn.copy()
	
	#Fit a 2D mm.gaussian
	if cameraProps.cameraType == DEFINES.PC_CAMERA_TYPE_XY:
		params = mm.fitgaussian(current_image,current_colIn,current_rowIn,data_min,data_max, DEFINES.CC_OPTIMIZER_TOLERANCE_XY)
	else:
		params = mm.fitgaussian(current_image,current_colIn,current_rowIn,data_min,data_max, DEFINES.CC_OPTIMIZER_TOLERANCE_TILT)
	(height, center_col, center_row, width_col, width_row, n) = params
	
	#rescale the result
	center_col = center_col+crop_size_col_min
	center_row = center_row+crop_size_row_min

	col_out = col_centroid+center_col+col_offset # Add centroid offset and ROI offset
	row_out = row_centroid+center_row+row_offset

	return [col_out*scale_factor,row_out*scale_factor,col_out,row_out,width_col,width_row,height,result_ID]

def main():
	import miscmath as mm
	import matplotlib.pyplot as plt
	import classCamera

	imgSizeX = 200
	imgSizeY = 100

	cam = classCamera.Camera()
	cam.parameters = classCamera.CameraParameters(DEFINES.PC_CAMERA_TYPE_XY, None)
	cam.parameters.ROIoffsetX = 0
	cam.parameters.ROIoffsetY = 0
	cam.parameters.xCorr = np.zeros((imgSizeX,imgSizeY))
	cam.parameters.yCorr = np.zeros((imgSizeX,imgSizeY))
	cam.parameters.scaleFactor = 1

	Xin = np.array([np.mgrid[0:imgSizeX],]*(imgSizeY)).transpose()
	Yin = np.array([np.mgrid[0:imgSizeY],]*(imgSizeX))
	imgIn = np.zeros((imgSizeX,imgSizeY))
	# centroid = gaussian(height, center_x, center_y, width_x, width_y, n)
	imgIn = mm.gaussian(255, 23.44, 18.08, 2.7, 2.8, 1.5)(Xin,Yin)
	# corrHeight = 2
	# cam.parameters.xCorr = np.subtract(mm.gaussian(corrHeight, 2500, 1500, 500, 500, 1)(Xin,Yin),corrHeight)
	# cam.parameters.yCorr = np.subtract(mm.gaussian(corrHeight, 2500, 1500, 500, 500, 1)(Xin,Yin),corrHeight)

	plt.figure()
	plt.pcolormesh(Xin, Yin, imgIn, cmap=plt.cm.viridis)
	plt.draw()
	plt.pause(1e-17)
	# plt.figure()
	# plt.pcolormesh(Xin, Yin, cam.parameters.xCorr, cmap=plt.cm.viridis)
	# plt.draw()
	# plt.pause(1e-17)
	# plt.figure()
	# plt.pcolormesh(Xin, Yin, cam.parameters.yCorr, cmap=plt.cm.viridis)
	# plt.draw()
	# plt.pause(1e-17)

	centroid = compute_centroid(imgIn,cam.parameters,1)
	print(centroid)
	plt.figure()
	plt.pcolormesh(np.add(Xin,cam.parameters.xCorr) , np.add(Yin, cam.parameters.yCorr), imgIn, cmap=plt.cm.viridis)
	plt.scatter(centroid[1],centroid[0],marker ='x',c='red')
	plt.draw()
	plt.pause(1e-17)
	plt.show()
	
	pass

if __name__ == '__main__':
	main()