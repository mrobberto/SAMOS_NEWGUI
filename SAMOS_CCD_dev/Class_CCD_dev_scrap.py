from urllib.request import Request,urlopen
from urllib.error import URLError,HTTPError
import socket
from time import sleep,time
#from msvcrt import getch,kbhit
import xml.dom.minidom
#import sys
import os

### Substitute getch from https://www.reddit.com/r/learnpython/comments/7036k5/can_i_use_getch_on_macos_x/
import sys, tty, termios

### Needed to run ConvertSIlly by C. Loomis
import math
import pathlib

#needed to navigate the SAMOS_GUI directory tree
from pathlib import Path
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)   
sys.path.append(parent_dir)

from SAMOS_system_dev.SAMOS_Functions import Class_SAMOS_Functions as SF


class Class_Camera(object):
    
    def __init__(self,dict_params):
        self.dict_params = dict_params.copy() #in the class, make a copy of the dict
        self.ExpTime = dict_params['Exposure Time']
        self.DetTemp = dict_params['CCD Temperature']
        self.TriggerMode = dict_params['Trigger Mode']
 
        IP_status_dict = SF.read_IP_status()
        IP_dict = SF.read_IP_default()
        print(IP_status_dict,IP_dict)
        if IP_status_dict['IP_CCD'] == 'True':
            self.IP_Host = str(IP_dict['IP_CCD']).split(':')[0]
            self.IP_Port = int(str(IP_dict['IP_CCD']).split(':')[1])
        else: 
            print('CCD NOT CONNECTED')
 
#        self.params = {'Host': '128.220.146.254', 'Port': 8900}
        self.params = {'Host': '172.16.0.245', 'Port': 80}

    def getch(char_width=1):
        '''get a fixed number of typed characters from the terminal. 
        Linux / Mac only'''
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(char_width)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    ####
    
    
    def get_url(self,url_name,post_data=None):
    	if(None!=post_data):
    		post_data=post_data.encode()
    	req=Request(url_name,post_data)
    	try:
    		response=urlopen(req,timeout=7)
    	except HTTPError as e:
    		print("The server couldn't fulfill the request. Error code:",e.code)
    		html=b""
    	except URLError as e:
    		print('We failed to reach a server. Reason:',e.reason)
    		html=b""
    	except ConnectionAbortedError:
    		print('The server aborted the connection.')
    		html=b""
    	except ConnectionError:
    		print('Connection error.')
    		html=b""
    	except ConnectionRefusedError:
    		print('The server refused the connection.')
    		html=b""
    	except ConnectionResetError:
    		print('The server reset the connection.')
    		html=b""
    	except socket.timeout:
    		print('Connection timed out.')
    		html=b""
    	else:
    		html=response.read()
    	return html
    
    def get_url_as_string(self,url_name,post_data=None):
    	return str(self.get_url(url_name,post_data),encoding="utf-8",errors='ignore')
    
    def xml_parameter_tag(self,param_list,display_name,tag_name):
    	for node in param_list:
    		if(display_name==node.getElementsByTagName("display")[0].childNodes[0].data):
    			return node.getElementsByTagName(tag_name)[0].childNodes[0].data
    	return None
    def xml_parameter_pulldown_value(self,param_list,display_name,pulldown_name):
    	for node in param_list:
    		if(display_name==node.getElementsByTagName("display")[0].childNodes[0].data):
    			pulldown=node.getElementsByTagName("pull_down")
    			for node2 in pulldown:
    				if(pulldown_name==node2.getElementsByTagName("display")[0].childNodes[0].data):
    					return node2.getElementsByTagName("value")[0].childNodes[0].data
    	return None
    def param_bounds(self,xml_str):
    	i=xml_str.index('<parameter>')
    	j=xml_str.index('</list>')
    	return (i,j)


