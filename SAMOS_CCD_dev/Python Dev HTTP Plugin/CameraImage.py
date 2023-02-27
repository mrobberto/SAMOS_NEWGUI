from CCL_wrap import *
from xml.dom.minidom import *
import time
import numpy as np
from pylab import*
#import pyfits as pf
from ctypes import *

f = DllCalls()      # get dll object

ExposTime = 1000        # sets exposure time in ms
AcqMode = 0             # sets Acquisition mode. 0 is actual image type (see command.xml)
# this scans all plugins for existing interfaces and cameras
# if the camera device and plugin name is known, ScanInterfaces does not need to be called
# from the output of ScanInterfaces the desired device name (dev) and plugin name (plug) can be derived
xml = f.ScanInterfaces()                                        # gets available interfaces 
print(xml)

print("\n\nwait for camera to be opened\n\n")
#dev = "169.254.75.1"
dev = "128.220.146.254"
plug = "HttpXcpCamera"
camHandle = f.OpenCamera(dev, plug)
#camHandle = f.OpenCamera("SIPCI", "PciXcpCamera")	# this is the call for the 1110 camera

if camHandle >= 0:
	print("camera opened")
	# the following printouts are for reference only
	commands = f.GetXmlFile(camHandle,"command.xml")	# returns the allowable commands as XML
	print("commands:")
	print(commands)
	f.IssueCommand(camHandle,'SHUTTER','0')		# example of issuing a command to the camera

	# camera parameters and status values are referenced by the ASCII names. Here are the available names:
	parameterNames = f.GetParameterNames(camHandle)		# lists all known parameter names [Category,Name,read/write]
	print (parameterNames)
	statusNames = f.GetStatusNames(camHandle)			#lists all known status names [Category,Name]
	print(statusNames)

	fc = input('Enter Frame Count -->')             # prompts for number of frames from user
	fcount = int(fc)                                # sets number of frames for camera to take 
	print("setting test image type: {:0d}".format(AcqMode))

	# setting parameters: Parameter names must be exactly as in parameter list.
	# SetParameterValue only stages the command. It is sent to camera with SendParameters
	errval = f.SetParameterValue(camHandle,"Acquisition mode",str(AcqMode)) #command to set acquisition mode
	print(errval)
	print("setting exposure time")
	errval = f.SetParameterValue(camHandle,"Exposure Time",str(ExposTime))  # command to set exposure time
	print(errval)
	print("setting frame count")
	errval = f.SetParameterValue(camHandle,"Frame Count",str(fcount))      #  command to set frame count 
	print(errval)
	errval = f.SendParameters(camHandle)                                    # sends command to set values defined above
	print(errval)

	print("geting image size")
	imgSerLen, imgParLen, is16, nSerCCD, nParCCD, nSerSect, nParSect = f.GetImageSize(camHandle)    #gets image size, type and # of CCDs from camera and sets them to variables
	print("imgSerLen: {:0d}".format(imgSerLen))
	print("imgParLen: {:0d}".format(imgParLen))
	print("is16:      {:0d}".format(is16))
	print("nSerCCD:   {:0d}".format(nSerCCD))
	print("nParCCD:   {:0d}".format(nParCCD))
	print("nSerSect:  {:0d}".format(nSerSect))
	print("nParSect:  {:0d}".format(nParSect))

	print("geting status")
	readPc, frameNum, statusFlag = f.FramesAcqStatus(camHandle)                      # checks camera status 
	print("Frame Number")
	print(frameNum)
	print("ReadPc")
	print(readPc)
	print("preparing acquisition")

	nBuffers = 1	# number of image buffers to allocate for frames acquisition. Driver will roll through these buffers regardless of frame count
	retval = f.PrepareAcqFilm(camHandle,imgSerLen,imgParLen,nBuffers,True)
	print("RetVal")
	print(retval)
	print("IMGARR")
        
	print( 'shape is' + str(shape(f.imgarr)))       #image array should be 1D array 
	retarr = []
	
	response = f.IssueCommand(camHandle,"ACQUIRE","0")      # initiates image capture
	print('printed response' + response)
	print(time.time())
	startTime = time.time()
	st = 0
	#while time.time() < startTime +3.5:
	frameNum = 0
	while readPc != 100 or frameNum < fcount:                 #gets and reports readout status until it is done reading out image first exposure happens then read
		readPc, frameNum, finishedFrame = f.FramesAcqStatus(camHandle)
		print("time: {:.2f} readPc:{:0d} frameNum:{:0d} finishedFrame:{:0b}".format(time.time() - startTime,readPc, frameNum, finishedFrame))
		if st !=finishedFrame:
			#here the image is complete. In case of multiple buffers being used, the offset into the f.imgarr needs to be evaluated
			retarr.append(f.imgarr)
			print("set image {:0d} from imgarra".format(frameNum))
		st = finishedFrame
		# a sleep can be inserted to avoid busyness

	f.endAcq(camHandle)		# endAcq MUST be called after each acquisition to initiate memory cleanup
	print('ended acq')
	f.closeCam(camHandle)
	print('closed camera')



	i = 0
	while i < len(retarr):
		pfname = 'image{:0d}.fits'.format(i+1)
		rfloat = asfarray(retarr[0])               #converts to float array
		ruint= rfloat.astype(uint16)            # converts to array of 16 bit unsigned integers 
		reshaped = reshape(rfloat,(imgParLen,-1))       #reshapes array to 2D 
		imshow(reshaped,cmap=cm.gray)
		show()                                  # shows image. Note pixel 0,0 is shown to be in top left corner, not lower left, so image is rotated 


		## the FITS converter did not work, so it is disabled here
		
		# hdu = pf.PrimaryHDU(ruint)             ##makes fits dada object from array
		# hdrtemplate = pf.getheader('fitstemplate.fits')     ##opens a template fits file
		# locTime = time.localtime(time.time())           #gets time to use for fits header
		# hdrtemplate['NAXIS1'] = imgSerLen
		# hdrtemplate['NAXIS2'] = imgParLen
		# hdulist = pf.HDUList([hdu]) # packs  data into file            
		# hdulist[0].header = hdrtemplate
		# #writes to file  i think this overwrites the dimensions and  naxis of the image to reflect the array actually being saved, which is a 1D array
		# hdulist.writeto(pfname, output_verify = 'ignore', clobber = True)                 
		# pf.setval(pfname , 'NAXIS', value = -16)              #sets data type to SpecInst standard representing unsigned 16bit int.
		# pf.setval(pfname , 'NAXIS1', value =imgSerLen)              #resets first axis length
		# pf.setval(pfname , 'NAXIS2', value =imgParLen, after = 'NAXIS1')              #adds second axis which pyfits function removes 
		# print('saved image {:0d} as \"image{:0d}.fits\"'.format(i+1,i+1))
		i = i+1

		
else:
	print("camera failed to open")
	
    

##dom = parseString(xml)
##print(dom.toprettyxml())

s = input('DONE hit ENTER -->')









	
