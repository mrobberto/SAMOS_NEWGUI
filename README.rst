SAMOS Control Software
######################

This repository contains control software for the SAMOS combined imaging/spectroscopic 
multi-mirror instrument. The 
`SAMOS User Manual <https://www.overleaf.com/5144243873krfgcykcycjz#91ea30>`_
is available online.

Installation and Setup
**********************

SAMOS is intended to be installed by cloning this repository. The easiest way to set up 
the SAMOS software (and interface) is as follows::

    $> git clone https://github.com/mrobberto/SAMOS_NEWGUI
    $> cd SAMOS_NEWGUI
    $> conda env create -f environment.yml
    $> conda activate samos
    $> run_samos

As can be seen above, the default method of creating and running SAMOS requires some 
variant of `Anaconda <https://docs.conda.io/projects/conda/en/stable/>`_ to be installed.
However, SAMOS should also be installable with `pip` as follows::

    $> git clone https://github.com/mrobberto/SAMOS_NEWGUI
    $> pip install SAMOS_NEWGUI
    $> run_samos

In this case, you will need to have python installed.

Interface Conventions
*********************

SAMOS is built using tkinter for its GUI, and 
`ttkbootstrap <https://ttkbootstrap.readthedocs.io/en/latest/>`_ for its interface 
theming. Currently, SAMOS uses the 
`cosmo <https://ttkbootstrap.readthedocs.io/en/latest/themes/light/>`_ theme.

.. image:: https://ttkbootstrap.readthedocs.io/en/latest/assets/themes/cosmo.png

In general, SAMOS adopts the following UI conventions:

* Interface elements that allow choices to be made, or that affect the state of the SAMOS
  GUI itself, without changing the state of the hardware[1]_, use the Primary colour.
* Interface elements that send messages to the hardware in order to receive back status 
  information, but which should not themselves affect the hardware state, use the Info
  colour.

.. [1] Although they may affect what parameters are later sent to the hardware. For 
   example, selecting a filter or grism setting in the main page does not command the 
   hardware, but does affect the command that will be sent if the corresponding "set" 
   button is clicked.
