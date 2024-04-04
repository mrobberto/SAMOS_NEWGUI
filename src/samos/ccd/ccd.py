from copy import deepcopy
from datetime import datetime
import logging
import math
import os
from pathlib import Path
import socket
from time import sleep, time
from urllib.request import Request,urlopen
from urllib.error import URLError,HTTPError
import xml.dom.minidom

from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.utilities import get_fits_dir


class CCD():
    def __init__(self, par, dmd, logger):
        self.PAR = par
        self.DMD = dmd
        self.logger = logger
        self.initialized = False
        self.ccd_on = False
        self.cooler_on = False


    def get_url(self, url_name, post_data=None, as_string=False):
        if post_data is not None:
            post_data = post_data.encode()
        req = Request(url_name, post_data)
        html_reply = b""
        try:
            response = urlopen(req, timeout=7)
            html_reply = response.read()
        except HTTPError as e:
            self.logger.error("The server couldn't fulfill the request. Error code: {}".format(e.code))
        except URLError as e:
            self.logger.error("Failed to reach the server. Reason: {}".format(e.reason))
        except ConnectionAbortedError as e:
            self.logger.error("The server aborted the connection. Error {}".format(e))
        except ConnectionError as e:
            self.logger.error("Connection Error: {}".format(e))
        except ConnectionRefusedError as e:
            self.logger.error("The server refused the connection: {}".format(e))
        except ConnectionResetError as e:
            self.logger.error("The server reset the connection: {}".format(e))
        except socket.timeout:
            self.logger.error("Connection timed out")
        
        if as_string:
            try:
                html_reply = html_reply.decode(response.headers.get_content_charset())
            except Exception as e:
                # Fall back on UTF8
                html_reply = html_reply.decode('utf-8')
        return html_reply


    def xml_parameter_tag(self, param_list, display_name, tag_name):
        for node in param_list:
            if display_name == node.getElementsByTagName("display")[0].childNodes[0].data:
                return node.getElementsByTagName(tag_name)[0].childNodes[0].data
        return None


    def xml_parameter_pulldown_value(self, param_list, display_name, pulldown_name):
        for node in param_list:
            if display_name == node.getElementsByTagName("display")[0].childNodes[0].data:
                pulldown = node.getElementsByTagName("pull_down")
                for element in pulldown:
                    if pulldown_name == element.getElementsByTagName("display")[0].childNodes[0].data:
                        return element.getElementsByTagName("value")[0].childNodes[0].data
        return None


    def param_bounds(self, xml_str):
        i = xml_str.index('<parameter>')
        j = xml_str.index('</list>')
        return i, j


    def convertSIlly(self, fname, outname=None):
        #ConvertSIlly courtesy of C. Loomis
        FITSblock = 2880

        # If no output file given, just prepend "fixed"
        if outname is None:
                fname = Path(fname)
                dd = fname.parent
                outname = Path(fname.parent, 'fixed'+fname.name)

        with open(fname, "rb") as in_f:
                buf = in_f.read()

        # Two fixes:
        # Header cards:
        buf = buf.replace(b'SIMPLE  =                    F', b'SIMPLE  =                    T')
        buf = buf.replace(b'BITPIX  =                  -16', b'BITPIX  =                   16')
        buf = buf.replace(b"INSTRUME= Spectral Instruments, Inc. 850-406 camera  ", 
                          b"INSTRUME= 'Spectral Instruments, Inc. 850-406 camera'")
    
        # Pad to full FITS block:
        blocks = len(buf) / FITSblock
        pad = round((math.ceil(blocks) - blocks) * FITSblock)
        buf = buf + (b'\0' * pad)
    
        with open(outname, "wb+") as out_f:
                out_f.write(buf)


    def prep_exposure(self, file_name, start_fnumber):
        night_dir_basename = get_fits_dir() / file_name
        fnumber = start_fnumber
        self.img_night_dir_list = []
        target = self.PAR.IP_dict["IP_CCD"]

        target_url = 'http://'+target+'/'

        # Combine the various XML parameter files
        xml_str = self.get_url(target+'setup.xml', as_string=True)
        if len(xml_str) < 9:
            self.logger.error("Invalid Reponse: '{}': Too short.".format(xml_str))
            return
        i, j = self.param_bounds(xml_str)
        xml_hdr = xml_str[0:i]
        xml_param = xml_str[i:j]
        xml_ftr = xml_str[j:len(xml_str)]

        xml_str = self.get_url(target+'control.xml', as_string=True)
        i, j = self.param_bounds(xml_str)
        xml_param += xml_str[i:j]
        
        xml_str = self.get_url(target+'factory.xml', as_string=True)
        i, j = self.param_bounds(xml_str)
        xml_param += xml_str[i:j]
        
        xml_str = self.get_url(target+'miscellaneous.xml', as_string=True)
        i, j = self.param_bounds(xml_str)
        xml_param += xml_str[i:j]
        
        xml_str = xml_hdr + xml_param + xml_ftr
        self.logger.info("Full reply: {}".format(xml_str))
        
        # Extract the parameter information we require from the combined XML DOM
        with xml.dom.minidom.parseString(xml_str) as dom:
            dom_list = dom.getElementsByTagName("list")[0]
            param_list = dom_list.getElementsByTagName("parameter")
            par_pix = int(self.xml_parameter_tag(param_list, "Parallel Active Pix.", "value"))
            ser_pix = int(self.xml_parameter_tag(param_list, "Serial Active Pix.", "value"))
            source_cmd = self.xml_parameter_tag(param_list, "Server Data Source", "post_name")
            source_camera = self.xml_parameter_pulldown_value(param_list, "Server Data Source", "Camera")
            test_img_cmd = self.xml_parameter_tag(param_list, "Server Test Image Type", "post_name")
            walking_1 = self.xml_parameter_pulldown_value(param_list, "Server Test Image Type", "Walking 1")
            serial_origin_cmd = self.xml_parameter_tag(param_list, "Serial Origin", "post_name")
            serial_length_cmd = self.xml_parameter_tag(param_list, "Serial Length", "post_name")
            serial_post_scan_cmd = self.xml_parameter_tag(param_list, "Serial Post Scan", "post_name")
            serial_binning_cmd = self.xml_parameter_tag(param_list, "Serial Binning", "post_name")
            serial_phasing_cmd = self.xml_parameter_tag(param_list, "Serial Phasing", "post_name")
            parallel_origin_cmd = self.xml_parameter_tag(param_list, "Parallel Origin", "post_name")
            parallel_length_cmd = self.xml_parameter_tag(param_list, "Parallel Length", "post_name")
            parallel_post_scan_cmd = self.xml_parameter_tag(param_list, "Parallel Post Scan", "post_name")
            parallel_binning_cmd = self.xml_parameter_tag(param_list, "Parallel Binning", "post_name")
            parallel_phasing_cmd = self.xml_parameter_tag(param_list, "Parallel Phasing", "post_name")
            port_select_cmd = self.xml_parameter_tag(param_list, "Port Select", "post_name")
            exposure_time_cmd = self.xml_parameter_tag(param_list, "Exposure Time", "post_name")
            trigger_mode_cmd = self.xml_parameter_tag(param_list, "Trigger Mode", "post_name")

        with xml.dom.minidom.parseString(self.get_url(target+'command.xml', as_string=True)) as dom:
            dom_list = dom.getElementsByTagName("list")[0]
            param_list = dom_list.getElementsByTagName("parameter")
            acquire_cmd = self.xml_parameter_tag(param_list, "Acquire an image.", "post_name")
            #this is the final command, and we distinguish Light vs Dark also here...
            if self.TriggerMode == 4:
                 xml_str = self.xml_parameter_pulldown_value(param_list, "Acquire an image.", "Light")
            else: 
                 xml_str = self.xml_parameter_pulldown_value(param_list, "Acquire an image.", "Dark")
            self.logger.info("Response to command: {}".format(xml_str))
            
        self.acquire_cmd += " {}".format(xml_str)
        # Construct the commands needed to initialize the HTTP Camera Server
        serial_size = 528  # This is our desired serial size in pixels for this test
        binning = (ser_pix + serial_size - 1) // serial_size
        cmd_str = f"{exposure_time_cmd}={self.ExpTime}&{test_img_cmd}={walking_1}&{trigger_mode_cmd}={self.TriggerMode}"
        cmd_str += f"&{serial_origin_cmd}=8&{serial_length_cmd}={serial_size}&{serial_post_scan_cmd}=0&{serial_binning_cmd}=1"
        cmd_str += f"&{serial_phasing_cmd}=2&{parallel_origin_cmd}=0&{parallel_length_cmd}=1032&{parallel_post_scan_cmd}=0"
        cmd_str += f"&{parallel_binning_cmd}=1&{parallel_phasing_cmd}=0&{port_select_cmd}=3&{source_cmd}={source_camera}"
        self.logger.debug("Sending {}".format(cmd_str))
        reply = self.get_url(target+'command.txt', cmd_str, as_string=True)
        self.logger.info("Camera replied {}".format(reply))
        
        reply = self.get_url(target+'command.txt', "COOLER 1", as_string=True)
        self.logger.info("Reply to cooler start command: {}".format(reply))
        return startTime


    def start_exposure(self):
        reply = self.get_url(target+'command.txt',f"{self.acquire_cmd}", as_string=True)
        if len(reply) < 9:
            self.logger.error("Reply '{}' too short: failed to expose camera.".format(reply))
            return
        self.logger.info("Camera responded {}".format(reply))


    def read_exposure(self, parent, callback, params):
        data = self.get_url(target+'acq.xml', as_string=True)
        x = data.split("</display><value>")
        if len(x) < 8:
            self.logger.info("Finished getting data")
            return True
        exposure_remaining = int(x[3].split("</value>")[0])
        readout_percent = int(x[4].split("</value>")[0])
        result = int(x[7].split("\n")[0].split("</value>")[0])
        
        if exposure_remaining >= 0 and params["exptime"] > 0:
            parent.exposure_progress.step()
            expose_perc = ((params["exptime"] - exposure_remaining) / params["exptime"]) * 100
            parent.progress_status.set(expose_perc)
            parent.exposure_progress.update()
            self.logger.info(f"exp remaining={exposure_remaining}, percent={readout_percent}, result={result}")
        elif 0 < readout_percent <= 100:
            if "Exposing" in parent.exposure_status.get():
                parent.exposure_status.set("Reading out detector.")
                parent.progress_status.set(0.)
            parent.exposure_progress.step()
            parent.progress_status.set(readout_percent)
            parent.exposure_progress.update()
        
        if readout_percent > 99:
            return True
        parent.after(200, callback)
        return False


    def store_exposure(self, file_name, fnumber):
        target = self.PAR.IP_dict["IP_CCD"]
        night_dir_basename = get_fits_dir() / file_name
        timeRequested = time()
        data = self.get_url(target + "image.fit")  # Just the pixels (in network byte order)
        timeReceived = time()
        self.logger.info("Read {} bytes in {:.3f} seconds".format(len(data), timeReceived - timeRequested))
        cycle_time = timeReceived - timeCollected
        read_time = (timeReceived - timeRequested)
        read_bytes += len(data)
        
        # write to file
        # 1) the last file is always saved as newimage.fit, and handled by ginga
        self.write_exposure(self.PAR.QL_images / "newimage.fits", data)
        self.write_exposure("{}_{:04n}.fits".format(night_dir_basename, fnumber), data)
        return "{}_{:04n}.fits".format(night_dir_basename, fnumber), cycle_time, read_time, read_bytes


    def finish_exposure(self, collected_images, startTime, longest_cycle, total_read_bytes, total_read_time):
        self.logger.info("Collected {} images in {:.3f} seconds.".format(len(collected_images), time() - startTime))
        for file_name in collected_images:
            self.logger.debug("\t{}".format(file_name))
        self.logger.info("Longest image collection cycle was {:.3f} seconds.".format(longest_cycle))
        self.logger.info(f"Read {total_read_bytes} bytes in {total_read_time:.3f} seconds.")        
    
    
    def write_exposure(self, file_name, data):
        with open(file_name, "wb") as out_file:
            out_file.write(data)
        self.convertSIlly(file_name, file_name)


    EXP_MAPPINGS = {
        "Science": "light",
        "Bias": "bias",
        "Flat": "flat",
        "Dark": "dark",
        "Buffer": "buff"
    }
    
    CCD_TEMP = 2300
    SHUTTER_OPEN = 4
    SHUTTER_CLOSED = 5
