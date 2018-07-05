''' Script to split the mask on its bits, then calculate the area masked
by each bit, and in how many different sets of contiguous pixels.
The results are saved in a dictionary

NOTE: a useful method wrapping various functvions in skimage is 
skimage.measure.regionprops
'''

import os
import sys
import argparse
import copy
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import fitsio
from skimage import measure
import multiprocessing as mp

def open_fits(fnm, ext=None, s=None, h_ext='SCI'):
    ''' Open fits and return a copy of the selected data, as well as the header
    '''
    tmp = fitsio.FITS(fnm)
    if (s is None):
        extension = tmp[ext]
        ext_tmp = np.copy(extension.read())
    else:
        subarea = tmp[ext]
        ext_tmp = subarea[s[1] : s[3], s[0] : s[2]]
    # Get the primary header, not restricted to the extension only
    header_tmp = copy.deepcopy(tmp[h_ext].read_header())
    return ext_tmp, header_tmp

def get_moments(image):
    ''' Image moments does not perform well in this scenario, I didn't 
    investigated the source
    '''
    order = 7
    imm = measure.moments(image, order=order)
    return imm 

def get_labels(image, back_value=0, ):
    ''' Image labels, simplistic clustering only based in contiguous pixels
    hving the same value
    '''
    labels, n_labels = measure.label(image, background=back_value, 
                                     return_num=True,
                                     connectivity=image.ndim)
    return labels, n_labels

def labels_prop(label_image):
    ''' Using the labeled image, get some useful measurements
    '''
    prop = measure.regionprops(label_image, cache=True)
    return prop

def decompose_bit2(z_int):
    ''' Decompose a number in the unique base 2 bits needed to produce the 
    number
    Note:
    - x & y: Bitwise and, bit by bit comparison
    - x << y: Returns x with the bits shifted to the left by y places 
    (and new bits on the right-hand-side are zeros). This is the same as 
    multiplying x by 2**y.
    '''
    base2bit = []
    k = 1
    while (k <= z_int):
        if (k & z_int):
            base2bit.append(k)
        k = k << 1
    return base2bit

def flatten_list(list_2levels):
    ''' Returns a flatten list, when a nested list of lists is given
    '''
    f = lambda x: [item for sublist in x for item in sublist]
    return f(list_2levels)

def aux_main(tab, extension=None, section=None, outname=None):
    # Some empty
    expnum = []
    band = []
    mjd = []
    bit = []
    nclust = []
    area = []
    reqnum = []
    attnum = []
    unitname = []
    nite = []
    ccdnum = []
    # Load the one-column file with the filenames
    df_fits = pd.read_table(tab, sep='\s+', engine='python', names=['path'])
    for idx, row in df_fits.iterrows():
        try:
            x, hdr = open_fits(row.path, ext=extension, s=section)
        except:
            print('Issue opening: {0}'.format(row.path))
            continue
        # Unique values for the section
        aux_uni, aux_uni_cnt = np.unique(x.ravel(), return_counts=True)
        # How many bits do we have? It is important to keep the ascending
        # sorting, as it will be used for filling up the array
        all_bits = map(decompose_bit2, aux_uni)
        all_bits = flatten_list(all_bits)
        all_bits = list(set(all_bits))
        all_bits = sorted(all_bits)
        all_bits = tuple(all_bits)
        # Array to be used as template over which to stack different bit 
        # layers
        aux_layer = np.zeros((x.shape[0], x.shape[1], len(all_bits)))
        # Go through all unique values and decompose them on their bits
        for idx, val in enumerate(aux_uni):
            list_bit = decompose_bit2(val)
            # Each one of these bits will be stored in different layers. 
            # For each one of the layers the area and number of clusters 
            # will be saved
            # Go bit by bit, for each unique value of the array
            for b in list_bit:
                tmp_arr = np.zeros_like(x)
                tmp_arr[np.where(x == val)] = b
                # Save th positions in the auxiliary array of layers
                aux_layer[: , : , all_bits.index(b)] = tmp_arr
        # The 3D array containing one layer per bit is now filled. 
        # Statistics over each one of the layers to get the area and the
        # number of clusters
        tmp_bit = []
        tmp_nclust = []
        tmp_area = []
        for idxL in range(aux_layer.shape[2]):
            lab, n_labs = get_labels(aux_layer[: , : , idxL]) 
            areaL = np.flatnonzero(aux_layer[: , : , idxL]).size
            tmp_bit.append(all_bits[idxL])
            tmp_nclust.append(n_labs)
            tmp_area.append(areaL)
        # Fill the results array
        expnum.append(hdr['EXPNUM'])
        mjd.append(hdr['MJD-OBS'])
        band.append(hdr['BAND'].strip()) # (hdr['FILTER'].strip()[0])
        bit.append(tmp_bit)
        nclust.append(tmp_nclust)
        area.append(tmp_area)
        # Additional
        reqnum.append(int(hdr['REQNUM']))
        unitname.append(hdr['UNITNAME'].strip())
        attnum.append(int(hdr['ATTNUM']))
        nite.append(int(hdr['NITE']))
        ccdnum.append(int(hdr['CCDNUM']))
    # Dictionary to be saved as dataframe
    kw = dict()
    kw['expnum'] = expnum
    kw['mjd'] = mjd
    kw['band'] = band
    kw['bit'] = bit
    kw['bit_nclust'] = nclust
    kw['bit_area'] = area
    kw['reqnum'] = reqnum
    kw['attnum'] = attnum
    kw['unitname'] = unitname
    kw['nite'] = nite
    kw['ccdnum'] = ccdnum
    df_res = pd.DataFrame.from_dict(kw)
    # Write out
    if (outname is None):
        aux_b = ''.join( list(set(kw['band'])) )
        outname = 'maskStat_{0}_PID{1}.csv'.format(aux_b, os.getpid())
    df_res.to_csv(outname, index=False, header=True)
    print('Saved: {0}'.format(outname))
    return True

if __name__ == '__main__':
    ''' Regions to look
    1) wedge: (x , y) = (25 , 3094) to (2023 , 3285)
    2) lightbulb: (x , y) = (645 , 2470) to (945 , 4080)
    '''
    t_gral = 'Simple code to get FITS image moments, for the entire image'
    t_gral +=  ' or for a section'
    par = argparse.ArgumentParser(description=t_gral)
    h0 = 'Filename of the list of fullpaths to the FITS images'
    par.add_argument('fits', help=h0, metavar='filename')
    aux_ext = 2
    h1 = 'Data extension of the FITS file to be loaded.'
    h1 += ' Default: {0}'.format(aux_ext)
    par.add_argument('--ext', help=h1, metavar='string/integer', 
                     default=aux_ext)
    h2 = 'Section of the CCD to be loaded. Format: x1 y1 x2 y2'
    h2 += ' Default is entire area'
    par.add_argument('--sec', help=h2, metavar='corners', nargs='+', type=int)
    h3 = 'Output filename.'
    h3 += ' Default: maskStat_{bands}_PIDnnnn.csv'
    par.add_argument('--out', help=h3, metavar='filename')
    #
    par = par.parse_args()
    #
    kw = dict()
    kw['tab'] = par.fits
    kw['extension'] = par.ext
    kw['section'] = par.sec
    kw['outname'] = par.out
    aux_main(**kw)
