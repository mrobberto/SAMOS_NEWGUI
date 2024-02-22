#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  4 14:44:44 2022

@author: robberto
"""

""" KBHIT-test.py
    Shlomo Solomon    
    program to demonstrate the use of kbhit and getch in LINUX """
    
import KBHIT
kbd = KBHIT.KBHit()  # define a keyboard object


def get_input():
    """ use kbhit and getch to get keyboard input """
    key_code = 0
    key_char = None
    if kbd.kbhit():    
        print("hit"),
        key_char = kbd.getch()
        key_code = ord(key_char)
        
        if key_code == KBHIT.ENTER: 
            print("ENTER")
        elif key_code == KBHIT.TAB: 
            print("TAB") 
        elif key_code == KBHIT.BACKSPACE: 
            print("BACKSPACE") 
        elif key_code == KBHIT.ESC: 
            print("ESCAPE") 
        else:
     	    print(key_char, "code=", key_code)
    return key_code, key_char


def main():
    """ main runs until Escape is hit """
    print("Starting test program - waiting for input")
    print("Hit ESC to end the test")
    key_code = 0
    while key_code != KBHIT.ESC:
        key_code, key_char = get_input()
    print("End of test")


if __name__ == "__main__":
    main()
# =============================================================================
# """
# KBHIT.py
# A Python class to implement kbhit() and getch()
#   adapted by Shlomo Solomon from http://home.wlu.edu/~levys/software/kbhit.py
#   NOTES- This version has been tested on LINUX, but should work on Windows too
#        - the original code also had getarrow() which I deleted in this version
#        - works with ASCII chars, ENTER, ESC, BACKSPACE - NOT with special keys
#        - Does not work with IDLE.
# 
# 
# >>>>> 2 ways to use in LINUX - the 2nd one is better!!
# >>>>>>> 11111 >>>>>>>>>>>>>
# from KBHIT import KBHit
# kbd = KBHit()
# 
# Then use as follows:
#     if kbd.kbhit():    
#         print kbd.getch()
# 
# optionally - add the following constants:
# ENTER = 10
# ESC = 27
# BACKSPACE = 127
# TAB = 9
# >>>>>>>>>>>>>>>>>>>
# 
# 
# >>>>>>> 22222 >>>>>>>>>>>>>
# import KBHIT
# kbd = KBHIT.KBHit()
# 
# Then use as follows:
#     if kbd.kbhit():    
#         print kbd.getch()
# 
# the constants mentioned in the first method will be available as:
# KBHIT.ENTER, etc
# >>>>>>>>>>>>>>>>>>>
# =============================================================================
