"""
PanSTARRS interface for the guide star module.
"""
from astropy.io import ascii, fits
from astropy.table import Table
import numpy as np
from pathlib import Path

from samos.utilities import get_temporary_dir

from .base import GuideStar


class PanSTARRSGuideStar(GuideStar):
    def __init__(self, ra, dec, band, logger):
        super().__init__(ra, dec, band, "panstarrs", logger)


    def run_query(self):
        """
        Create URLs based on co-ordinates and bands, then retrieve image and catalog data.
        """
        image_urls = self.build_image_urls()
        self.fits_image = fits.open(image_urls[0])
        self.star_table = self.get_panstarrs_table()        


    def get_source_table(self):
        """
        Query ps1filenames.py service to get a list of images
        
        Returns
        -------
        table : astropy.table.Table
            Table containing search results
        """
        base_url = "https://ps1images.stsci.edu/cgi-bin/ps1filenames.py"
        query_url = f"{base_url}?ra={self.ra}&dec={self.dec}&filters={self.band}"
        return Table.read(url, format="ascii")


    def build_image_urls(self, size=240):
        """
        Get URL for FITS images in an image table returned from `self.get_source_table()`

        Parameters
        ----------
        size : int
            Extracted image size in pixels (at 0.25 arcseconds/pixel)
        
        Returns
        -------
        url_results : list
            List of strings containing image retrieval URLs
        """
        source_table = self.get_source_table()
        base_url = "https://ps1images.stsci.edu/cgi-bin/fitscut.cgira={self.ra}&dec={self.dec}&size={size}&format=fits"
        urls = [f"{base_url}&red={file_name}" for file_name in source_table['filename']]
        return urls


    def get_panstarrs_table(self):
        """
        Use the PanSTARRS catalog query class to do a cone search on our RA and dec, and
        give us a source table.
        """
        column_names = {
            f"{self.band}MeanPSFMag": "star_mag",
            "raMean": "ra",
            "decMean": "dec"
        }
        radius = (212.0 * u.arcsec).to(u.deg).value
        constraints = {'nDetections.gt': 1}
        columns = ["objID", "raMean", "decMean", "nDetections", f"n{self.band}", f"{self.band}MeanPSFMag"]
        results = self.ps_cone(radius, release="dr2", columns=columns, verbose=True, **constraints)
        tab = ascii.read(results)
        mag_col = f"{self.band}MeanPSFMag"
        if mag_col in tab:
            tab[mag_col].format = ".4f"
            tab[mag_col][tab[mag_col] == -999.0] = np.nan
        tab["id"] = ["{}".format(x) for x in tab["objID"]]
        return tab.rename(columns=column_names)


    def ps_cone(self, radius, **kwargs):
        """
        Do a cone search of the PS1 catalog. In addition to the parameters listed below,
        see the astroquery documentation at <https://astroquery.readthedocs.io/en/latest/> 
        for additional parameters and options.
        
        Parameters
        ----------
        ra : float
            J2000 right ascension
        dec : float
            J2000 declination
        radius : float, <= 0.5 degrees
            Search radius in degrees
        
        Optional Parameters
        -------------------
        table : string, default 'mean', options 'mean', 'stack', 'detection'
            ***** what does it indicate?
        release: string, default 'dr1', options 'dr1', 'dr2'
            Which Panstarrs data release to use
        format : string, default 'csv', options 'csv', 'votable', 'json'
            Format in which to return the search results
        columns : list, default None
            List of columns to include in the results. None returns the default columns.
        baseurl : string, default "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs"
            URL to use to make the request
        verbose : bool, default False
            Whether to print out additional information about the request and retrieval
        """
        
        kwargs['ra'] = self.ra
        kwargs['dec'] = self.dec
        kwargs['radius'] = radius
        return self.ps_search(**kwargs)
    
    
    def ps_search(self, **kwargs):
        """
        Do a general search of the PS1 catalog (possibly without ra/dec/radius). In 
        addition to the parameters listed below, see the astroquery documentation at 
        <https://astroquery.readthedocs.io/en/latest/> for additional parameters and 
        options.
        
        Parameters
        ----------
        table : string, default 'mean', options 'mean', 'stack', 'detection'
            ***** what does it indicate?
        release: string, default 'dr1', options 'dr1', 'dr2'
            Which Panstarrs data release to use
        format : string, default 'csv', options 'csv', 'votable', 'json'
            Format in which to return the search results
        columns : list, default None
            List of columns to include in the results. None returns the default columns.
        baseurl : string, default "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs"
            URL to use to make the request
        verbose : bool, default False
            Whether to print out additional information about the request and retrieval
        """
        
        kwargs['table'] = kwargs.get('table', 'mean')
        kwargs['release'] = kwargs.get('release', 'dr1')
        kwargs['format'] = kwargs.get('format', 'csv')
        kwargs['columns'] = kwargs.get('columns', None)
        kwargs['verbose'] = kwargs.get('verbose', False)
        
        self.check_legal(table, release)
        if kwargs['columns'] is not None:
            valid_list = [name.lower() for name in self.ps_metadata(table, release)['name']]
            badcols = []
        
            for col in kwargs['columns']:
                if col.lower().strip() not in valid_list:
                    badcols.append(col)
            
            if len(badcols) > 0:
                raise ValueError("Columns {} not available in Panstarrs data table".format(badcols))
        
        url = f"{self.BASE_URL}/{kwargs['release']}/{kwargs['table']}.{kwargs['format']}"
        r = requests.get(url, params=kwargs)
    
        if kwargs['verbose']:
            print(r.url)
        r.raise_for_status()
        if kwargs['format'] == "json":
            return r.json()
        return r.text
    
    
    def check_legal(self, table, release):
        """
        Checks if this combination of table and release is acceptable
        
        Raises a VelueError exception if there is problem
        """
        
        release_list = ("dr1", "dr2")
        if release not in release_list:
            raise ValueError("Bad value for release (must be one of {})".format(release_list))
        if release=="dr1":
            tablelist = ("mean", "stack")
        else:
            tablelist = ("mean", "stack", "detection")
        if table not in tablelist:
            raise ValueError("Bad value for table (for {} must be one of {})".format(release, table_list))


    def ps_metadata(self, **kwargs):
        """
        Return metadata for the specified catalog and table
        
        Parameters
        ----------
        table : string, default 'mean', options 'mean', 'stack', 'detection'
            ***** what does it indicate?
        release: string, default 'dr1', options 'dr1', 'dr2'
            Which Panstarrs data release to use
        baseurl : string, default "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs"
            URL to use to make the request
        
        Returns an astropy table with columns name, type, description
        """
        table = kwargs.get('table', 'mean')
        release = kwargs.get('release', 'dr1')
        baseurl = kwargs.get('baseurl', self.BASE_URL)
        
        self.check_legal(table,release)
        url = f"{baseurl}/{release}/{table}/metadata"
        r = requests.get(url)
        r.raise_for_status()
        # convert to astropy table
        tab = Table(rows=[(x['name'],x['type'],x['description']) for x in r.json()],
                   names=('name','type','description'))
        return tab
    
    
    def mast_query(self, request):
        """
        Perform a MAST query.
    
        Parameters
        ----------
        request : dict
            The MAST request JSON object
        
        Returns
        -------
        head : object
            HTTP headers
        content : object
            Result data
        """
        
        server='mast.stsci.edu'
    
        # Grab Python Version 
        version = ".".join(map(str, sys.version_info[:3]))
    
        # Create Http Header Variables
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain",
                   "User-agent":"python-requests/"+version}
    
        # Encoding the request as a json string
        request_string = json.dumps(request)
        request_string = urlencode(request_string)
        
        # opening the https connection
        conn = httplib.HTTPSConnection(server)
    
        # Making the query
        conn.request("POST", "/api/v0/invoke", "request="+request_string, headers)
    
        # Getting the response
        resp = conn.getresponse()
        head = resp.getheaders()
        content = resp.read().decode('utf-8')
    
        # Close the https connection
        conn.close()
    
        return head, content
    
    
    def resolve(self, name):
        """
        Get the RA and Dec for an object using the MAST name resolver
        
        Parameters
        ----------
        name : str
            Name of object
        
        Returns
        -------
        ra : float
            Object RA
        dec : float
            Object DEC
        """
    
        resolver_request = {
            'service': 'Mast.Name.Lookup',
            'params': {'input': name, 'format': 'json'}
        }
        headers, resolved_object_string = self.mast_query(resolver_request)
        resolved_object = json.loads(resolved_object_string)
        
        # The resolver returns a variety of information about the resolved object, 
        # however for our purposes all we need are the RA and Dec
        try:
            obj_ra = resolved_object['resolvedCoordinate'][0]['ra']
            obj_dec = resolved_object['resolvedCoordinate'][0]['decl']
        except IndexError as e:
            raise ValueError("Unknown object '{}'".format(name))

        return (obj_ra, obj_dec)


    VALID_BANDS = ['g', 'r', 'i', 'z', 'y']
    BASE_URL = "https://catalogs.mast.stsci.edu/api/v0.1/panstarrs"

