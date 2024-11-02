"""
SAMOS Guide Star Query Frame Interface
"""
import tkinter as tk
import ttkbootstrap as ttk
from samos.astrometry.guide_stars import GenericGuideStar, PanSTARRSGuideStar, SDSSGuideStar, SkyMapperGuideStar
from samos.utilities.constants import *


class GSQueryFrame(ttk.LabelFrame):
    def __init__(self, parent, ra_var, dec_var, query_callback, logger, **kw):
        super().__init__(parent, text="Query Image Server", **kw)
        self.ra_var = ra_var
        self.dec_var = dec_var
        self.query_callback = query_callback
        self.logger = logger

        # Guide Star Survey Classes
        self.catalogs = {
            "panstarrs": PanSTARRSGuideStar,
            "skymapper": SkyMapperGuideStar,
            "sdss": SDSSGuideStar,
#            "other": GenericGuideStar
        }

        # UI
        ttk.Label(self, text="Survey").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.survey_selected =  self.make_db_var(tk.StringVar, "gs_survey_selected", "SkyMapper")
        ttk.OptionMenu(self, self.survey_selected, None, *list(self.SURVEY_MAP.keys())).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.survey_filter = self.make_db_var(tk.StringVar, "gs_survey_filter", "i")
        ttk.Label(self, text="Filter:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(self, textvariable=self.survey_filter).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        ttk.Button(self, text="Run Query", command=self.run_query).grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL)


    def run_query(self):
        # Find Selected survey
        selected_survey = self.survey_selected.get()
        survey_key = self.SURVEY_MAP[selected_survey]
        ra = self.ra_var.get()
        dec = self.dec_var.get()
        band = self.survey_filter.get()

        # Create catalog interface, and query it.        
        try:
            self.logger.info("Creating Catalog Object")
            self.catalog = self.catalogs[survey_key](ra, dec, band, self.logger)
            self.logger.info("Running Query")
            self.catalog.run_query()
            self.logger.info("Finished query")
            self.query_callback(self.catalog)
        except Exception as e:
            self.logger.error("Failed to retrieve data from {} survey".format(selected_survey))
            self.logger.error("Reported error was: {}".format(e))


    SURVEY_MAP = {
        "SkyMapper": "skymapper",
        "SDSS": "sdss",
        "PanSTARRS/DR1": "panstarrs", 
#         "DSS": "other", 
#         "DSS2/red": "other", 
#         "CDS/P/AKARI/FIS/N160": "other", 
#         "2MASS/J": "other", 
#         "GALEX": "other", 
#         "AllWISE/W3": "other"
    }
