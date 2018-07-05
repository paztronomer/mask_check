# Code to measure mass and number of masks per bit

Simple code to assess a bitmask (Dark Energy Survey) of a reduced image, split
each pixel in its bits. Creating one layer of the image per bit, calculates
the mass of the mask as well as the number of connected areas.

Results are saved in a csv table (to be changed to HDF5)

Requirements:
- fitsio
- pandas
- numpy
- scikit-image
