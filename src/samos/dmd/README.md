# Pixel/DMD Coordinate Transformations

In order to accurately predict the pixels corresponding to a set of micromirrors (and vice
versa), we need to solve for the transformation matrix which will allow us to switch
between the CCD and DMD coordinate systems.  This GUI takes images of a DMD pattern
obtained with the SAMOS Imager and uses 
[Astropy WCS tools](https://docs.astropy.org/en/stable/wcs/index.html) to find a solution
that is compatible with the [FITS WCS standard](https://fits.gsfc.nasa.gov/fits_wcs.html).
This is in active development.

### Step 0

Upon running the script, a window will pop up where the user may load an image (Figure 1).
The image here is a 54x54 grid of points, the details of which are in the DMD pattern
table `grid_54x54_dmd.csv`, which is loaded via the `Open DMD Pattern File` button. (There
should be a way for the program to automatically select an image's corresponding pattern
file, I will work on this.)

| ![ScreenShot](DMD_gui_loaded_grid.png)|
|:--:|
| ***Figure 1*** *Grid image loded into GUI*| 

### Step 1
The first step of getting the coordinate transformation is to extract the point sources.
We need to specify the number of points we want to map out so the source extractor only
reads the points we want. For a 54x54 grid, this would be 2,916 sources. (**However,
because of the misalignment of the CCD when this image was taken, which can be seen in the
edges of the image in Figure 1, in this example I am excluding the left column and top row
to treat it as a grid of 53x53=2809 points, so that is the number we add to the input.**)

Then, enter the approximate FWHM for the points and run the star finder. When finished,
each source is marked by a circle so we may check that the source extractor picked out all
the correct points, with the table of extracted pixel coordinates displayed below the
image (Figure 2).


| ![ScreenShot](dmd_grid_sextract.png)|
|:--:|
| ***Figure 2*** *RunIRAFStarFinder result.  Blue circles are added to the figure and centered on coordinates obtained by the source extractor, with the output table shown in the panel below.*| 

### Step 2
Now that we have matched coordinates for both the CCD and DMD frames (remember we loaded
the DMD pattern file in Step 0), we can initialize the affine transformation matrix
solver.  Since slight warping at the edges of the CCD image is expected, we want include
[SIP distortion](https://irsa.ipac.caltech.edu/data/SPITZER/docs/files/spitzer/shupeADASS.pdf)
in the fit. Enter the degree of distortion that seems appropriate and run the fitting
algorithm.
 
There are two transformations that we solve for: 
![equation](https://latex.codecogs.com/gif.image?%5Cdpi%7B110%7D%5Cbg%7Bwhite%7D%7B%5Ccolor%7BBlack%7D%20%20%5Ctextbf%7BDMD%7D_%7Bxy%7D%5Crightarrow%20%5Ctextbf%7BCCD%7D_%7Bxy%7D%20%5C%20%5Cmathrm%7Band%7D%20%5C%20%5Ctextbf%7BCCD%7D_%7Bxy%7D%5Crightarrow%20%5Ctextbf%7BDMD%7D_%7Bxy%7D%20%7D)

The names of the transformation functions are `ccd2dmd_wcs` and `dmd2ccd_wcs`, each of
which can be inversely applied, giving 4 total coordinate transformation functions.

To check the accuracy of each, this step applies the transformations to the coordinates
read from the pattern file (or source extraction table for CCD), and computes the
difference between resulting X and Y coordinates and the known values. For instance, the
`ccd2dmd_wcs` and (inverse)`dmd2ccd_wcs` transformations are applied to the pixel
coordinates in the extracted sources table to produce two estimates for mirror locations
on the DMD.  These output mirror coordinates are compared to the coordinates in the DMD
pattern table.  The differences between $x_{in},x_{out}$ and $y_{in},y_{out}$ for both
transformations are plotted as histograms (Figure 3). Then, we have to decide which
transformation function(s) work best.

| ![ScreenShot](grid_54x54_coord_transf_output_sip3.png)|
|:--:|
| ***Figure 3*** *Histogram of differences between known and transformed coordinats.  Top row shows the results of the DMD mirror positions transformed from CCD pixels.  Bottom row shows the CCD coordinates transformed from the DMD mirrors.*| 
