#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 23:05:22 2023

@author: robberto

from https://ps1images.stsci.edu/ps1_dr2_api.html
"""

"""Query Pan-STARRS DR2 catalog using MAST API
The new MAST interface to the Pan-STARRS catalog supports queries to both the DR1 and DR2 PS1 catalogs. It also has an associated API, which is used in this script.

This script shows how to query the Pan-STARRS DR2 catalog using the PS1 search API. The examples show how to do a simple cone search, how to manipulate the table of results, and how to get a light curve from the table of detections.

This notebook is available for download.
"""

from astropy.table import Table

import sys
import re
import numpy as np
import matplotlib.pyplot as plt
import json
import requests

try: # Python 3.x
    from urllib.parse import quote as urlencode
    from urllib.request import urlretrieve
except ImportError:  # Python 2.x
    from urllib import pathname2url as urlencode
    from urllib import urlretrieve

try: # Python 3.x
    import http.client as httplib 
except ImportError:  # Python 2.x
    import httplib   

class PS_DR2_Catalog():
    def __init__(self):
        print("in")

    """
    Useful functions
    Execute PS1 searches and resolve names using MAST query.
    """
    def ps1cone(self,ra,dec,radius,table="mean",release="dr1",format="csv",columns=None,
               baseurl="https://catalogs.mast.stsci.edu/api/v0.1/panstarrs", verbose=False,
               **kw):
        """Do a cone search of the PS1 catalog
        
        Parameters
        ----------
        ra (float): (degrees) J2000 Right Ascension
        dec (float): (degrees) J2000 Declination
        radius (float): (degrees) Search radius (<= 0.5 degrees)
        table (string): mean, stack, or detection
        release (string): dr1 or dr2
        format: csv, votable, json
        columns: list of column names to include (None means use defaults)
        baseurl: base URL for the request
        verbose: print info about request
        **kw: other parameters (e.g., 'nDetections.min':2)
        """
        
        data = kw.copy()
        data['ra'] = ra
        data['dec'] = dec
        data['radius'] = radius
        return self.ps1search(table=table,release=release,format=format,columns=columns,
                        baseurl=baseurl, verbose=verbose, **data)
    
    
    def ps1search(self,table="mean",release="dr1",format="csv",columns=None,
               baseurl="https://catalogs.mast.stsci.edu/api/v0.1/panstarrs", verbose=False,
               **kw):
        """Do a general search of the PS1 catalog (possibly without ra/dec/radius)
        
        Parameters
        ----------
        table (string): mean, stack, or detection
        release (string): dr1 or dr2
        format: csv, votable, json
        columns: list of column names to include (None means use defaults)
        baseurl: base URL for the request
        verbose: print info about request
        **kw: other parameters (e.g., 'nDetections.min':2).  Note this is required!
        """
        
        data = kw.copy()
        if not data:
            raise ValueError("You must specify some parameters for search")
        self.checklegal(table,release)
        if format not in ("csv","votable","json"):
            raise ValueError("Bad value for format")
        url = f"{baseurl}/{release}/{table}.{format}"
        if columns:
            # check that column values are legal
            # create a dictionary to speed this up
            dcols = {}
            for col in self.ps1metadata(table,release)['name']:
                dcols[col.lower()] = 1
            badcols = []
            for col in columns:
                if col.lower().strip() not in dcols:
                    badcols.append(col)
            if badcols:
                raise ValueError('Some columns not found in table: {}'.format(', '.join(badcols)))
            # two different ways to specify a list of column values in the API
            # data['columns'] = columns
            data['columns'] = '[{}]'.format(','.join(columns))
    
    # either get or post works
    #    r = requests.post(url, data=data)
        r = requests.get(url, params=data)
    
        if verbose:
            print(r.url)
        r.raise_for_status()
        if format == "json":
            return r.json()
        else:
            return r.text
    
    
    def checklegal(self,table,release):
        """Checks if this combination of table and release is acceptable
        
        Raises a VelueError exception if there is problem
        """
        
        releaselist = ("dr1", "dr2")
        if release not in ("dr1","dr2"):
            raise ValueError("Bad value for release (must be one of {})".format(', '.join(releaselist)))
        if release=="dr1":
            tablelist = ("mean", "stack")
        else:
            tablelist = ("mean", "stack", "detection")
        if table not in tablelist:
            raise ValueError("Bad value for table (for {} must be one of {})".format(release, ", ".join(tablelist)))
    
    
    def ps1metadata(self,table="mean",release="dr1",
               baseurl="https://catalogs.mast.stsci.edu/api/v0.1/panstarrs"):
        """Return metadata for the specified catalog and table
        
        Parameters
        ----------
        table (string): mean, stack, or detection
        release (string): dr1 or dr2
        baseurl: base URL for the request
        
        Returns an astropy table with columns name, type, description
        """
        
        self.checklegal(table,release)
        url = f"{baseurl}/{release}/{table}/metadata"
        r = requests.get(url)
        r.raise_for_status()
        v = r.json()
        # convert to astropy table
        tab = Table(rows=[(x['name'],x['type'],x['description']) for x in v],
                   names=('name','type','description'))
        return tab
    
    
    def mastQuery(self,request):
        """Perform a MAST query.
    
        Parameters
        ----------
        request (dictionary): The MAST request json object
    
        Returns head,content where head is the response HTTP headers, and content is the returned data
        """
        
        server='mast.stsci.edu'
    
        # Grab Python Version 
        version = ".".join(map(str, sys.version_info[:3]))
    
        # Create Http Header Variables
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain",
                   "User-agent":"python-requests/"+version}
    
        # Encoding the request as a json string
        requestString = json.dumps(request)
        requestString = urlencode(requestString)
        
        # opening the https connection
        conn = httplib.HTTPSConnection(server)
    
        # Making the query
        conn.request("POST", "/api/v0/invoke", "request="+requestString, headers)
    
        # Getting the response
        resp = conn.getresponse()
        head = resp.getheaders()
        content = resp.read().decode('utf-8')
    
        # Close the https connection
        conn.close()
    
        return head,content
    
    
    def resolve(self,name):
        """Get the RA and Dec for an object using the MAST name resolver
        
        Parameters
        ----------
        name (str): Name of object
    
        Returns RA, Dec tuple with position"""
    
        resolverRequest = {'service':'Mast.Name.Lookup',
                           'params':{'input':name,
                                     'format':'json'
                                    },
                          }
        headers,resolvedObjectString = self.mastQuery(resolverRequest)
        resolvedObject = json.loads(resolvedObjectString)
        # The resolver returns a variety of information about the resolved object, 
        # however for our purposes all we need are the RA and Dec
        try:
            objRa = resolvedObject['resolvedCoordinate'][0]['ra']
            objDec = resolvedObject['resolvedCoordinate'][0]['decl']
        except IndexError as e:
            raise ValueError("Unknown object '{}'".format(name))
        return (objRa, objDec)

