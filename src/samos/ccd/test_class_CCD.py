#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  6 18:11:10 2022

@author: robberto
"""

from .Class_CCD_dev import Class_Camera

params = {'Exposure Time':100,'CCD Temperature':2300,'Trigger Mode': 4, 'NofFrames': 1}
        #Trigger Mode = 4: light
        #Trigger Mode = 4: dark

Camera= Class_Camera(dict_params=params)


#Camera.expose()
Camera.expose()

#Camera.dict_params['Exposure Time']=10

#Camera.set_CCD_temp(2030)    #(273-80) * 10

#Status = Camera.status()
#print(Status)
#url_name = 'http://128.220.146.254:8900/'