#ConvertSIlly courtesy of C. Loomis
    def convertSIlly(self,fname, outname=None):
    	FITSblock = 2880

    # If no output file given, just prepend "fixed"
    	if outname is None:
    	        fname = pathlib.Path(fname)
    	        dd = fname.parent
    	        outname = pathlib.Path(fname.parent, 'fixed'+fname.name)
    
    	with open(fname, "rb") as in_f:
    	        buf = in_f.read()

    # Two fixes:
    # Header cards:
    	buf = buf.replace(b'SIMPLE  =                    F', b'SIMPLE  =                    T')
    	buf = buf.replace(b'BITPIX  =                  -16', b'BITPIX  =                   16')
    	buf = buf.replace(b"INSTRUME= Spectral Instruments, Inc. 850-406 camera  ", b"INSTRUME= 'Spectral Instruments, Inc. 850-406 camera'")
    
    # Pad to full FITS block:
    	blocks = len(buf) / FITSblock
    	pad = round((math.ceil(blocks) - blocks) * FITSblock)
    	buf = buf + (b'\0' * pad)
    
    	with open(outname, "wb+") as out_f:
    	        out_f.write(buf)
        


    
    def expose_original(self):
    	if 2<=len(sys.argv):
    		target=sys.argv[1]
    	else:
    		target=self.IP_Host+":"+str(self.IP_Port)
                    #'128.220.146.254:8900'
                    #'192.168.0.223'
    	if 3<=len(sys.argv):
    		iterations=sys.argv[2]
    		iterations=int(iterations)
    	else:
    		iterations=1
    	target='http://'+target+'/'
    	print("URI=%s" % target)
    	# Combine the various XML parameter files
    	xml_str=self.get_url_as_string(target+'setup.xml')
    	if len(xml_str)<9:
    		exit()
    	i,j=self.param_bounds(xml_str)
    	xml_hdr=xml_str[0:i]
    	xml_param=xml_str[i:j]
    	xml_ftr=xml_str[j:len(xml_str)]
    	xml_str=self.get_url_as_string(target+'control.xml')
    	i,j=self.param_bounds(xml_str)
    	xml_param+=xml_str[i:j]
    	xml_str=self.get_url_as_string(target+'factory.xml')
    	i,j=self.param_bounds(xml_str)
    	xml_param+=xml_str[i:j]
    	xml_str=self.get_url_as_string(target+'miscellaneous.xml')
    	i,j=self.param_bounds(xml_str)
    	xml_param+=xml_str[i:j]
    	xml_str=xml_hdr+xml_param+xml_ftr
        
    	print(xml_param)
    	# Extract the parameter information we require from the combined XML DOM
    	with xml.dom.minidom.parseString(xml_str) as dom:
    		dom_list=dom.getElementsByTagName("list")[0]
    		param_list=dom_list.getElementsByTagName("parameter")
    		par_pix=int(self.xml_parameter_tag(param_list,"Parallel Active Pix.","value"))
    		ser_pix=int(self.xml_parameter_tag(param_list,"Serial Active Pix.","value"))
    		source_cmd=self.xml_parameter_tag(param_list,"Server Data Source","post_name")
    		source_camera=self.xml_parameter_pulldown_value(param_list,"Server Data Source","Camera")
    		#source_server=xml_parameter_pulldown_value(param_list,"Server Data Source","Server")
    		test_img_cmd=self.xml_parameter_tag(param_list,"Server Test Image Type","post_name")
    		walking_1=self.xml_parameter_pulldown_value(param_list,"Server Test Image Type","Walking 1")
    		serial_origin_cmd=self.xml_parameter_tag(param_list,"Serial Origin","post_name")
    		serial_length_cmd=self.xml_parameter_tag(param_list,"Serial Length","post_name")
    		serial_post_scan_cmd=self.xml_parameter_tag(param_list,"Serial Post Scan","post_name")
    		serial_binning_cmd=self.xml_parameter_tag(param_list,"Serial Binning","post_name")
    		serial_phasing_cmd=self.xml_parameter_tag(param_list,"Serial Phasing","post_name")
    		parallel_origin_cmd=self.xml_parameter_tag(param_list,"Parallel Origin","post_name")
    		parallel_length_cmd=self.xml_parameter_tag(param_list,"Parallel Length","post_name")
    		parallel_post_scan_cmd=self.xml_parameter_tag(param_list,"Parallel Post Scan","post_name")
    		parallel_binning_cmd=self.xml_parameter_tag(param_list,"Parallel Binning","post_name")
    		parallel_phasing_cmd=self.xml_parameter_tag(param_list,"Parallel Phasing","post_name")
    		port_select_cmd=self.xml_parameter_tag(param_list,"Port Select","post_name")
    		exposure_time_cmd=self.xml_parameter_tag(param_list,"Exposure Time","post_name")
    		trigger_mode_cmd=self.xml_parameter_tag(param_list,"Trigger Mode","post_name")
    	with xml.dom.minidom.parseString(self.get_url_as_string(target+'command.xml')) as dom:
    		dom_list=dom.getElementsByTagName("list")[0]
    		param_list=dom_list.getElementsByTagName("parameter")
    		acquire_cmd=self.xml_parameter_tag(param_list,"Acquire an image.","post_name")
    		xml_str=self.xml_parameter_pulldown_value(param_list,"Acquire an image.","Light")
    		print('\nxml_list\n',xml_str)
    	acquire_cmd+=" "+xml_str
    	# Construct the commands needed to initialize the HTTP Camera Server
    	i=528#2048	# This is our desired serial size in pixels for this test
    	binning=int((ser_pix+i-1)/i)
    	#cmd_str="{}=1000".format(exposure_time_cmd)
    	cmd_str="{}={}".format(exposure_time_cmd,str(self.ExpTime))
    	cmd_str+="&{}={}".format(test_img_cmd,walking_1)
        #
    	cmd_str+="&{}={}".format(trigger_mode_cmd,4)   #4=light exposure
    	#cmd_str+="&{}=0".format(serial_origin_cmd)
    	cmd_str+="&{}=8".format(serial_origin_cmd)
    	cmd_str+="&{}={}".format(serial_length_cmd,i)
    	cmd_str+="&{}=0".format(serial_post_scan_cmd)
    	#cmd_str+="&{}={}".format(serial_binning_cmd,binning)
    	cmd_str+="&{}={}".format(serial_binning_cmd,1)
    	#cmd_str+="&{}=0".format(serial_phasing_cmd)
    	cmd_str+="&{}=2".format(serial_phasing_cmd)
    	cmd_str+="&{}=0".format(parallel_origin_cmd)
    	#cmd_str+="&{}={}".format(parallel_length_cmd,int((par_pix+binning-1)/binning))
    	cmd_str+="&{}={}".format(parallel_length_cmd,1032)
    	cmd_str+="&{}=0".format(parallel_post_scan_cmd)
    	#cmd_str+="&{}={}".format(parallel_binning_cmd,binning)
    	cmd_str+="&{}={}".format(parallel_binning_cmd,1)
    	cmd_str+="&{}=0".format(parallel_phasing_cmd)
    	#cmd_str+="&{}=1".format(port_select_cmd)	# Port 0 only
    	cmd_str+="&{}=3".format(port_select_cmd)	# Port 0 only
    	cmd_str+="&{}={}".format(source_cmd,source_camera)

    	print(self.get_url_as_string(target+'command.txt',cmd_str))	# Display the results of the initialization
    	# Collect images as quickly as possible
    	collected_images=0
    	total_read_time=0.0
    	total_read_bytes=0
    	longest_cycle=0
    	startTime=time()
    	what = self.get_url_as_string(target+'command.txt',"{}".format("COOLER 1"))
    	print(what)
    	for image in range(iterations):
    		timeCollected=time()
    		print("Collecting image %u of %u" % (image+1,iterations))
    		data=self.get_url_as_string(target+'command.txt',"{}".format(acquire_cmd))
    		if len(data)<9:
    			break
    		print(data)
    		reading=True
    		while reading:
    			data=self.get_url_as_string(target+'acq.xml')
    			x=data.split("</display><value>")
    			if len(x)<8:
    				break
    			exposure_remaining=int(x[3].split("</value>")[0])
    			readout_percent=int(x[4].split("</value>")[0])
    			result=int(x[7].split("\n")[0].split("</value>")[0])
    			print("exposure_remaining={},readout_percent={},result={}.\n".format(exposure_remaining,readout_percent,result),end='\r')
    			if readout_percent>99:
    				reading=False
    			else:
    				sleep(0.2)
    		timeRequested=time()
    		#data=get_url(target+'image.bin')	# Just the pixels (in network byte order)
    		data=self.get_url(target+'image.fit')	# Just the pixels (in network byte order)
    		timeReceived=time()
    		print("\nRead %u bytes in %.3f seconds" % (len(data),(timeReceived - timeRequested)),end="")
    		if timeReceived>timeRequested:
    			print(" (%.3f MB/s)" % (len(data)/(1000000 * (timeReceived - timeRequested))),end="")
    		print(".")
    		k=timeReceived-timeCollected
    		if k>longest_cycle:
    			longest_cycle=k
    		collected_images+=1
    		total_read_time+=(timeReceived - timeRequested)
    		total_read_bytes+=len(data)
    		print(data[0:1000])
    
            
    		# write to file
            
    		fileout = "/Users/robberto/Box/@Massimo/_Python/SAMOS_GUI_dev/fits_image/newimage.fit"
    		newFile = open(fileout, "wb")
    		newFile.write(data)

 
      		#if kbhit():
    		#	if 27==ord(getch()):
    		#		break
    	print("Collected {} images in {:.3f} seconds.".format(collected_images,time() - startTime))
    	print("Longest image collection cycle was {:.3f} seconds.".format(longest_cycle))
    	print("Read %u bytes in %.3f seconds (%.3f MB/s average)." % (total_read_bytes,total_read_time,(total_read_bytes/(1000000 * total_read_time))))
        
        
    def Cooler(self,OnOff):
    	target=self.IP_Host+":"+str(self.IP_Port)
                    #'128.220.146.254:8900'
    	target='http://'+target+'/'

        #OnOff = '0' : Cooler OFF; OnOff = '1' : Cooler ON
    	Command = "COOLER "+OnOff
    	what = self.get_url_as_string(target+'command.txt',"{}".format(Command))
    	print(what)
    	pass
    
    
    def set_CCD_temp(self,CCD_temp_setpoint):
    	target=self.IP_Host+":"+str(self.IP_Port)
                    #'128.220.146.254:8900'
    	target='http://'+target+'/'
        
    	self.CCD_temp_setpoint = CCD_temp_setpoint
        
    	# Combine the various XML parameter files
    	xml_str=self.get_url_as_string(target+'setup.xml')
    	if len(xml_str)<9:
    		exit()
    	#i,j=self.param_bounds(xml_str)
    	#xml_hdr=xml_str[0:i]
    	#xml_param=xml_str[i:j]
    	#xml_ftr=xml_str[j:len(xml_str)]
