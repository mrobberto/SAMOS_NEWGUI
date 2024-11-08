#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 20 21:47:46 2024

@author: robberto, york
"""

from contextlib import contextmanager
from datetime import datetime
from functools import wraps
import logging
from pathlib import Path
import sqlite3 
import yaml


# @contextmanager
# def samos_db(db_file):
#     conn = sqlite3.connect(db_file)
#     try:
#         cur = conn.cursor()
#         yield cur
#     except Exception as e:
#         print(f"ERROR in database operations: {e}")
#         # do something with exception
#         conn.rollback()
#         raise e
#     else:
#         conn.commit()
#     finally:
#         conn.close()


def with_db_update(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        try:
            with open(self.db_path, "wt") as out_file:
                yaml.dump(self.db_dict, out_file, default_flow_style=False)
        except Exception as e:
            self.logger.error(f"Unable to write to database {self.db_path}")
            self.logger.error(f"Error was {e}")
        return result
    return wrapper

class StorageDatabase:
    def __init__(self, db_file="Settings.yaml", logger=None):
        if logger is None:
            self.logger = logging.getLogger('samos')
        else:
            self.logger = logger
        self.db_path = Path(db_file)
        if not self.db_path.is_file():
            self.logger.info(f"Creating new database at {self.db_path}")
        self.db_dict = self._load_db()
        self.callbacks = {}
    
    def get_all(self):
        self.logger.debug(f"SAMOS Database {self.db_path}")
        out_str = f"SAMOS2 Database at {self.db_path}:\n"
        for key in self.db_dict:
            out_str += f"{key}: {self.db_dict[key]}"
        return out_str

    def has_parameter(self, parameter):
        return (parameter in self.db_dict)
        
    def get_value(self, parameter, default="", add_missing=False):
        self.logger.debug(f"Database: Extracting the value of: {parameter}")
        if parameter in self.db_dict:
            return self.db_dict[parameter][0]
        self.logger.error(f"ERROR: Database: Parameter {parameter} not in database")
        if add_missing:
            self.update_value(parameter, default)
        return default

    @with_db_update
    def update_value(self, parameter, value):
        self.logger.debug(f"Database: Setting {parameter} to {value}")
        update_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        updated = False
        if parameter not in self.db_dict:
            self.logger.info(f"Database: {parameter} not in database. Inserting {value}.")
            self.db_dict[parameter] = [value, update_time, None]
            updated = True
        else:
            previous_value = self.get_value(parameter)
            if value != previous_value:
                self.logger.info(f"Database: doing update of {parameter} to {value}")
                self.db_dict[parameter] = [value, update_time, previous_value]
                updated = True
        if updated and (parameter in self.callbacks):
            for callback in self.callbacks[parameter]:
                callback()
        return updated

    @with_db_update
    def delete_parameter(self, parameter):
        self.logger.debug(f"Database: Deleting {parameter}")
        if parameter in self.db_dict:
            del self.db_dict[parameter]

    def undo(self, parameter):
        self.logger.debug(f"Database: Restoring {parameter} to previous value")
        if parameter not in self.db_dict:
            self.logger.error(f"Database: Parameter {parameter} not in database! Can't revert.")
            return
        elif self.db_dict[parameter][2] is None:
            self.logger.warning(f"Database: Parameter {parameter} has no previous value. Aborting.")
            return
        self.update_value(parameter, self.db_dict[parameter][2])

    def register_callback(self, parameter, callback):
        if parameter not in self.callbacks:
            self.callbacks[parameter] = []
        self.callbacks[parameter].append(callback)

    def _load_db(self):
        if not self.db_path.is_file():
            # No database file
            self.logger.error("Database: Empty Database")
            return {}
        try:
            with open(self.db_path) as in_file:
                db_dict = yaml.safe_load(in_file)
                if db_dict is None:
                    db_dict = {}
                return db_dict
        except Exception as e:
            self.logger.error(f"Unable to load database {self.db_path}")
            self.logger.error(f"Error was {e}")
            return {}
    
    @property
    def _default_db(self):
        default_values = {
            "Observer": ["Massimo Robberto", "2024:10:20", None],
            "Telescope": ["SOAR", "2024:10:20", None]
        }
        return default_values


# class StorageDatabase:
#     def __init__(self, db_file="SAMOS2.db", logger=None):
#         if logger is None:
#             self.logger = logging.getLogger('samos')
#         else:
#             self.logger = logger
#         db_path = Path(db_file)
#         if not db_path.is_file():
#             self.logger.info(f"Creating new database at {db_path}")
#             self._create_db(db_path)
#         self.logger.info(f"Connecting to database at {db_path}")
#         self.db_path = db_path
#     
#     def get_all(self):
#         self.logger.debug("Returning full database")
#         with samos_db(self.db_path) as cursor:
#             cursor.execute("SELECT * FROM SAMOS2")
#             output = cursor.fetchall()
#         out_str = f"SAMOS2 Database at {self.db_path}:\n"
#         for row in output:
#             out_str += f"{row}\n"
#         return out_str
# 
#     def has_parameter(self, parameter):
#         if self.get_value(parameter) == "":
#             return False
#         return True
#         
#     def get_value(self, parameter, default=""):
#         self.logger.debug(f"Extracting the value of: {parameter}")
#         with samos_db(self.db_path) as cursor:
#             cursor.execute("SELECT * FROM SAMOS2 WHERE Parameter = ?", (parameter,))
#             output = cursor.fetchone()
#         if output is not None and len(output) > 1:
#             self.logger.debug(f"Returning {output[1]}")
#             return output[1]
#         self.logger.error(f"ERROR: Parameter {parameter} not in database")
#         return default
# 
#     def update_value(self, parameter, value):
#         self.logger.info(f"Setting {parameter} to {value}")
#         update_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
#         previous_value = self.get_value(parameter)
#         with samos_db(self.db_path) as cursor:
#             if previous_value == "":
#                 self.logger.info(f"{parameter} not in database. Inserting {value}.")
#                 cursor.execute("INSERT INTO SAMOS2 VALUES (?, ?, ?, ?)", (parameter, value, update_time, "N/A"))
#             else:
#                 cursor.execute("UPDATE SAMOS2 SET Previous = ? WHERE Parameter = ?", (previous_value, parameter))
#                 cursor.execute("UPDATE SAMOS2 SET Date = ? WHERE Parameter = ?", (update_time, parameter))
#                 cursor.execute("UPDATE SAMOS2 SET Value = ? WHERE Parameter = ?", (value, parameter))
#         result = self.get_value(parameter)
#         self.logger.info(f"{parameter} is now {result}")
# 
#     def delete_parameter(self, parameter):
#         self.logger.debug(f"Deleting {parameter}")
#         with samos_db(self.db_path) as cursor:
#             cursor.execute("DELETE FROM SAMOS2 WHERE Parameter = ?", (parameter,))
# 
#     def undo(self, parameter):
#         self.logger.debug(f"Restoring {parameter} to previous value")
#         with samos_db(self.db_path) as cursor:
#             cursor.execute("SELECT * FROM SAMOS2 WHERE Parameter = ?", (parameter,))
#             output = cursor.fetchone()
#         if output is None:
#             print(f"Parameter {parameter} not in database")
#             return
#         if (output[3] is None) or (output[3] == ""):
#             print(f"Parameter {parameter} has no previous value. Aborting.")
#             return
#         self.update_DB(parameter, output[3])
# 
#     def _create_db(self, db_path):
#         """
#         Create a SAMOS2 database table in an SQLITE database at the given path.
#         """
#         with samos_db(db_path) as cursor:
#             cursor.execute("""CREATE TABLE IF NOT EXISTS SAMOS2 (
#                 Parameter varchar(255),
#                 Value,
#                 Date varchar(255),
#                 Previous
#             )""")
#             cursor.execute("""INSERT INTO SAMOS2 VALUES (
#                 "Observer", "Massimo Robberto", "2024-10-20", ""
#             )""")
#             cursor.execute("""INSERT INTO SAMOS2 VALUES (
#                 "Telescope", "SOAR", "2024-10-20", ""
#             )""")
