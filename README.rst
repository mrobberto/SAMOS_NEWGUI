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
However, SAMOS should also be installable with `pip` as follows:

    $> git clone https://github.com/mrobberto/SAMOS_NEWGUI
    $> pip install SAMOS_NEWGUI
    $> run_samos

In this case, you will need to have python installed.

Interface Conventions
*********************

SAMOS is built using tkinter for its GUI, and 
`ttkbootstrap <https://ttkbootstrap.readthedocs.io/en/latest/>`_ for its interface 
theming. In general, 