# =============================================================================
#     	xml_str=self.get_url_as_string(target+'control.xml')
#     	i,j=self.param_bounds(xml_str)
#     	xml_param+=xml_str[i:j]
#     	xml_str=self.get_url_as_string(target+'factory.xml')
#     	i,j=self.param_bounds(xml_str)
#     	xml_param+=xml_str[i:j]
#     	xml_str=self.get_url_as_string(target+'miscellaneous.xml')
#     	i,j=self.param_bounds(xml_str)
#     	xml_param+=xml_str[i:j]
#     	xml_str=xml_hdr+xml_param+xml_ftr
# =============================================================================
        
    	#print(xml_param)
    	# Extract the parameter information we require from the combined XML DOM
    	with xml.dom.minidom.parseString(xml_str) as dom:
    		dom_list=dom.getElementsByTagName("list")[0]
    		param_list=dom_list.getElementsByTagName("parameter")
    		#par_pix=int(self.xml_parameter_tag(param_list,"Parallel Active Pix.","value"))
    		#ser_pix=int(self.xml_parameter_tag(param_list,"Serial Active Pix.","value"))
    		#source_cmd=self.xml_parameter_tag(param_list,"Server Data Source","post_name")
    		#source_camera=self.xml_parameter_pulldown_value(param_list,"Server Data Source","Camera")
    		#source_server=xml_parameter_pulldown_value(param_list,"Server Data Source","Server")
    		#test_img_cmd=self.xml_parameter_tag(param_list,"Server Test Image Type","post_name")
    		#walking_1=self.xml_parameter_pulldown_value(param_list,"Server Test Image Type","Walking 1")
    		#serial_origin_cmd=self.xml_parameter_tag(param_list,"Serial Origin","post_name")
    		#serial_length_cmd=self.xml_parameter_tag(param_list,"Serial Length","post_name")
    		#serial_post_scan_cmd=self.xml_parameter_tag(param_list,"Serial Post Scan","post_name")
    		#serial_binning_cmd=self.xml_parameter_tag(param_list,"Serial Binning","post_name")
    		#serial_phasing_cmd=self.xml_parameter_tag(param_list,"Serial Phasing","post_name")
    		#parallel_origin_cmd=self.xml_parameter_tag(param_list,"Parallel Origin","post_name")
    		#parallel_length_cmd=self.xml_parameter_tag(param_list,"Parallel Length","post_name")
    		#parallel_post_scan_cmd=self.xml_parameter_tag(param_list,"Parallel Post Scan","post_name")
    		#parallel_binning_cmd=self.xml_parameter_tag(param_list,"Parallel Binning","post_name")
    		#parallel_phasing_cmd=self.xml_parameter_tag(param_list,"Parallel Phasing","post_name")
    		#port_select_cmd=self.xml_parameter_tag(param_list,"Port Select","post_name")
    		#exposure_time_cmd=self.xml_parameter_tag(param_list,"Exposure Time","post_name")
    		#trigger_mode_cmd=self.xml_parameter_tag(param_list,"Trigger Mode","post_name")
    		set_CCD_temp_cmd=self.xml_parameter_tag(param_list,"CCD Temperature Setpoint","post_name")
    	with xml.dom.minidom.parseString(self.get_url_as_string(target+'command.xml')) as dom:
    		dom_list=dom.getElementsByTagName("list")[0]
    		param_list=dom_list.getElementsByTagName("parameter")
    		#acquire_cmd=self.xml_parameter_tag(param_list,"Acquire an image.","post_name")
    		#xml_str=self.xml_parameter_pulldown_value(param_list,"Acquire an image.","Light")
    		#print('\nxml_list\n',xml_str)
    	#acquire_cmd+=" "+xml_str
    	#print('aaa> ',acquire_cmd)
    	# Construct the commands needed to initialize the HTTP Camera Server
    	#i=528#2048	# This is our desired serial size in pixels for this test
    	#binning=int((ser_pix+i-1)/i)
    	cmd_str=""#"{}=1000".format(exposure_time_cmd)
    	#cmd_str="{}=1000".format(exposure_time_cmd)
    	#cmd_str="{}={}".format(exposure_time_cmd,str(self.ExpTime))
    	#cmd_str+="&{}={}".format(test_img_cmd,walking_1)
        #
    	#cmd_str+="&{}={}".format(trigger_mode_cmd,4)   #4=light exposure
    	#cmd_str+="&{}=0".format(serial_origin_cmd)
    	#cmd_str+="&{}=8".format(serial_origin_cmd)
    	#cmd_str+="&{}={}".format(serial_length_cmd,i)
    	#cmd_str+="&{}=0".format(serial_post_scan_cmd)
    	#cmd_str+="&{}={}".format(serial_binning_cmd,binning)
    	#cmd_str+="&{}={}".format(serial_binning_cmd,1)
    	#cmd_str+="&{}=0".format(serial_phasing_cmd)
    	#cmd_str+="&{}=2".format(serial_phasing_cmd)
    	#cmd_str+="&{}=0".format(parallel_origin_cmd)
    	#cmd_str+="&{}={}".format(parallel_length_cmd,int((par_pix+binning-1)/binning))
    	#cmd_str+="&{}={}".format(parallel_length_cmd,1032)
    	#cmd_str+="&{}=0".format(parallel_post_scan_cmd)
    	#cmd_str+="&{}={}".format(parallel_binning_cmd,binning)
    	#cmd_str+="&{}={}".format(parallel_binning_cmd,1)
    	#cmd_str+="&{}=0".format(parallel_phasing_cmd)
    	#cmd_str+="&{}=1".format(port_select_cmd)	# Port 0 only
    	#cmd_str+="&{}=3".format(port_select_cmd)	# Port 0 only
    	#cmd_str+="&{}={}".format(source_cmd,source_camera)
    	cmd_str+="&{}={}".format(set_CCD_temp_cmd,self.CCD_temp_setpoint)

    	print(self.get_url_as_string(target+'command.txt',cmd_str))	# Display the results of the initialization
    	# Collect images as quickly as possible
