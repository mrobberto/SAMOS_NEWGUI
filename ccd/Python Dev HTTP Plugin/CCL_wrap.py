import ctypes
from ctypes import *
import os
from sys import platform as _platform



class DllCalls(object):
	''' encapsulates DLL calls '''
	def __init__(self,color='green'):
		''' initialize DLL wrapper '''
		self.color = color
		if _platform == "linux" or _platform == "linux2":
			self.SiCamLib = ctypes.CDLL("libsivcam.so")
#		elif _platform == "darwin":
#			a=10		# OS X
		elif _platform == "win32":
			self.SiCamLib = ctypes.WinDLL (os.getcwd()+"\SiVCamDll_64.dll")

	def ScanInterfaces(self):
		''' invokes interface scan, returns XML string '''
		xmlStr=ctypes.create_string_buffer(10000)
		xLen = (c_long)(10000)
		xForce = (c_bool)(False)
		self.SiCamLib.ScanInterfaces(byref(xmlStr),byref(xLen),xForce)
		return xmlStr.value.decode('utf-8')

	def GetErrorString(self,number):
		''' returns an explanatory string for a given error number
			number: error number to be looked up.
			returns: string containing the error explanation.
		'''
		errStr=ctypes.create_string_buffer(1000)
		xLen = (c_long)(1000)
		self.SiCamLib.GetErrorString((c_long)(number),byref(errStr),byref(xLen))
		return errStr.value.decode('utf-8')

	def OpenCamera(self,name,plugin):
		''' opens a camera referenced by device name and plugin name
			name: string - device name as returned by ScanInterfaces
			plugin: string - plugin name as returned by ScanInterfaces
			returns: camera handle. Use this handle for all accesses to this camera.
					-1 if camera could not be opened.
		'''
		c_plug = create_string_buffer(32)
		c_plug.value = bytes(plugin,'utf-8')
		c_name = create_string_buffer(32)
		c_name.value = bytes(name,'utf-8')				#### opposite is str(name,'utf-8')
		cameraHandle = self.SiCamLib.OpenCamera(byref(c_name),byref(c_plug))
		return cameraHandle

	def CameraHwReset(self,name,plugin):
		''' sends a reset signal to an interface without the camera opened.
			This is a last resort reset attempt and should be used with care.
					-1 if reset failed.
		'''
		c_plug = create_string_buffer(32)
		c_plug.value = bytes(plugin,'utf-8')
		c_name = create_string_buffer(32)
		c_name.value = bytes(name,'utf-8')				#### opposite is str(name,'utf-8')
		cameraHandle = self.SiCamLib.CameraHwReset(byref(c_name),byref(c_plug))
		return cameraHandle

	def GetXmlFile(self,cam,fileName):
		''' retrieves a file from camera
			cam: camera handle as returned by OpenCamera
			fileName: string - name of the file to be retrieved from camera
			returns: string containing the file data i.e.XML file
		'''
		c_cam = (c_long)(cam)
		c_name = create_string_buffer(128)
		c_name.value = bytes(fileName,'utf-8')
		xmlStr=ctypes.create_string_buffer(100000)
		xLen = (c_long)(100000)
		retval = self.SiCamLib.GetXmlFile(c_cam,byref(c_name),byref(xmlStr),byref(xLen))
		return xmlStr.value.decode('utf-8')

	def GetStatusNames(self,cam):
		''' returns a list of status names
			cam: camera handle as returned by OpenCamera
			returns: string containing all status names from camera database
		'''
		myStr=ctypes.create_string_buffer(100000)
		sLen = (c_long)(100000)
		retval = self.SiCamLib.GetStatusNames((c_long)(cam),byref(myStr),sLen)
		return myStr.value.decode('utf-8')

	def GetStatus(self,cam):
		''' causes the status to be read from the camera and loaded into database
			cam: camera handle as returned by OpenCamera
		'''
		retval = self.SiCamLib.GetStatus((c_long)(cam))
		return retval

	def GetStatusItem(self,cam,name):
		''' returns one status item from the database
			cam: camera handle as returned by OpenCamera
			returns tuple: (string: value,
							integer: unit type,
							string: unit string,
							string: step size)
		'''
		c_name = create_string_buffer(128)
		c_name.value = bytes(name,'utf-8')
		valStr=ctypes.create_string_buffer(100)
		unitStr=ctypes.create_string_buffer(100)
		stepStr=ctypes.create_string_buffer(100)
		sLen = (c_long)(100)
		c_utype = (c_short)(-1)
		retval = self.SiCamLib.GetStatusItem((c_long)(cam),byref(c_name),byref(valStr),sLen,byref(c_utype),byref(unitStr),sLen,byref(stepStr),sLen)
		return (valStr.value.decode('utf-8'),
				c_utype.value,
				unitStr.value.decode('utf-8'),
				stepStr.value.decode('utf-8'))

	def GetStatusPulldownItem(self,Cam,displayName,PulldownIndex):
		''' Returns values for one pull down entry. When the unit_type indicates this being a pull down or a sparsely
		populated list, it contains the number of pull down entries in it's Max value (see GetParameterItem). In a
		loop from 0 to <max the individual pull down entries can be retrieved to build the complete pull down. In case
		of pull down, the returned PulldownValue entries will just be the index. In case of a sparsely populated list,
		the PulldownValue holds the value of the respective entry.
		'''
		#inputs
		c_displayName = create_string_buffer(128)
		c_displayName.value = bytes(displayName,'utf-8')
		c_PulldownIndex = (c_long)(PulldownIndex)
		#outputs
		PulldownValStr = ctypes.create_string_buffer(100)
		PulldownName = ctypes.create_string_buffer(100)
		retval = self.SiCamLib.GetStatusPulldownItem((c_long)(Cam),byref(c_displayName),(c_int)(c_PulldownIndex),
													 byref(PulldownValStr),(c_long)(len(PulldownValStr)),
													 byref(PulldownName),(c_long)(len(PulldownName)))
		return (PulldownValStr.value.decode('utf-8'),PulldownName.value.decode('utf-8'))

	def GetStatusValue(self,cam,name):
		''' gets a status value from the database
			cam: camera handle as returned by OpenCamera
			returns: string - status value
		'''
		myStr=ctypes.create_string_buffer(10000)
		sLen = (c_long)(10000)
		c_name = create_string_buffer(128)
		c_name.value = bytes(name,'utf-8')
		retval = self.SiCamLib.GetStatusValue((c_long)(cam),byref(c_name),byref(myStr),sLen)
		return myStr.value.decode('utf-8')

	def UpdateParameters(self,cam):
		''' updates the parameter database using
			abreviated XML files
		'''
		retval = self.SiCamLib.UpdateParameters((c_long)(cam))
		return retval

	def GetParameterItem(self,cam,name):
		''' returns one parameter item from the database
			cam: camera handle as returned by OpenCamera
			returns tuple: (string: value,
							string: min value,
							string: max value,
							integer: unit type,
							string: unit string,
							string: step size)
		'''
		c_name = create_string_buffer(128)
		c_name.value = bytes(name,'utf-8')
		valStr=ctypes.create_string_buffer(100)
		minStr=ctypes.create_string_buffer(100)
		maxStr=ctypes.create_string_buffer(100)
		unitStr=ctypes.create_string_buffer(100)
		stepStr=ctypes.create_string_buffer(100)
		sLen = (c_long)(100)
		c_utype = (c_short)(-1)
		retval = self.SiCamLib.GetParameterItem((c_long)(cam),byref(c_name),byref(valStr),sLen,byref(minStr),sLen,byref(maxStr),sLen,byref(c_utype),byref(unitStr),sLen,byref(stepStr),sLen)
		return (valStr.value.decode('utf-8'),
				minStr.value.decode('utf-8'),
				maxStr.value.decode('utf-8'),
				c_utype.value,
				unitStr.value.decode('utf-8'),
				stepStr.value.decode('utf-8'))

	def GetParameterNames(self,cam):
		''' returns a list of parameter names
			cam: camera handle as returned by OpenCamera
			returns: string containing all parameter names from camera database
		'''
		myStr=ctypes.create_string_buffer(100000)
		sLen = (c_long)(100000)
		retval = self.SiCamLib.GetParameterNames((c_long)(cam),byref(myStr),sLen)
		return myStr.value.decode('utf-8')

	def GetParameterPulldownItem(self,Cam,displayName,PulldownIndex):
		'''
		Returns values for one pull down entry. When the unit_type indicates this being a pull down or a sparsely
		populated list, it contains the number of pull down entries in it's Max value (see GetParameterItem). In
		a loop from 0 to max the individual pull down entries can be retrieved to build the complete pull down.
		In case of pull down, the returned PulldownValue entries will just be the index. In case of a sparsely
		populated list, the PulldownValue holds the value of the respective entry.
		'''
		c_displayName = create_string_buffer(128)
		c_displayName.value = bytes(displayName,'utf-8')
		#outputs
		PulldownValStr = ctypes.create_string_buffer(100)
		PulldownName = ctypes.create_string_buffer(100)
		retval = self.SiCamLib.GetParameterPulldownItem((c_long)(Cam),byref(c_displayName),(c_long)(PulldownIndex),
														byref(PulldownValStr),(c_long)(len(PulldownValStr)),
														byref(PulldownName),(c_long)(len(PulldownName)))
		return (PulldownValStr.value.decode('utf-8'),PulldownName.value.decode('utf-8'))

	def GetParameterValue(self,cam,name):
		''' gets a parameter value from the database
			cam: camera handle as returned by OpenCamera
			returns: string - parameter value
		'''
		myStr=ctypes.create_string_buffer(10000)
		sLen = (c_long)(10000)
		c_name = create_string_buffer(128)
		c_name.value = bytes(name,'utf-8')
		retval = self.SiCamLib.GetParameterValue((c_long)(cam),byref(c_name),byref(myStr),sLen)
		return myStr.value.decode('utf-8')

	def SetParameterValue(self,cam,name,valStr):
		''' sets a parameter value
			cam: camera handle as returned by OpenCamera
			name: string - parameter name
			valStr: string - value to be set
			returns: integer - error number 0: no error
		'''
		c_name = create_string_buffer(128)
		c_name.value = bytes(name,'utf-8')
		c_valstr = create_string_buffer(128)
		c_valstr.value = bytes(valStr,'utf-8')
		retval = self.SiCamLib.SetParameterValue((c_long)(cam),byref(c_name),byref(c_valstr))
		return retval

	def SendParameters(self,cam):
		retval = self.SiCamLib.SendParameters((c_long)(cam))
		return retval

	def GetImageSize(self,cam):
		''' gets image size information
			cam: camera handle as returned by OpenCamera
			returns tuple: (integer: serial length of image,
							integer: parallel length of image,
							integer: 1: is 16 bit image; 0: is 32 bit image,
							integer: number of CCDs along serial dimension
							integer: number of CCDs along parallel dimension
							integer: number of serial sections
							integer: number of parallel sections)

		'''
		c_imgSerLen = (c_ulong)(0)
		c_imgParLen = (c_ulong)(0)
		c_is16 = (c_ulong)(0)
		c_nSerCCD = (c_ulong)(0)
		c_nParCCD = (c_ulong)(0)
		c_nSerSect = (c_ulong)(0)
		c_nParSect = (c_ulong)(0)
		retval = self.SiCamLib.GetImageSize((c_long)(cam),
			byref(c_imgSerLen),
			byref(c_imgParLen),
			byref(c_is16),
			byref(c_nSerCCD),
			byref(c_nParCCD),
			byref(c_nSerSect),
			byref(c_nParSect))
		return (c_imgSerLen.value,c_imgParLen.value,c_is16.value,c_nSerCCD.value,c_nParCCD.value,c_nSerSect.value,c_nParSect.value)

	def IssueCommand(self,cam,postName,argStr):
		''' Sends a command to the camera
			cam: camera handle as returned by OpenCamera
			postName: string - command
			argStr: string - argument string
			returns: string - command response from camera (ends with prompt)
		'''
		c_postName = create_string_buffer(128)
		c_postName.value = bytes(postName,'utf-8')
		c_argStr = create_string_buffer(1000)
		c_argStr.value = bytes(argStr,'utf-8')
		retStr=ctypes.create_string_buffer(100000)
		sLen = (c_long)(100000)
		retval = self.SiCamLib.IssueCommand((c_long)(cam),byref(c_postName),byref(c_argStr),byref(retStr),sLen)
		return retStr.value.decode('utf-8')

	def PrepareFileSave(self,cam,fileName,fitsHeader,fileType):
		''' prepares direct file save
			cam: camera handle as returned by OpenCamera
			fileName: location and name of image storage. If no auto save is required, pass an empty string.
						If fileName is specified, a fitsHeader must be provided
			fitsHeader: string which will prepended to image data when auto saved.
			fileType:	string containing the file type. Only "FIT" supported currently
		'''
		c_fileName = create_string_buffer(1000)
		c_fileName.value = bytes(fileName,'utf-8')
		c_fitsHeader = create_string_buffer(1000)
		c_fitsHeader.value = bytes(fitsHeader,'utf-8')
		c_fileType = create_string_buffer(1000)
		c_fileType.value = bytes(fileType,'utf-8')
		retval = self.SiCamLib.PrepareFileSave((c_long)(cam),byref(c_fileName),byref(c_fitsHeader),byref(c_fileType))
		return retval
	def PrepareAcqFilm(self,cam,serLen,parLen,nBuffers,is16):
		''' prepares a sequence acquisition in "Film" mode
			cam: camera handle as returned by OpenCamera
			serLen: size of serial dimension of expeted image (as returned by GetImageSize).
			parLen: size of parallel dimension of expeted image (as returned by GetImageSize).
			nBuffers: number of image buffers to allocate for the acquition
			is16: 1 for 16 bit unsigned image data. 0 for 32 bit signed imaga data (camera dependent)
		'''
		b=True
		if is16:
			self.imgarr = (c_ushort * (serLen * parLen * nBuffers))()	# keep in context
		else:
			self.imgarr = (c_long * (serLen * parLen * nBuffers))()	# keep in context
		retval = self.SiCamLib.PrepareAcqFilm((c_long)(cam),(c_uint16)(serLen),(c_uint16)(parLen),byref(self.imgarr),(c_uint16)(nBuffers),(bool)(b))
		return retval
	def PrepareFramesAcquisition(self,cam,serLen,parLen,fileName,fitsHeader,fcount):
		'''	prepares an image  transfer
			cam: camera handle as returned by OpenCamera
			serLen: size of serial dimension of expeted image (as returned by GetImageSize).
			parLen: size of parallel dimension of expeted image (as returned by GetImageSize).
			fileName: location and name of image storage. If no auto save is required, pass an empty string.
						If fileName is specified, a fitsHeader must be provided
			fitsHeader: string which will prepended to image data when auto saved.
			fcount:	number of frames to be taken. if 0, acquisition is indefinite until endAcq is called.
			returns: integer - error number 0: no error
		'''
		c_fileName = create_string_buffer(1000)
		c_fileName.value = bytes(fileName,'utf-8')
		c_fitsHeader = create_string_buffer(1000)
		c_fitsHeader.value = bytes(fitsHeader,'utf-8')
		self.imgarra = (c_ushort * (serLen * parLen))()	# keep in context
		self.imgarrb = (c_ushort * (serLen * parLen))()	# keep in context
		retval = self.SiCamLib.PrepareAcqU16((c_long)(cam),(c_uint16)(serLen),(c_uint16)(parLen),byref(self.imgarra),byref(self.imgarrb),(c_int)(fcount),byref(c_fileName),byref(c_fitsHeader))
		return retval

	def FramesAcqStatus(self,cam):
		''' gets readout status from camera
			cam: camera handle as returned by OpenCamera
			returns: tuple: (integer: readout percent
							integer: current frame
							integer: status flag  (bit0=1: imgarra is availabe bit1=1: imgarrb is availabe)
							)
		'''
		c_readPc = (c_uint16)(0)
		c_frame = (c_uint32)(0)
		c_statusFlag = (c_uint32)(0)
		retval = self.SiCamLib.AcqStatus((c_long)(cam),byref(c_readPc),byref(c_frame),byref(c_statusFlag))
		return (c_readPc.value,c_frame.value,c_statusFlag.value)

	def closeCam(self,Cam):
		'''	closes camera
			cam: camera handle as returned by OpenCamera
			returns: integer - error number 0: no error
		'''
		retval = self.SiCamLib.CloseCamera((c_long)(Cam))
		return retval

	def endAcq(self,Cam,b=True):
		'''	ends an acquisition. This function must be called after an image acquisition
			to unload the internal elemets the driver has loaded.
			With b=True, an abort is issued when the current image transfer is still ongoing.
			cam: camera handle as returned by OpenCamera
			b: abort flag (True: force abort, False: cleanup only)
		'''
		retval = self.SiCamLib.EndAcq((c_long)(Cam),(bool)(b))
		return retval

	def PrettyString(self,inValue,inType):
		''' returns a formatted string according to the unit type
			inValue: string - value to be formatted
			inType: integer - unit type
			returns: formatted string
		'''
		if inType == 1:
			outStr = "pressure raw: "+inValue
		elif inType == 2:
			outStr = inValue + " mTorr"
		elif inType == 3:
			temp = float(inValue)/10.0-273.15
			outStr = "{:.1f} degC".format(temp)
		elif inType == 4:
			temp = float(inValue)/1000.0
			outStr = "{:.3f} V".format(temp)
		elif inType == 5:
			temp = float(inValue)
			outStr = "{:.1f} V".format(temp)
		elif inType == 6:
			temp = float(inValue)/1000.0
			outStr = "{:.3f} A".format(temp)
		elif inType == 7:
			temp = float(inValue)/1000.0
			outStr = "{:.3f} sec".format(temp)
		else:
			outStr = "unknown type: "+inValue
		return outStr
