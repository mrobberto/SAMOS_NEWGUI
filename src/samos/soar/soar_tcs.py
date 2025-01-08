# python3
# coding: utf-8

"""
SOAR TCS
This library handles the SOAR TCS communication, translate instructions to the TCS commands and then takes appropriate steps
"""

import time
import json
import logging
from .scl import SCL, SCLError
from astropy.coordinates import Angle
from astropy import units as u

def angle(angle, f="deg", t="deg"):
    if f == "deg" or f == "dms":
        angle = Angle(angle, unit=u.deg)
    elif f == "hms":
        angle = Angle(angle, unit=u.hour)

    if t == "deg":
        return angle.deg
    elif t == "dms":
        return angle.to_string(unit=u.deg, sep=":", precision=3)
    elif t == "hms":
        return angle.to_string(unit=u.hour, sep=":", precision=3)



class SoarTCSError(Exception):
    pass


class SoarTCS:
    """
    SoarTCS
    The SoarTCS object to carry out functions executions and translations
    """

    def __init__(self, host, port, logger=None, websocket=None):
        """
        __init__
        Create a SoarTCS object to carry out functions executions and translations
        Parameters
        ----------
        logger : Logger object
            Logger object to log all the operations
        websocket : Websocket object
            Websocket to communicate with website
        """

        # External Inputs
        self._logger = logger # Logger object
        self._websocket = websocket # Websocket to communicate with website
        self._host = host # TCS host
        self._port = port # TCS port

        # Variables
        if self._logger is None:
            self._logger = logging.getLogger(__name__)
        self.info = {}  # Dictionary with TCS info
        self.lamps = {}  # Dictionary with possible lamps
        self.selected_instrument = None  # Current selected instrument
        self.automatic_mount = False  # Current mount state (automatic/manual)

        # Create a socket using the SOAR communication library
        self._SCL = SCL(self._host, self._port)

        # Get TCS information to populate local variables
        self.infoa()
        self._logger.info(
            json.dumps(self.info)
            .replace(",", "\n")
            .replace("{", "Information received from instrument:\n ")
            .replace("}", "")
            .replace('"', "")
        )

    def is_connected(self):
        """
        is_connected
        Check the current TCS connection status
        Returns
        -------
        bool
            True if connected, False otherwise
        """
        if self._SCL:
            return self._SCL.is_connected()
        else:
            return False

    def send_command(self, command, timeout=1.5):
        """
        send_command
        Send a command to the TCS and return the response in a dictionary format
        Parameters
        ----------
        command : str
            The command to send to the TCS
        timeout : float, optional
            The timeout for the communication, default is 1.5 seconds
        Returns
        -------
        dict
            A dictionary with the following keys:
            - raw_response: The raw response from the TCS
            - response: A list of the response elements that are not key=value pairs
            - The rest of the keys are the response split by "=" and stripped
        """
        res = self._SCL.send_command(command, timeout=timeout)
        self._logger.debug("Tx Command: %s" % (command))
        self._logger.debug("Rx Command: %s" % (res))
        response_dict = {"raw_response": res, "response": []}
        for pair in res.split():
            if "=" in pair:
                try:
                    key, val = pair.split("=")
                    key = key.strip()
                    if key in response_dict:
                        key = "%s[%s]" % (
                            key,
                            sum([1 if k.startswith(key) else 0 for k in response_dict]),
                        )
                    response_dict[key] = val.strip()
                except ValueError as e:
                    self._logger.error(f"Value Error for attempted pair split: {str(e)} [{pair}]")
            else:
                response_dict["response"].append(pair)
        return response_dict

    def send_command_loop(
        self,
        cmd_name,
        parameters,
        timeout=1.5,
        retry=None,
        active_callback=None,
        polling_time=0.5,
    ):
        """
        send_command_loop
        Send a command to the TCS and loop until the command is no longer in "ACTIVE" state
        Parameters
        ----------
        cmd_name : str
            The command name to send to the TCS
        parameters : str
            The parameters to send with the command
        timeout : float, optional
            The timeout for the communication, default is 1.5 seconds
        retry : int, optional
            The maximum number of retries to perform in case of an error, default is None
        active_callback : callable, optional
            The callback to call when the command is active, default is None
        polling_time : float, optional
            The time to wait between polling the command status, default is 0.5 seconds
        Returns
        -------
        dict
            A dictionary with the following keys:
            - raw_response: The raw response from the TCS
            - response: A list of the response elements that are not key=value pairs
            - The rest of the keys are the response split by "=" and stripped
        """
        res = self.send_command(cmd_name + " " + parameters, timeout)
        if res["response"][0] != "ACTIVE":
            return res
        else:
            if active_callback is not None:
                active_callback(res)

        while True:
            try:
                res = self.send_command(cmd_name + " STATUS", timeout)
                if res["response"][0] != "ACTIVE":
                    return res
                else:
                    if active_callback is not None:
                        active_callback(res)
            except SCLError as e:
                if retry is not None:
                    if retry == 0:
                        raise SCLError("Maximum retries reached.  Error: " + str(e))
                    else:
                        retry -= 1
            if polling_time != 0:
                time.sleep(polling_time)

    def way(self):
        """
        WAY = Who Are You?.
        
        Returns
        -------
        str
            The current telescope WAY response.
        """
        try:
            res = self.send_command("WAY")
            return res["raw_response"][len("DONE ") :]
        except SCLError as e:
            raise SoarTCSError("WAY command error - " + str(e))

    def offset(self, target):
        """
        Send an offset command to the telescope.

        Parameters
        ----------
        target : dict
            The target with the offset information.
            Expected format target = { "offset_ra": float, "offset_dec": float }

        Returns
        -------
        str
            The result of the command.

        Raises
        ------
        SoarTCSError
            If the offset is not numeric or if the command fails.
        """
        try:
            ra = ""
            dec = ""
            if type(target) is dict:
                try:
                    float(target["offset_ra"])
                    float(target["offset_dec"])
                except ValueError:
                    raise SoarTCSError(
                        "Offset not numeric, wrong format %s %s"
                        % (target["offset_ra"], target["offset_dec"])
                    )

                if target["offset_ra"] == 0 and target["offset_dec"] == 0:
                    return "OFFSET not needed for offset_ra=0 and offset_dec=0"

                if target["offset_ra"] > 0:
                    ra = "E %.1f" % (
                        100 if target["offset_ra"] > 100 else abs(target["offset_ra"])
                    )
                else:
                    ra = "W %.1f" % (
                        100 if target["offset_ra"] < -100 else abs(target["offset_ra"])
                    )

                if target["offset_dec"] > 0:
                    dec = "N %.1f" % (
                        100 if target["offset_dec"] > 100 else abs(target["offset_dec"])
                    )
                else:
                    dec = "S %.1f" % (
                        100
                        if target["offset_dec"] < -100
                        else abs(target["offset_dec"])
                    )

            else:
                raise SoarTCSError(
                    "OFFSET command error - Dictionary must be provided"
                )

            res = self.send_command_loop("OFFSET", "MOVE %s %s" % (ra, dec))
            if res["response"][0] == "DONE":
                return "OFFSET DONE %s %s" % (ra, dec)
            else:
                raise SoarTCSError("OFFSET command error - %s" % (res["raw_response"]))
        except SCLError as e:
            raise SoarTCSError("OFFSET command error - " + str(e))

    def focus(self, value, move_type="absolute"):
        """
        Send a focus command to the TCS.

        Parameters
        ----------
        value : int
            The value to send to the focus command.
        move_type : str, optional
            The type of move. Defaults to "absolute".

        Returns
        -------
        str
            The result of the command.

        Raises
        ------
        SoarTCSError
            If the command fails or if the move type is invalid.
        """
        try:
            if move_type == "absolute":
                res = self.send_command_loop("FOCUS", "MOVEABS %i" % (value))
            elif move_type == "relative":
                res = self.send_command_loop("FOCUS", "MOVEREL %i" % (value))
            else:
                raise SoarTCSError(
                    "FOCUS command error - Invalid move type %s" % (move_type)
                )

            if res["response"][0] == "DONE":
                return "FOCUS MOVE successfully - %s" % (res["raw_response"])
            else:
                raise SoarTCSError("FOCUS command error - %s" % (res["raw_response"]))
        except SCLError as e:
            raise SoarTCSError("FOCUS move error - " + str(e))

    def clm(self, position):
        """
        Send a CLM (calibration lamp mechanism) command to the TCS.

        Parameters
        ----------
        position : str
            The position of the CLM. Valid values are "IN" and "OUT".

        Returns
        -------
        str
            The result of the command.

        Raises
        ------
        SoarTCSError
            If the command fails or if the position is invalid.
        """
        try:
            position = position.upper()
            if position not in ["IN", "OUT"]:
                raise SoarTCSError("CLM command error - Invalid position %s" % (position))
            # Get current position
            res = self.send_command("CLM STATUS")
            current_position = res["response"][1]
            if current_position == position:
                return "CLM already %s" % (position)
            elif position == "IN":
                self.guider("DISABLE")
            res = self.send_command_loop("CLM", position)
            if res["response"][0] == "DONE":
                return "CLM succesfully moved %s - %s" % (position, res["raw_response"])
            else:
                raise SoarTCSError("CLM command error - %s" % (res["raw_response"]))
        except SCLError as e:
            raise SoarTCSError("CLM command error - " + str(e))

    def guider(self, state):
        """
        Send a GUIDER command to the TCS.

        Parameters
        ----------
        state : str
            The state of the guider. Valid values are "ENABLE", "DISABLE", "PARK", and "CENTER".

        Returns
        -------
        str
            The result of the command.

        Raises
        ------
        SoarTCSError
            If the command fails or if the state is invalid.
        """
        try:
            state = state.upper()
            if state not in ["ENABLE", "DISABLE", "PARK", "CENTER"]:
                raise SoarTCSError("GUIDER command error - Invalid state %s" % (state))
            res = self.send_command_loop("GUIDER", state)
            if res["response"][0] == "DONE":
                return "GUIDER command %s successfully %s" % (
                    state,
                    res["raw_response"],
                )
            else:
                raise SoarTCSError("GUIDER command error - %s" % (res["raw_response"]))
        except SCLError as e:
            raise SoarTCSError("GUIDER command error - " + str(e))

    def whitespot(self, percentage, turn_on=True):
        """
        Send a WHITESPOT command to the TCS.

        Parameters
        ----------
        percentage : int
            The percentage of the white spot to set. Valid values are 0 - 100.
        turn_on : bool, optional
            If True (default), turn the white spot on. If False, turn the white spot off.

        Returns
        -------
        str
            The result of the command.

        Raises
        ------
        SoarTCSError
            If the command fails or if the percentage is invalid.
        """
        try:
            if turn_on:
                res = self.send_command_loop("WHITESPOT", "ON %i" % (percentage))
                if res["response"][0] == "DONE":
                    return "WHITESPOT successfully turned ON at %i- %s" % (
                        percentage,
                        res["raw_response"],
                    )
                else:
                    raise SoarTCSError(
                        "WHITESPOT command error - %s" % (res["raw_response"])
                    )
            else:
                res = self.send_command_loop("WHITESPOT", "OFF")
                if res["response"][0] == "DONE":
                    return "WHITESPOT successfully turned OFF - %s" % (
                        res["raw_response"]
                    )
                else:
                    raise SoarTCSError(
                        "WHITESPOT command error - %s" % (res["raw_response"])
                    )
        except SCLError as e:
            raise SoarTCSError("WHITESPOT command error - " + str(e))

    def get_lamp_number(self, name):
        """
        Get the number of the lamp given its name.

        Parameters
        ----------
        name : str
            The name of the lamp.

        Returns
        -------
        int
            The number of the lamp.

        Raises
        ------
        SoarTCSError
            If the lamp name is not found in the list of valid lamp names.
        """
        try:
            return self.lamps[name]["number"]
        except KeyError:
            raise SoarTCSError(
                "Lamp %s not found in lamp options %s"
                % (name, ", ".join(self.lamps.keys()))
            )

    def lamp(self, lamp, state="ON", percentage=0):
        """
        Turn on or off a lamp.

        Parameters
        ----------
        lamp : str or int
            The name or number of the lamp.
        state : str, optional
            The state of the lamp. One of "ON" or "OFF". Defaults to "ON".
        percentage : float, optional
            The percentage level of the lamp. Defaults to 0.

        Returns
        -------
        str
            The result of the command.

        Raises
        ------
        SoarTCSError
            If the command fails or if the percentage is invalid.
        """
        try:
            state = state.upper()
            if state not in ["ON", "OFF"]:
                raise SoarTCSError("LAMP command error - Invalid state %s" % (state))
            if type(lamp) is str:
                lamp_number = self.get_lamp_number(lamp)
            elif type(lamp) is int:
                lamp_number = lamp
            elif type(lamp) is float:
                lamp_number = int(lamp)
            else:
                raise SoarTCSError(
                    "LAMP command error - Lamp name or lamp number must be provided"
                )

            res = self.send_command("LAMP L%i STATUS" % (lamp_number))

            current_state = res["response"][2]
            if len(res["response"]) > 4:
                current_percentage = float(res["response"][4])
                if percentage is None:
                    raise SoarTCSError(
                        "LAMP command error - Percentage required for lamp %i"
                        % (lamp_number)
                    )
                else:
                    try:
                        percentage = float(percentage)
                    except ValueError:
                        raise SoarTCSError(
                            "LAMP command error - Percentage is not a number for lamp %i"
                            % (lamp_number)
                        )

                if current_state != state or current_percentage != percentage:
                    res = self.send_command_loop(
                        "LAMP L%i" % (lamp_number),
                        "%s %s" % (state, percentage),
                        retry=10,
                    )
                    if res["response"][0] == "DONE":
                        return "LAMP %i successfully turned %s at %s" % (
                            lamp_number,
                            state,
                            percentage,
                        )
                    else:
                        raise SoarTCSError(
                            "LAMP command error - %s" % (res["raw_response"])
                        )
                else:
                    return "LAMP command not needed - Lamp %i already %s at %s" % (
                        lamp_number,
                        state,
                        percentage,
                    )
            else:
                if current_state != state:
                    res = self.send_command_loop(
                        "LAMP L%i" % (lamp_number), state, retry=10
                    )
                    if res["response"][0] == "DONE":
                        return "LAMP %i successfully turned %s" % (lamp_number, state)
                    else:
                        raise SoarTCSError(
                            "LAMP command error - %s" % (res["raw_response"])
                        )
                else:
                    return "LAMP command not needed - Lamp %i already %s" % (
                        lamp_number,
                        state,
                    )

        except SCLError as e:
            raise SoarTCSError("LAMP command error - " + str(e))

    def lamps_turn_on(self, lamps):
        # lamps format (keys as names)
        # {'lamp_0': percentage_0, 'lamp_1': percentage_1, ..., 'lamp_n': percentage_n}
        """
        Turn on a set of lamps.

        Parameters
        ----------
        lamps : dict, tuple or list
            The lamps to turn on. If a dictionary, the keys are the names of the lamps
            and the values are the percentage levels of the lamps. If a tuple or list,
            the values are the names of the lamps.

        Returns
        -------
        bool
            True if any lamps were turned on, False otherwise.

        Raises
        ------
        SoarTCSError
            If the lamps dictionary is not a dictionary, list or tuple, or if a lamp
            name is not found in the list of valid lamp names.
        """
        turned_on = False
        for lamp in self.lamps:
            if lamp in lamps:
                if type(lamps) is dict:
                    res = self.lamp(lamp, state="ON", percentage=lamps[lamp])
                elif type(lamps) is tuple or type(lamps) is list:
                    res = self.lamp(lamp, state="ON")
                else:
                    raise SoarTCSError(
                        "LAMPS OFF command error - Is not a dictionary, list or tuple"
                    )
                if "successfully turned ON" in res:
                    turned_on = True
            else:
                res = self.lamp(lamp, state="OFF")
        return turned_on

    def infoa(self):
        """
        Get information from the TCS.

        The INFOA command is sent to the TCS to retrieve various information
        about the current state of the TCS. This includes the currently selected
        instrument, the status of the mount (automatic or manual), and the state
        of the lamps.

        The information is stored in the `info` attribute of the object, and the
        lamps are stored in the `lamps` attribute.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        SoarTCSError
            If the INFOA command fails.
        """
        try:
            res = self.send_command("INFOA")
            del res["raw_response"]
            del res["response"]
            self.info = dict(res)
            info_out = dict(res)
           
            """
            if "TCS_INSTRUMENT" in self.info:
                if self.selected_instrument != self.info["TCS_INSTRUMENT"]:
                    self.selected_instrument = self.info["TCS_INSTRUMENT"]
                    self._websocket.broadcast(
                        json.dumps({"instrumentTCS": self.selected_instrument})
                    )
            """
            if "TCS_SYN" in self.info:
                automount = True if self.info["TCS_SYN"] == "TRUE" else False
                if self.automatic_mount != automount:
                    self.automatic_mount = automount
                    if self._websocket is not None:
                        self._websocket.broadcast(
                            json.dumps({"syncedTCS": self.automatic_mount})
                        )

            self.lamps = {}
            tags = [k for k in self.info.keys() if k.startswith("TAG_")]
            for tag in tags:
                key = self.info[tag]
                if key in self.lamps:
                    continue
                self.lamps[key] = {
                    "number": int(tag[len("TAG_") :]),
                    "state": self.info["LAMP_%i" % (int(tag[len("TAG_") :]))],
                }
            return info_out
        except SCLError as e:
            raise SoarTCSError("INFOA command error - " + str(e))

    def rotator(self, state):
        """
        Set the rotator state.

        Parameters
        ----------
        state : str
            The desired state of the rotator. Valid values are "TRACK_OFF" and "TRACK_ON".

        Returns
        -------
        str
            A string indicating the success of the command. If the command is not needed
            (i.e. the rotator is already in the desired state), a success message is returned.
            If the command is needed, a success message is returned if the command is
            successfully executed. If the command fails, an error message is returned.

        Raises
        ------
        SoarTCSError
            If the command fails.
        """
        try:
            state = state.upper()
            if state not in ["TRACK_OFF", "TRACK_ON"]:
                raise SoarTCSError("ROTATOR command error - Invalid state %s" % (state))
            res = self.send_command("ROTATOR STATUS")
            if res["response"][0] == "DONE":
                if res["response"][1] != state:
                    res = self.send_command_loop("ROTATOR", state)
                    if res["response"][0] == "DONE":
                        return (
                            "ROTATOR command succesfully done - Rotator set to %s"
                            % (state)
                        )
                    else:
                        raise SoarTCSError(
                            "ROTATOR command error - %s" % (res["raw_response"])
                        )
                else:
                    return "ROTATOR command not needed - Rotator already set to %s" % (
                        state
                    )
            else:
                raise SoarTCSError("ROTATOR command error - %s" % (res["raw_response"]))
        except SCLError as e:
            raise SoarTCSError("ROTATOR command error - " + str(e))

    def ipa(self, angle):
        """
        Sets the Instrument Position Angle (IPA) to the given angle.

        Parameters
        ----------
        angle : float
            The IPA angle to set in degrees.

        Returns
        -------
        str
            A string indicating the success of the command.

        Raises
        ------
        SoarTCSError
            If the command fails.
        """
        try:
            angle = float(angle)
            res = self.send_command_loop("IPA", "MOVE %s" % (angle))
            if res["response"][0] == "DONE":
                return "IPA successfully set to %s degrees" % (angle)
            else:
                raise SoarTCSError("IPA command error - %s" % (res["raw_response"]))
        except ValueError:
            raise SoarTCSError("IPA command error - Angle is not a number")

    def instrument(self, instrument):
        """
        Changes the active instrument in the TCS.

        Parameters
        ----------
        instrument : str
            The name of the instrument to set.

        Returns
        -------
        str
            A string indicating the success of the command.

        Raises
        ------
        SoarTCSError
            If the command fails.
        """
        try:
            res = self.send_command_loop("INSTRUMENT", "MOVE %s" % (instrument))
            if res["response"][0] == "DONE":
                self.selected_instrument = self.info["TCS_INSTRUMENT"]
                if self._websocket is not None:
                    self._websocket.broadcast(
                        json.dumps({"instrumentTCS": self.selected_instrument})
                    )
                return "Instrument %s successfully set" % (instrument)
            else:
                raise SoarTCSError("INSTRUMENT command error - %s" % (res["raw_response"]))
        except SCLError as e:
            raise SoarTCSError("INSTRUMENT command error - " + str(e))

    def target_move(self, target, original_target=True):
        """
        Move the telescope to the given target, splits the slew in multiple steps if necessary.

        Parameters
        ----------
        target : dict
            A dictionary containing the target's RA, Dec, epoch, RA rate and Dec rate.
            Expected format target = { "ra": float, "dec": float, "epoch": float, "ra_rate": float, "dec_rate": float }
        original_target : bool
            If True, the original target is returned if the command is successful.

        Returns
        -------
        dict or None
            If original_target is True, the original target is returned if the command is successful.
            If original_target is False, None is returned.

        Raises
        ------
        SoarTCSError
            If the command fails.
        """
        try:
            res = self.send_command(
                "TARGET CHECK RA=%s DEC=%s EPOCH=%s"
                % (
                    angle(target["ra"], f="deg", t="hms"),
                    angle(target["dec"], f="deg", t="dms"),
                    target["epoch"],
                )
            )
            if res["response"][0] == "DONE":
                res = self.send_command_loop(
                    "TARGET",
                    "MOVE RA=%s DEC=%s EPOCH=%s DRACOSD=%s DDEC=%s"
                    % (
                        angle(target["ra"], f="deg", t="hms"),
                        angle(target["dec"], f="deg", t="dms"),
                        target["epoch"],
                        target["ra_rate"],
                        target["dec_rate"],
                    ),
                )
                if res["response"][0] == "DONE":
                    return original_target
                else:
                    raise SoarTCSError("TARGET command error - %s" % (res["raw_response"]))
            elif res["response"][0] == "WARNING":
                mnt = self.get_mount_position()  # Update mount position
                middle_ra = (angle(mnt["ra"], f="hms", t="deg") + target["ra"]) / 2
                middle_dec = (angle(mnt["dec"], f="dms", t="deg") + target["dec"]) / 2
                self.target_move(
                    {
                        "ra": middle_ra,
                        "dec": middle_dec,
                        "epoch": target["epoch"],
                        "ra_rate": target["ra_rate"],
                        "dec_rate": target["dec_rate"],
                    },
                    original_target=False,
                )
            else:
                raise SoarTCSError("TARGET command error - %s" % (res["raw_response"]))
        except SCLError as e:
            raise SoarTCSError("TARGET command error - " + str(e))

    def target(self, target):
        """
        Move telescope to target.

        Parameters
        ----------
        target : Target
            Target to move to.

        Returns
        -------
        str
            String describing the outcome of the slew.
        """
        target_done = False
        while not target_done:
            target_done = self.target_move(target)
        return 'Telescope moved to target "%s" - RA %s - DEC %s' % (
            target.name,
            target.ra.deg,
            target.dec.deg,
        )

    def get_mount_position(self):
        """
        Get the current mount position of the telescope.

        Returns
        -------
        dict
            A dictionary containing the current RA and DEC of the mount.
            Example: {"ra": float, "dec": float}

        """
        self.infoa()
        return {"ra": self.info["MOUNT_RA"], "dec": self.info["MOUNT_DEC"]}

    def adc(self, percentage, park=False):
        """
        Set the ADC to the given percentage.

        Parameters
        ----------
        percentage : int or str
            The percentage to set the ADC to. Must be between 0 and 100.
        park : bool, optional
            If True, park the ADC.

        Returns
        -------
        str
            A string describing the outcome of the ADC move.

        Raises
        ------
        SoarTCSError
            If the command fails or if the percentage is invalid.
        """
        try:
            try:
                percentage = int(percentage)
            except ValueError:
                raise SoarTCSError("ADC command error - ADC percentage not numeric")
            if park:
                res = self.send_command_loop("ADC", "PARK")
                if res["response"][0] == "DONE":
                    return "ADC PARK successfully"
                else:
                    raise SoarTCSError("ADC command error - %s" % (res["raw_response"]))
            else:
                if 0 <= percentage <= 100:
                    res = self.send_command_loop("ADC", "IN")
                    if res["response"][0] == "DONE":
                        res = self.send_command_loop("ADC", "MOVE %i" % (percentage))
                        if res["response"][0] == "DONE":
                            return "ADC set successfully IN at %i" % (percentage)
                        else:
                            raise SoarTCSError(
                                "ADC command error - %s" % (res["raw_response"])
                            )
                    else:
                        raise SoarTCSError("ADC command error - %s" % (res["raw_response"]))
                else:
                    raise SoarTCSError(
                        "ADC command error - Percentage should be greather than or equal 0"
                    )
        except SCLError as e:
            raise SoarTCSError("WHITESPOT command error - " + str(e))