# =============================================================================
#     	collected_images=0
#     	total_read_time=0.0
#     	total_read_bytes=0
#     	longest_cycle=0
#     	startTime=time()
# #    	what = self.get_url_as_string(target+'command.txt',"{}".format("COOLER 1"))
# #    	print(what)
#     	for image in range(iterations):
#     		timeCollected=time()
# # =============================================================================
# =============================================================================
#     		print("Collecting image %u of %u" % (image+1,iterations))
#     		data=self.get_url_as_string(target+'command.txt',"{}".format(acquire_cmd))
#     		if len(data)<9:
#     			break
#     		print(data)
#     		reading=True
#     		while reading:
#     			data=self.get_url_as_string(target+'acq.xml')
#     			x=data.split("</display><value>")
#     			if len(x)<8:
#     				break
#     			exposure_remaining=int(x[3].split("</value>")[0])
#     			readout_percent=int(x[4].split("</value>")[0])
#     			result=int(x[7].split("\n")[0].split("</value>")[0])
#     			print("exposure_remaining={},readout_percent={},result={}.\n".format(exposure_remaining,readout_percent,result),end='\r')
#     			if readout_percent>99:
#     				reading=False
#     			else:
#     				sleep(0.2)
#     		timeRequested=time()
#     		#data=get_url(target+'image.bin')	# Just the pixels (in network byte order)
#     		data=self.get_url(target+'image.fit')	# Just the pixels (in network byte order)
#     		timeReceived=time()
#     		print("\nRead %u bytes in %.3f seconds" % (len(data),(timeReceived - timeRequested)),end="")
#     		if timeReceived>timeRequested:
#     			print(" (%.3f MB/s)" % (len(data)/(1000000 * (timeReceived - timeRequested))),end="")
#     		print(".")
#     		k=timeReceived-timeCollected
#     		if k>longest_cycle:
#     			longest_cycle=k
#     		collected_images+=1
#     		total_read_time+=(timeReceived - timeRequested)
#     		total_read_bytes+=len(data)
#     		print(data[0:1000])
#     
#             
#     		# write to file
#             
#     		fileout = "/Users/robberto/Box/@Massimo/_Python/SAMOS_GUI_dev/fits_image/newimage.fit"
#     		newFile = open(fileout, "wb")
#     		newFile.write(data)
# 
#  
#       		#if kbhit():
#     		#	if 27==ord(getch()):
#     		#		break
#     	print("Collected {} images in {:.3f} seconds.".format(collected_images,time() - startTime))
#     	print("Longest image collection cycle was {:.3f} seconds.".format(longest_cycle))
#     	print("Read %u bytes in %.3f seconds (%.3f MB/s average)." % (total_read_bytes,total_read_time,(total_read_bytes/(1000000 * total_read_time))))
# 
# =============================================================================


    def status(self):
    	target=self.IP_Host+":"+str(self.IP_Port)
                    #'128.220.146.254:8900'
    	target='http://'+target+'/'
        
    	status = self.get_url_as_string(target+'command.txt',"{}".format("STATUS"))
    	return status

    def expose(self):
    	if 2<=len(sys.argv):
    		target=sys.argv[1]
    	else:
    		target=self.IP_Host+":"+str(self.IP_Port)
                    #'128.220.146.254:8900'
                    #'192.168.0.223'
    	if 3<=len(sys.argv):
    		iterations=sys.argv[2]
    		iterations=int(iterations)
    	else:
    		iterations=1
    	target='http://'+target+'/'
    	print("URI=%s" % target)
    	# Combine the various XML parameter files
    	xml_str=self.get_url_as_string(target+'setup.xml')
    	if len(xml_str)<9:
    		sys.exit()
    	i,j=self.param_bounds(xml_str)
    	xml_hdr=xml_str[0:i]
    	xml_param=xml_str[i:j]
    	xml_ftr=xml_str[j:len(xml_str)]
