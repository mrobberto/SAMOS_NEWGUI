"""
This module defines a `fake_instrument()` function that will be spawned by the
multiprocessing library if contacting the real instrument doesn't work (note that this
will also potentially involve user input/feedback in the future). That function receives
network requests from the SAMOS instrument, logs the calls (and their values), and returns
the appropriate value to signal success.

In addition to `fake_instrument()`, the module also defines an assortment of functions
that are used by it.

Authors
-------

    - Brian York (york@stsci.edu)

Use
---

    This module is not intended to be used independently. Ideally it will only be used
    when the user has directed the SAMOS control interface to create a fake instrument.

Dependencies
------------
    
    None.
"""
import logging
import socket
import sys

def fake_instrument(port):
    """
    Fake instrument hardware for the SAMOS control software to talk to, either to test out
    new code or to allow for code running and testing when the actual instrument is not
    available on the network.
    """
    ins_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ins_socket.bind('localhost', port)
    except socket.error as msg:
        print("Bind failed. Error Code: {} Message: {}".format(msg[0], msg[1]))
        sys.exit(1)
    s.listen(1)
    conn, addr = s.accept()
    while True:
        data = conn.recv(4096)
        print("Received {}".format(str(data)))
        # do something with data
