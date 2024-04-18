# -*- coding: utf-8 -*-
"""
  on Thu Aug 12 11:17:10 2021
This is the script for generating DMD mask patterns for a given HTSI observation.
Input parameters include: 
    S or H matrix type
    Matrix order
    center point of matrix on DMD
    slit width (in terms of mircomirrors)

Output: A set of DMD patterns saved as images for the observation. 
image filenames 'H64_2w_mask_#.PNG' 'S79_3w_mask_#.PNG'
@author: Kate
"""
import imageio
import numpy as np
from scipy.linalg import hadamard


def S_matrix(order):
    # Creates a cyclical S-matrix
    s_matrices = {
        3: [1, 0, 1],
        7: [1, 1, 1, 0, 1, 0, 0],
        11: [1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0],
        15: [0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1],
        19: [1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0],
        23: [1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0],
        31: [0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1],
        35: [0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1],
        43: [1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0,
             1, 1, 0, 1, 0, 1, 1, 0],
        47: [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1,
             0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        63: [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1,
             0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1],
        71: [1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0,
             0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
        79: [1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0,
             1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0,
             1, 1, 0, 0, 1, 0, 0],
        83: [1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0,
             1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0,
             0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0],
        103: [1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0,
              1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0,
              1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0],
        127: [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0,
              1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0,
              1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1,
              0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1],
        255: [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1,
              1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1,
              1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1,
              0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0,
              1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1,
              0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1,
              0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1,
              1, 1, 1]
    }
    if order not in s_matrices:
        raise ValueError(f"Invalid order {order} for Hadamard S-matrix. Valid orders are: {s_matrices.keys()}")

    s_mat = np.zeros((order, order))

    # Insert first row of the matrix based on the order number
    s_mat[0, :] = s_matrices[order]

    # Now go through and populate the matrix
    for i in range(n - 1):
        row = np.roll(s_mat[i, :], -1, axis=0)
        s_mat[i + 1, :] = row

    return s_mat


def make_S_matrix_masks(order, DMD_size, slit_width, length, Xo, Yo, folder):
    matrix = S_matrix(order) # Generate the S-matrix
    matrix_type = 'S'

    DMD_mask = np.zeros((DMD_size)) # Create an array to represent the DMD mask. Use Zeros as those translate to off mirrors
    mask_set = np.zeros((DMD_size[0], DMD_size[1], order)) # data cube 1080x2048xorder filled with Zero
    for i in range(order):
        row = matrix[i, :]                           #an array of 1 or 0, as long as order (e.g. 7: [1, 1, 1, 0, 1, 0, 0]). All float
        row_expanded = np.repeat(row, slit_width)   #same but each element is now repeated eg. 3 times, so 21 values.
        mask_size_y = order * slit_width                #total number of elements, e.g. 21
        mask_size_x = length
        
        # insert that mask into the DMD mask array
        #
        # HERE IS A TRICK CHANGE OF COORDINATES: x is the long size (2048), y is the short side (1080)
        # The spectra go in the Y direction, the X is cross dispersion. 
        # So the width of the slit is in the short (Y) direction, the length is in the long (X) direction
        y1, y2 = Yo - (mask_size_y // 2), Yo + (mask_size_y // 2)
        x1, x2 = Xo - (mask_size_x // 2), Xo + (mask_size_x // 2)

        # For  vertical slits, spectra across the DMD
        for j in range(x1, x2):    
            DMD_mask[y1:y2, j]= row_expanded
        mask_set[:, :, i]= DMD_mask 
        mask = DMD_mask.astype(np.uint8)
        name = f"{matrix_type}{order}_mask_{slit_width}w_{i:03d}.bmp"
        imageio.imwrite(folder / name, mask)
        
    return mask_set, matrix


def make_H_matrix_masks(order, DMD_size, slit_width, length, Xo, Yo, folder):
    matrix = hadamard(order, dtype='float64') # generate the H-matrix 

    mask_set_a = np.zeros((DMD_size[0], DMD_size[1], order))
    mask_set_b = np.zeros((DMD_size[0], DMD_size[1], order))
    DMD_mask_a = np.zeros((DMD_size)) # Create an array to represent the DMD mask. Use Zeros as those translate to off mirrors
    DMD_mask_b = np.zeros((DMD_size)) # Create an array to represent the DMD mask. Use Zeros as those translate to off mirrors
    matrix_type = 'H'
    
    for i in range(order):
        row = matrix[i, :]
        row_expanded = np.repeat(row, slit_width)  # Adjusts the elements to account for slit widths
        mask_size_y = order * slit_width
        mask_size_x = length
    
        # Convert the -1s and +1s into pairs of masks with 1s and 0s
        row_a = np.copy(row_expanded) # 1 means on -1 means off
        row_b = np.copy(row_expanded) # 1 means off, -1 means on
        for j in range (len(row_expanded)):
            if row_expanded[j] < 0:
                row_a[j] = 0
                row_b[j] = 1 
            else:
                row_b[j] = 0 
                row_a[j] = 1 
    
        # insert that mask into the DMD mask array
        y1, y2 = Yo - (mask_size_y // 2), Yo + (mask_size_y // 2)
        x1, x2 = Xo - (mask_size_x // 2), Xo + (mask_size_x // 2)
    
        # For  vertical slits, spectra across the DMD
        for j in range(x1, x2):    # Insert the matrices into the DMD mask array
            DMD_mask_a[y1:y2, j] = row_a
            DMD_mask_b[y1:y2, j] = row_b


        mask_set_a[:, :, i]= DMD_mask_a
        mask_set_b[:, :, i]= DMD_mask_b 

        mask_a = DMD_mask_a.astype(np.uint8)
        mask_b = DMD_mask_b.astype(np.uint8)

        name_a = f"{matrix_type}{order}_mask_{slit_width}w_a_{i+1:03d}.bmp"
        name_b = f"{matrix_type}{order}_mask_{slit_width}w_b_{i+1:03d}.bmp"
        imageio.imwrite(folder / name_a, mask_a)
        imageio.imwrite(folder / name_b, mask_b)
        
    return mask_set_a, mask_set_b, matrix