#    	xml_str=self.get_url_as_string(target+'control.xml')
#    	i,j=self.param_bounds(xml_str)
#    	xml_param+=xml_str[i:j]
#    	xml_str=self.get_url_as_string(target+'factory.xml')
#    	i,j=self.param_bounds(xml_str)
#    	xml_param+=xml_str[i:j]
#    	xml_str=self.get_url_as_string(target+'miscellaneous.xml')
#    	i,j=self.param_bounds(xml_str)
 #   	xml_param+=xml_str[i:j]
    	xml_str=xml_hdr+xml_param+xml_ftr
        
 #   	print(xml_param)
    	# Extract the parameter information we require from the combined XML DOM
    	with xml.dom.minidom.parseString(xml_str) as dom:
    		dom_list=dom.getElementsByTagName("list")[0]
    		param_list=dom_list.getElementsByTagName("parameter")
# =============================================================================
#     		par_pix=int(self.xml_parameter_tag(param_list,"Parallel Active Pix.","value"))
#     		ser_pix=int(self.xml_parameter_tag(param_list,"Serial Active Pix.","value"))
# =============================================================================
    		source_cmd=self.xml_parameter_tag(param_list,"Server Data Source","post_name")
    		source_camera=self.xml_parameter_pulldown_value(param_list,"Server Data Source","Camera")
    		#source_server=xml_parameter_pulldown_value(param_list,"Server Data Source","Server")
    		test_img_cmd=self.xml_parameter_tag(param_list,"Server Test Image Type","post_name")
    		walking_1=self.xml_parameter_pulldown_value(param_list,"Server Test Image Type","Walking 1")
