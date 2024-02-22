# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 11:07:42 2021

@author: Kate
"""

from scipy.linalg import hadamard
import numpy as np
#from data_sim_class import *
#SIM = data_sim()

class HTSI_Models():
        
    def flatten(self, img):
        y = np.shape(img)[0]
        flat_array = []
        for i in range(0,y):
            row = img[i,:]
            flat_array = np.append(flat_array, row)
        return flat_array

    def un_flatten(self, array, img_size):
        x,y = img_size[0], img_size[1]
        img = np.zeros((x,y))
        for i in range(0,y):
            index = i*x
            rowi = array[index:index+y]
            img[i,:] = rowi
        return img
    
    def adjust_spatial_resolution(self, data, slit_width):
        x,y,l = np.shape(data)[0],np.shape(data)[1],np.shape(data)[2]
        xn = np.int(x/slit_width)
        yn = np.int(y/slit_width)
        interim_data = np.zeros((xn,y,l)) # empty array with output dimensions
        new_data = np.zeros((xn,yn,l)) # empty array with output dimensions

        for i in range (0,xn):
            rows = data[(slit_width*i):((slit_width*i+(slit_width))),:,:]
            sum_row = np.sum(rows, axis=0)
            interim_data[i,:,:] = sum_row
        for ii in range (0,yn):
            cols = interim_data[:,(slit_width*ii):((slit_width*ii+(slit_width))),:]
            sum_col = np.sum(cols, axis=1)
            new_data[:,ii,:] = sum_col
        # = new_data *
        return new_data
   
    def compute_MSEs_Q(self, sky, htsi_data, mos_data, max_adu, order, gain, slit_width):
        if slit_width > 1:
            sky= self.adjust_spatial_resolution(sky, slit_width)
        y1, y2 = np.int((np.shape(sky)[0]/2)-(order/2)), np.int((np.shape(sky)[0]/2)+(order/2))
        sky_ADU = (sky[y1:y2,y1:y2,:] * gain).astype(np.int) # multiplies by gain to convert to ADU from e-, sets to integer type
        sky_ADU[sky_ADU >max_adu] = max_adu # models pixel saturation
        
        m_MSEs = []
        h_MSEs = []
        qs = []
        for k in range(0,order):
            htsi = htsi_data[:,:,k] #- dark_frames_crop[:,k,:] #comment or uncomment to include dark frame subtraction
            err =  htsi - sky[y1:y2,y1:y2,k]
            Hmse = np.mean(err**2)
            h_MSEs = np.append(h_MSEs, Hmse)
            mos = mos_data[:,:,k] #- dark_frames_crop[:,k,:] #comment or uncomment to include dark frame subtraction
            err2 =  mos - sky[y1:y2,y1:y2,k]
            Mmse = np.mean(err2**2)
            m_MSEs = np.append(m_MSEs, Mmse)
            q = np.divide((np.sqrt(Mmse)),(np.sqrt(Hmse)))
            qs = np.append(qs,q)
            
        Q = np.divide((np.sqrt(np.mean(m_MSEs))),(np.sqrt(np.mean(h_MSEs))))
        
        return Q, qs, m_MSEs, h_MSEs, sky_ADU

         
    
    def addNoise(self, img, t, dt, num_pix_real, rn, gain, max_adu):
        signal_in = img  # The image should be the signal in terms of photons (or electrons)
        #generating shot noise with poisson stats
        shot_noise = np.random.poisson(signal_in,(np.shape(signal_in)))
        
        # Now add in the electrons from dark current and read noise:
        dark_current = dt*1*t #  electrons from dark current per pixel  = thermal dark signal x exposure time
        dc_noise = np.random.poisson(dark_current,(np.shape(signal_in)))# The dark current follows a poisson distribution
        
        # Read noise is added uniformly to every image pixel and is best representaed as a normal distribution 
        read_noise = np.random.normal(scale=rn, size=signal_in.shape) # Computing read noise
        
        # use rounding to ensure electrons are a discrete number
        signal_out = np.round(read_noise+shot_noise + dc_noise) # Adding read noise and dark current noise to the signal in electrons
        ADU_offset = 0
        signal_out_ADU = (signal_out * gain).astype(np.int) + ADU_offset # multiplies by gain to convert to ADU from e-, sets to integer type
        signal_out_ADU[signal_out_ADU >max_adu] = max_adu # models pixel saturation
                
        CCD_noise = ((np.mean(read_noise)+np.mean(dc_noise))*gain).astype(np.int) # The detector additive noise in ADU
        photons = shot_noise * gain
        photon_noise = (np.std(photons)).astype(np.int) # Photon noise in ADU
        
        return signal_out_ADU, CCD_noise, photon_noise
    
    def SNR_Q_ROI(self, x1,x2,y1,y2, htsi_data, mos_data, sky_ADU):
        
        h = htsi_data[x1:x2,y1:y2,:]
        m = mos_data[x1:x2,y1:y2,:]
        s = sky_ADU[x1:x2,y1:y2,:]
        
        h_err = h - s 
        h_mse = np.mean(h_err**2) # The mean square error
        htsi_S = np.mean(h)
        m_err = m - s
        mos_S = np.mean(m)
        m_mse = np.mean(m_err**2) # The mean square error

        Q = np.divide((np.sqrt(m_mse)),(np.sqrt(h_mse)))

        h_spec = np.average(h, axis=0)
        h_spec = np.average(h_spec, axis=1)
        
        m_spec = np.average(m, axis=0)
        m_spec = np.average(m_spec, axis=1)
        
        s_spec = np.average(s, axis=0)
        s_spec = np.average(s_spec, axis=1)
        
        return htsi_S, mos_S, h_spec, m_spec, s_spec, Q, h_mse, m_mse
    
    def SNR_pt(self, x,y, htsi_data, mos_data, sky_ADU):
        
        h = htsi_data[x,y,:]
        m = mos_data[x,y,:]
        s = sky_ADU[x,y,:]
        
        h_err = h - s 
        h_mse = np.mean(h_err**2) # The mean square error
        htsi_SNR = np.median(np.divide(h,h_err))
        m_err = m - s
        mos_SNR = np.median(np.divide(m,m_err))
        m_mse = np.mean(m_err**2) # The mean square error

        Q = np.divide((np.sqrt(m_mse)),(np.sqrt(h_mse)))

        return htsi_SNR, mos_SNR, Q, h_mse, m_mse
    
    def htsi(self, sky, order, slit_width, DMD_contrast, CCD):
        H = hadamard(order, dtype='float64') # Generates the Hadamard matrix
        c1 = 1 - np.divide(1,DMD_contrast) # Accounts for singular value of DMD contrast
        c2 = 0 + np.divide(1,DMD_contrast) # Accounts for singular value of DMD contrast
        if slit_width > 1:
            sky = self.adjust_spatial_resolution(sky, slit_width)
        D_ccd = np.zeros((np.shape(sky)[0],np.shape(sky)[2],order))
        dark_frames = np.zeros(np.shape(D_ccd))
        y1, y2 = np.int((np.shape(sky)[0]/2)-(order/2)), np.int((np.shape(sky)[0]/2)+(order/2))
        t, dt, num_pix, rn, gain, max_adu = CCD[0],CCD[1],CCD[2],CCD[3],CCD[4],CCD[5]
        
        pho_noise = [] 
        ccd_noise = []
                        
        print('Starting HTSI simulation')
        for i in range (0,order):
            dmd_row1 = np.zeros((np.shape(sky)[0])) # representing an entire DMD 
            dmd_row2 = np.copy(dmd_row1)
            row = H[i,:] #index the matrix to get a row
            row_1 = np.copy(row)
            row_2 = np.copy(row)
            for j in range(0, len(row)):
                if row[j] < 0:
                    row_1[j] = c2
                    row_2[j] = c1 
                else:
                    row_2[j] = c2 
                    row_1[j] = c1 
            
            dmd_row1[y1:y2]= row_1 # Inserting the indexed row to the mask
            dmd_row2[y1:y2]= row_2 # Inserting the indexed row to the mask
            
            empty_row = np.ones((np.shape(sky)[0]))*c2
            bg = np.matmul(empty_row, sky)
            dark = np.zeros((np.shape(bg)))
            dark,a,b = self.addNoise(dark,t,dt,num_pix, rn, gain, max_adu)
            Di_1 = np.matmul(dmd_row1, sky[y1:y2,:,:])
            Di_2 = np.matmul(dmd_row2, sky[y1:y2,:,:])
            # Add detector noise to the images
                        
            Di_1, ccd_N1, pho_N1 = self.addNoise(Di_1,t, dt, num_pix, rn, gain, max_adu)
            Di_2, ccd_N2, pho_N2 = self.addNoise(Di_2,t, dt, num_pix, rn, gain, max_adu)
            ccd_noise = np.append(ccd_noise,np.mean((ccd_N1,ccd_N2)))
            pho_noise = np.append(pho_noise, np.mean((pho_N1, pho_N2)))
            data = Di_1 - Di_2
    
            Full_D1,a,b = self.addNoise(bg,t, dt, num_pix, rn, gain, max_adu)
            Full_D2,a,b = self.addNoise(bg,t, dt, num_pix, rn, gain, max_adu)
            Full_D = Full_D1-Full_D2
            Full_D[y1:y2,:]= data
    
            D_ccd[:,:,i] = Full_D #- dark
            D = D_ccd[y1:y2,:,:] 
            dark_frames[:,:,i] = dark
           
        #dark_frames_crop = dark_frames[y1:y2,:,:]    
        flat_data = self.flatten(D[:,:,0])
        x,y = np.shape(D)[0], np.shape(D)[1]
        print('HTSI data simulated. Starting Reconstruction')
        for j in range(1,order):
            img = D[:,:,j]
            flat = self.flatten(img)
            flat_data = np.vstack((flat_data,flat))    
        HD = np.matmul(H, flat_data) # Inverse Hadmard transform
        # Data reconstruction
        htsi_data = np.zeros((x,np.shape(D)[2],y)) # The final reconstructed data cube from HTSI
        for ii in range(0,order):
            row = HD[ii,:]
            img = np.reshape(row,(x,y))
            img = np.divide(img,order)
            htsi_data[:,ii,:]= img
        print('data reconstruction done.')
        ## Convert sky photons/sec/pixel into ADU (e.g. signal recorded on the dector)
        ## This conversion does not account for noise- its for comparison purposes. 
        #if slit_width > 1:
            #sky_ADU = self.adjust_spatial_resolution(sky, slit_width)
        sky_ADU = (sky[y1:y2,y1:y2,:] * gain).astype(np.int) # multiplies by gain to convert to ADU from e-, sets to integer type
        sky_ADU[sky_ADU >max_adu] = max_adu # models pixel saturation
        
        MSEs = []
        for k in range(0,order):
            htsi_cal = htsi_data[:,:,k] #- dark_frames_crop[:,k,:] #comment or uncomment to include dark frame subtraction
            err =  htsi_cal - sky[y1:y2,y1:y2,k]
            mse = np.mean(err**2)
            MSEs = np.append(MSEs, mse)
        
        return htsi_data, sky_ADU, MSEs, ccd_noise, pho_noise #percent_err, D, Di_1, Full_D, ccd_noise, pho_noise, dark_frames_crop
    
    def MOS(self, sky, order, slit_width, DMD_contrast, CCD):
        #### Create measurements capturing the same field but with MOS mode. 
        M = np.zeros((order,order))
        for k in range(0,order):
            M[k,k] = 1
        
        #### Create measurements capturing the same field but with MOS mode. 
        c1 = 1 - np.divide(1,DMD_contrast) ##- update to include dmd contrast in this one
        c2 = 0 + np.divide(1,DMD_contrast)
        
        if slit_width >1:
            sky = self.adjust_spatial_resolution(sky, slit_width)
            #y1, y2 = np.int((np.shape(sky)[0]/2)-(order/2)), np.int((np.shape(sky)[0]/2)+(order/2))
       
        y1, y2 = np.int((np.shape(sky)[0]/2)-(order/2)), np.int((np.shape(sky)[0]/2)+(order/2))
        t, dt, num_pix, rn, gain, max_adu = CCD[0],CCD[1],CCD[2],CCD[3],CCD[4],CCD[5]
        sky_crop = sky[y1:y2,y1:y2,:]
            
        mos_data = np.zeros((np.shape(sky_crop)[0],np.shape(sky_crop)[1],np.shape(sky_crop)[2]))
        t, dt, num_pix, rn, gain, max_adu = CCD[0],CCD[1],CCD[2],CCD[3],CCD[4],CCD[5]

        sky_ADU = (sky_crop * gain).astype(np.int) # multiplies by gain to convert to ADU from e-, sets to integer type
        sky_ADU[sky_ADU >max_adu] = max_adu # models pixel saturation
        mos_mse = []
        ccd_noise = []
        pho_noise = []
        #dark_img = np.zeros(np.shape(sky_crop[:,0,:]))
        
        for i in range (0, order):
            # Creating images multiplexed in a image slicer mode (for comparison):
            #################################
            dmd_row = np.zeros((np.shape(sky)[0])) # representing an entire DMD 
            row0 = M[i,:] #index the matrix to get a row
            row = np.copy(row0)
            for j in range(0, len(row)):
                if row[j] <= 0:
                    row[j] = c2
                else:
                    row[j] = c1 
            # 4b. create realistic DMD rows representing the whole device array
            dmd_row[y1:y2]= row # Inserting the indexed row to the mask
            # 4c. Create "dark" images with a mask with all mirrors off. 
            empty_row = np.ones((np.shape(sky)[0]))*c2
            bg = np.matmul(empty_row, sky)
            dark = np.zeros((np.shape(bg)))
            dark_img_noise,a,b = self.addNoise(dark,t,dt,num_pix, rn, gain, max_adu)
            # 4d. Create the multiplexed 2-D image based on the DMD mask
            mos_img = np.matmul(dmd_row, sky[y1:y2,:,:])
            # 4f. Add detector noise to the images
            mos_img_noise, ccd, pho = self.addNoise(mos_img,t, dt, num_pix, rn, gain, max_adu)
            ##################################            
            #mos_img = sky_crop[:,i,:] # slicing the data as a MOS would
            #mos_img_noise, ccd, pho = self.addNoise(mos_img, t, dt, num_pix, rn, gain, max_adu) # Adding photon and detector noise to the images
            #dark_img_noise,a,b = self.addNoise(dark_img, t, dt, num_pix, rn, gain, max_adu)
            #mos_img_cal = mos_img_noise - dark_img_noise # Use if want to subtract dark prior to calculating errors
            mos_data[:,i,:] = mos_img_noise  # The data cube containing all mos generated images
             
            ccd_noise = np.append(ccd_noise, ccd)
            pho_noise = np.append(pho_noise, pho)
            err = mos_img_noise - sky_ADU[:,i,:] # The error aka difference between resulting MOS data and original sky
            mse = np.mean(err**2) # The mean square error
            mos_mse = np.append(mos_mse, mse) # append mse to array to save all MSEs

        print('MOS simulation complete')    
        return mos_data, sky_ADU, mos_mse, ccd_noise, pho_noise

    def S_htsi(self, sky, order, slit_width, DMD_contrast, CCD):
        # Step 1. Generate Hadamard matrix (S-matrix in this case)
        S = self.S_matrix(order) # Generates the S-matrix
        
        # Step 2. Define mask errors based off DMD contrast values
        c1 = 1 - np.divide(1,DMD_contrast) # Accounts for singular value of DMD contrast
        c2 = 0 + np.divide(1,DMD_contrast) # Accounts for singular value of DMD contrast
        # Step 3. Account for the slit wdith by adjusting spatial resolution of images
        if slit_width > 1:
            sky = self.adjust_spatial_resolution(sky, slit_width)

        
        # Create some emppy arrays for population later
        D_ccd = np.zeros((np.shape(sky)[0],np.shape(sky)[2],order))
        dark_frames = np.zeros(np.shape(D_ccd))
        y1, y2 = np.int((np.shape(sky)[0]/2)-(order/2)), np.int((np.shape(sky)[0]/2)+(order/2)) # variables to help define central ROI 
        t, dt, num_pix, rn, gain, max_adu = CCD[0],CCD[1],CCD[2],CCD[3],CCD[4],CCD[5] # unpack the CCD properties
        pho_noise = [] 
        ccd_noise = []
        print('Starting HTSI simulation')
        
        # Step 4. Create simulated HTSI detector images
        for i in range (0,order):
            # 4a. Create the DMD masks based off the matrix rows
            dmd_row = np.zeros((np.shape(sky)[0])) # representing an entire DMD 
            row0 = S[i,:] #index the matrix to get a row
            row = np.copy(row0)
            for j in range(0, len(row)):
                if row[j] <= 0:
                    row[j] = c2
                else:
                    row[j] = c1 
            # 4b. create realistic DMD rows representing the whole device array
            dmd_row[y1:y2]= row # Inserting the indexed row to the mask
           
            # 4c. Create "dark" images with a mask with all mirrors off. 
            empty_row = np.ones((np.shape(sky)[0]))*c2
            bg = np.matmul(empty_row, sky)
            dark = np.zeros((np.shape(bg)))
            dark,a,b = self.addNoise(dark,t,dt,num_pix, rn, gain, max_adu)
         
            # 4d. Create the multiplexed 2-D image based on the DMD mask
            Di = np.matmul(dmd_row, sky[y1:y2,:,:])
            # 4f. Add detector noise to the images
            Di, ccd_N, pho_N = self.addNoise(Di,t, dt, num_pix, rn, gain, max_adu)
            ccd_noise = np.append(ccd_noise, ccd_N)
            pho_noise = np.append(pho_noise, pho_N)

            # 4e. Create a "background" full frame for the entire ccd image & add noise- then add the HTSI data
            # This creates a more realistic representation of what the detector images would measure
            Full_frame,a,b = self.addNoise(bg,t, dt, num_pix, rn, gain, max_adu) # A full-sized frame with background
            Full_frame[y1:y2,:]= Di # inserting the HTSI data into the full frame
            
            # Save everything into data cubes!
            D_ccd[:,:,i] = Full_frame #- dark # A collection of full sized dector images
            D = D_ccd[y1:y2,:,:] # Images with only the HTSI ROI 
            dark_frames[:,:,i] = dark # dark frames for "callibration" purposes
            
        #dark_frames_crop = dark_frames[y1:y2,:,:]    
        # Step 5. Flatten the multiplexed data array to prepare for reconstruction.
        flat_data = self.flatten(D[:,:,0])
        x,y = np.shape(D)[0], np.shape(D)[1]
        print('x: '+ str(x))
        print('y: '+ str(y))
        print('shape of D: '+ str(np.shape(D)))

        print('HTSI data simulated. Starting Reconstruction')
        for j in range(1,order):
            img = D[:,:,j]
            flat = self.flatten(img)
            flat_data = np.vstack((flat_data,flat))    
            
        # Step 6. Apply the inverse hadamard transform to the flattened multiplexed data. e
        # Inverse transfrom with an S-matrix = 2/(n+1) * (2*ST - J)
        a = np.divide(2, (order+1)) # a constant in the equation
        J = np.ones((order,order)) # The J matrix, (all 1s same size as S-matrix)
        St = np.transpose(S) # The transpose of S-matrix
        S_inv = a*((2*St)-J) # The inverse of the S-matrix per equations given in Harwit's book
        SD = np.matmul(S_inv, flat_data) # Inverse Hadmard transform
        
        # Step 7. Data reconstruction
        htsi_data = np.zeros((order,order,np.shape(D)[1])) # The final reconstructed data cube from HTSI
        # 7a. Re-shape/un-flatten the data and divide by the appropriate factor to get a reconstructed 2-d image, then collect all into a cube
        for ii in range(0,order):
            row = SD[ii,:]
            #img = HTSI.un_flatten(row,(x,y))
            img = np.reshape(row,(x,y))
            htsi_data[:,ii,:]= img
        print('data reconstruction done.')
     
        # Step 8. Convert sky photons/sec/pixel into ADU (e.g. signal recorded on the dector)
        # This conversion does not account for noise- its for comparison purposes. 
       # if slit_width > 1:
        #    sky_ADU = self.adjust_spatial_resolution(sky, slit_width)
        sky_ADU = (sky[y1:y2,y1:y2,:] * gain).astype(np.int) # multiplies by gain to convert to ADU from e-, sets to integer type
        sky_ADU[sky_ADU >max_adu] = max_adu # models pixel saturation
        
        # Step 9. Compute the error and mean square error of the entire data cube
        MSEs = []
        for k in range(0,order):
            htsi_cal = htsi_data[:,:,k] #- dark_frames_crop[:,k,:] #comment or uncomment to include dark frame subtraction
            err =  htsi_cal - sky[y1:y2,y1:y2,k]
            mse = np.mean(err**2)
            MSEs = np.append(MSEs, mse)
        
        return htsi_data, sky_ADU, MSEs, ccd_noise, pho_noise #percent_err, D, Di_1, Full_D, ccd_noise, pho_noise, dark_frames_crop

############################ S Matrix Stuff ###################################################################
    
    def S_matrix(self,n):    # Creats a cyclical S-matrix
        # First a list of all possible order S-matrices provided (from Hadamard book)
        s_orders = [3,7,11,15,19,23,31,35,43,47,63,71,79,83,103,127,255]
        exists = n in s_orders
        if exists == False: 
            print('Invalid order for the S-matrix')
            print('Valid S-matrix orders are: ' +str(s_orders))
            return
        s3 = [1,0,1]
        s7 = [1,1,1,0,1,0,0]
        s11 = [1,1,0,1,1,1,0,0,0,1,0]
        s15 =[0,0,0,1,0,0,1,1,0,1,0,1,1,1,1]
        s19 = [1,1,0,0,1,1,1,1,0,1,0,1,0,0,0,0,1,1,0]
        s23 = [1,1,1,1,1,0,1,0,1,1,0,0,1,1,0,0,1,0,1,0,0,0,0]
        s31=[0,0,0,0,1,0,0,1,0,1,1,0,0,1,1,1,1,1,0,0,0,1,1,0,1,1,1,0,1,0,1]
        s35=[0,0,1,0,0,1,1,0,1,0,1,0,0,0,0,1,0,0,1,1,1,0,1,1,1,1,1,0,0,0,1,1,1,0,1]
        s43 = [1,1,0,0,1,0,1,0,0,1,1,1,0,1,1,1,1,1,0,0,0,1,0,1,1,1,0,0,0,0,0,1,0,0,0,1,1,0,1,0,1,1,0]
        s47= [1,1,1,1,1,0,1,1,1,1,0,0,1,0,1,0,1,1,1,0,0,1,0,0,1,1,0,1,1,0,0,0,1,0,1,0,1,1,0,0,0,0,1,0,0,0,0]
        s63= [0,0,0,0,0,1,0,0,0,0,1,1,0,0,0,1,0,1,0,0,1,1,1,1,0,1,0,0,0,1,1,1,0,0,1,0,0,1,0,1,1,0,1,1,1,0,1,1,0,0,1,1,0,1,0,1,0,1,1,1,1,1,1]
        s71= [1,1,1,1,1,1,1,0,1,1,1,0,1,0,0,1,1,0,1,1,1,0,0,0,1,1,0,1,0,1,1,0,1,0,0,0,1,1,1,0,1,0,0,1,0,1,0,0,1,1,1,0,0,0,1,0,0,1,1,0,1,0,0,0,1,0,0,0,0,0,0]
        s79= [1,1,1,0,1,1,0,0,1,1,1,1,0,1,0,0,1,0,1,1,1,1,1,1,0,1,1,0,0,0,0,1,1,0,0,0,1,0,1,0,1,0,1,0,1,1,1,0,0,1,1,1,1,0,0,1,0,0,0,0,0,0,1,0,1,1,0,1,0,0,0,0,1,1,0,0,1,0,0]
        s83= [1,1,0,1,1,0,0,1,0,1,1,1,1,0,0,0,1,1,0,0,0,1,0,1,0,1,1,1,1,1,1,1,0,1,0,0,1,1,1,0,1,1,0,0,1,0,0,0,1,1,0,1,0,0,0,0,0,0,0,1,0,1,0,1,1,1,0,0,1,1,1,0,0,0,0,1,0,1,1,0,0,1,0]
        s103= [1,1,1,0,1,0,0,1,1,1,0,0,0,1,1,1,1,1,1,1,0,0,0,1,0,1,1,0,1,1,1,0,1,1,1,0,1,0,1,0,0,1,0,0,0,0,1,0,0,1,1,0,1,0,0,1,1,0,1,1,1,1,0,1,1,0,1,0,1,0,0,0,1,0,0,0,1,0,0,1,0,1,1,1,0,0,0,0,0,0,0,1,1,1,0,0,0,1,1,0,1,0,0]
        s127= [0,0,0,0,0,0,1,0,0,0,0,0,1,1,0,0,0,0,1,0,1,0,0,0,1,1,1,1,0,0,1,0,0,0,1,0,1,1,0,0,1,1,1,0,1,0,1,0,0,1,1,1,1,1,0,1,0,0,0,0,1,1,1,0,0,0,1,0,0,1,0,0,1,1,0,1,1,0,1,0,1,1,0,1,1,1,1,0,1,1,0,0,0,1,1,0,1,0,0,1,0,1,1,1,0,1,1,1,0,0,1,1,0,0,1,0,1,0,1,0,1,1,1,1,1,1,1]
        s255= [0,0,0,0,0,0,0,1,0,1,1,1,0,0,0,1,1,1,0,1,1,1,1,0,0,0,1,0,1,1,0,0,1,1,0,1,1,0,0,0,0,1,1,1,1,0,0,1,1,1,0,0,0,0,1,0,1,0,1,1,1,1,1,1,1,1,0,0,1,0,1,1,1,1,0,1,0,0,1,0,1,0,0,0,0,1,1,0,1,1,1,0,1,1,0,1,1,1,1,1,0,1,0,1,1,1,0,1,0,0,0,0,0,1,1,0,0,1,0,1,0,1,0,1,0,0,0,1,1,0,1,0,1,1,0,0,0,1,1,0,0,0,0,0,1,0,0,1,0,1,1,0,1,1,0,1,0,1,0,0,1,1,0,1,0,0,1,1,1,1,1,1,0,1,1,1,0,0,1,1,0,0,1,1,1,1,0,1,1,0,0,1,0,0,0,0,1,0,0,0,0,0,0,1,1,1,0,0,1,0,0,1,0,0,1,1,0,0,0,1,0,0,1,1,1,0,1,0,1,0,1,1,0,1,0,0,0,1,0,0,0,1,0,1,0,0,1,0,0,0,1,1,1,1,1]
        #    s511= []
        #    s1023= []
    
        s_mat = np.zeros((n,n))
        # Insert first row of the matrix based on the order number
        if n == 3:
            s_mat[0,:] = s3
        if n == 7:
            s_mat[0,:] = s7
        if n == 11:
            s_mat[0,:] = s11
        if n == 15:
            s_mat[0,:] = s15
        if n == 19:
            s_mat[0,:] = s19
        if n == 23:
            s_mat[0,:] = s23      
        if n == 31:
            s_mat[0,:] = s31
        if n == 35:
            s_mat[0,:] = s35
        if n == 43:
            s_mat[0,:] = s43
        if n == 47:
            s_mat[0,:] = s47
        if n == 63:
            s_mat[0,:] = s63
        if n == 71:
            s_mat[0,:] = s71  
        if n == 79:
            s_mat[0,:] = s79
        if n == 83:
            s_mat[0,:] = s83
        if n == 103:
            s_mat[0,:] = s103
        if n == 127:
            s_mat[0,:] = s127
        if n == 255:
            s_mat[0,:] = s255
    #   if n == 511:
#           s_mat[0,:] = s511     
#       if n == 1023:
#           s_mat[0,:] = s1023
    # Now go through and populate the matrix
        for i in range (0,n-1):
            row = np.roll(s_mat[i,:],-1,axis=0)
            s_mat[i+1,:]=row
    
        return s_mat

########################################################################################################3