# =============================================================================
#     		serial_origin_cmd=self.xml_parameter_tag(param_list,"Serial Origin","post_name")
#     		serial_length_cmd=self.xml_parameter_tag(param_list,"Serial Length","post_name")
#     		serial_post_scan_cmd=self.xml_parameter_tag(param_list,"Serial Post Scan","post_name")
#     		serial_binning_cmd=self.xml_parameter_tag(param_list,"Serial Binning","post_name")
#     		serial_phasing_cmd=self.xml_parameter_tag(param_list,"Serial Phasing","post_name")
#     		parallel_origin_cmd=self.xml_parameter_tag(param_list,"Parallel Origin","post_name")
#     		parallel_length_cmd=self.xml_parameter_tag(param_list,"Parallel Length","post_name")
#     		parallel_post_scan_cmd=self.xml_parameter_tag(param_list,"Parallel Post Scan","post_name")
#     		parallel_binning_cmd=self.xml_parameter_tag(param_list,"Parallel Binning","post_name")
#     		parallel_phasing_cmd=self.xml_parameter_tag(param_list,"Parallel Phasing","post_name")
#     		port_select_cmd=self.xml_parameter_tag(param_list,"Port Select","post_name")
# =============================================================================
    		exposure_time_cmd=self.xml_parameter_tag(param_list,"Exposure Time","post_name")
    		trigger_mode_cmd=self.xml_parameter_tag(param_list,"Trigger Mode","post_name")
    	with xml.dom.minidom.parseString(self.get_url_as_string(target+'command.xml')) as dom:
    		dom_list=dom.getElementsByTagName("list")[0]
    		param_list=dom_list.getElementsByTagName("parameter")
    		acquire_cmd=self.xml_parameter_tag(param_list,"Acquire an image.","post_name")
    		xml_str=self.xml_parameter_pulldown_value(param_list,"Acquire an image.","Light")
  #  		print('\nxml_list\n',xml_str)
    	acquire_cmd+=" "+xml_str
    	# Construct the commands needed to initialize the HTTP Camera Server
# =============================================================================
#     	i=528#2048	# This is our desired serial size in pixels for this test
#     	binning=int((ser_pix+i-1)/i)
# =============================================================================
    	#cmd_str="{}=1000".format(exposure_time_cmd)
    	cmd_str="{}={}".format(exposure_time_cmd,str(self.ExpTime))
    	cmd_str+="&{}={}".format(test_img_cmd,walking_1)
        #
    	cmd_str+="&{}={}".format(trigger_mode_cmd,self.TriggerMode)   #4=light exposure
# =============================================================================
#     	#cmd_str+="&{}=0".format(serial_origin_cmd)
#     	cmd_str+="&{}=8".format(serial_origin_cmd)
#     	cmd_str+="&{}={}".format(serial_length_cmd,i)
#     	cmd_str+="&{}=0".format(serial_post_scan_cmd)
#     	#cmd_str+="&{}={}".format(serial_binning_cmd,binning)
#     	cmd_str+="&{}={}".format(serial_binning_cmd,1)
#     	#cmd_str+="&{}=0".format(serial_phasing_cmd)
#     	cmd_str+="&{}=2".format(serial_phasing_cmd)
#     	cmd_str+="&{}=0".format(parallel_origin_cmd)
#     	#cmd_str+="&{}={}".format(parallel_length_cmd,int((par_pix+binning-1)/binning))
#     	cmd_str+="&{}={}".format(parallel_length_cmd,1032)
#     	cmd_str+="&{}=0".format(parallel_post_scan_cmd)
#     	#cmd_str+="&{}={}".format(parallel_binning_cmd,binning)
#     	cmd_str+="&{}={}".format(parallel_binning_cmd,1)
#     	cmd_str+="&{}=0".format(parallel_phasing_cmd)
#     	#cmd_str+="&{}=1".format(port_select_cmd)	# Port 0 only
#     	cmd_str+="&{}=3".format(port_select_cmd)	# Port 0 only
#     	cmd_str+="&{}={}".format(source_cmd,source_camera)
# 
# =============================================================================
    	print(self.get_url_as_string(target+'command.txt',cmd_str))	# Display the results of the initialization
    	# Collect images as quickly as possible
    	collected_images=0
    	total_read_time=0.0
    	total_read_bytes=0
    	longest_cycle=0
    	startTime=time()
    	for image in range(iterations):
    		timeCollected=time()
    		print("Collecting image %u of %u" % (image+1,iterations))
    		data=self.get_url_as_string(target+'command.txt',"{}".format(acquire_cmd))
    		if len(data)<9:
    			break
    		print(data)
    		reading=True
    		while reading:
    			data=self.get_url_as_string(target+'acq.xml')
    			x=data.split("</display><value>")
    			if len(x)<8:
    				break
    			exposure_remaining=int(x[3].split("</value>")[0])
    			readout_percent=int(x[4].split("</value>")[0])
    			result=int(x[7].split("\n")[0].split("</value>")[0])
    			print("exposure_remaining={},readout_percent={},result={}.\n".format(exposure_remaining,readout_percent,result),end='\r')
    			if readout_percent>99:
    				reading=False
    			else:
    				sleep(0.2)
    		timeRequested=time()
    		#data=get_url(target+'image.bin')	# Just the pixels (in network byte order)
    		data=self.get_url(target+'image.fit')	# Just the pixels (in network byte order)
    		timeReceived=time()
    		print("\nRead %u bytes in %.3f seconds" % (len(data),(timeReceived - timeRequested)),end="")
    		if timeReceived>timeRequested:
    			print(" (%.3f MB/s)" % (len(data)/(1000000 * (timeReceived - timeRequested))),end="")
    		print(".")
    		k=timeReceived-timeCollected
    		if k>longest_cycle:
    			longest_cycle=k
    		collected_images+=1
    		total_read_time+=(timeReceived - timeRequested)
    		total_read_bytes+=len(data)
    		print(data[0:1000])
    
            
    		# write to file
            
    		fileout = parent_dir + "/fits_image/newimage.fit"
    		newFile = open(fileout, "wb")
    		newFile.write(data)

 
      		#if kbhit():
    		#	if 27==ord(getch()):
    		#		break
    	print("Collected {} images in {:.3f} seconds.".format(collected_images,time() - startTime))
    	print("Longest image collection cycle was {:.3f} seconds.".format(longest_cycle))
    	print("Read %u bytes in %.3f seconds (%.3f MB/s average)." % (total_read_bytes,total_read_time,(total_read_bytes/(1000000 * total_read_time))))
  