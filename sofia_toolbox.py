import os
import glob
import numpy as np
import bottleneck as bn
import pandas as pd
import astrobox as ab
import bootmedian as bm # This is a custom made module available at GitHub. https://github.com/Borlaff/bootmedian
from tqdm import tqdm
from astropy.io import fits
import matplotlib.pyplot as plt
from celluloid import Camera
from IPython.display import Video
from astropy.wcs import WCS
from reproject import reproject_interp
import aplpy
from scipy import signal
import pickle

sigma1 = 0.682689492137086
sigma2 = 0.954499736103642
sigma3 = 0.997300203936740

s1_down_q = (1-sigma1)/2
s1_up_q = 1 - s1_down_q
s2_down_q = (1-sigma2)/2
s2_up_q = 1 - s2_down_q
s3_down_q = (1-sigma3)/2
s3_up_q = 1 - s3_down_q

def plot_profile(profile, color, linestyle, linewidth, marker, label):
    # Line + Points
    ax.plot(profile["R"]*pixsize_hawc, profile["pitch"], color=color, linestyle=linestyle,
            linewidth=linewidth, label=label, marker=marker, markerfacecolor=color,
            markersize=10, markeredgecolor="black")
    #ax.scatter(profile["R"]*pixsize_hawc, profile["pitch"], color=color, marker=marker,
    #           label='')
    # Error bars
    ax.fill_between(profile["R"]*pixsize_hawc, profile["pitch_s1up"], profile["pitch_s1down"],
                    where=(profile["pitch_s1up"] > profile["pitch_s1down"]), facecolor=color,
                    alpha=0.5, label="")
    ax.fill_between(profile["R"]*pixsize_hawc, profile["pitch_s2up"], profile["pitch_s2down"],
                    where=(profile["pitch_s2up"] > profile["pitch_s2down"]), facecolor=color,
                    alpha=0.12, label="")


def magnetic_pitch_angle_profile_plot(output_magnetic_pitch_angle_profile):

    median_curve, pitch_angle_array = output_magnetic_pitch_angle_profile
    median_pitch_angle_hawc_halfbeam = measure_median_pitch_angle(pitch_angle_array)


    fig, ax = plt.subplots(figsize=(14,7))
    #for j in range(len(pitch_angle_curves)):
    #    plt.plot(pitch_angle_curves[j]["R"], pitch_angle_curves[j]["pitch"],
    #             color="green", alpha=10/len(pitch_angle_curves))
    
    #plt.errorbar(x=median_curve["R"], y=median_curve["pitch"],
    #             xerr=(median_curve["R_s2up"]-median_curve["R_s2down"])/2., 
    #             yerr=(median_curve["pitch_s2up"]-median_curve["pitch_s2down"])/2., 
    #             elinewidth=2, color="black")   

    for j in range(len(median_curve["R"])):
        plt.scatter(median_curve["R"][j], median_curve["pitch"][j], color="black", s=2, marker="s")

        plt.plot([median_curve["R_s1up"][j], median_curve["R_s1down"][j]],
                 [median_curve["pitch"][j],median_curve["pitch"][j]], color="black")
    
        plt.plot([median_curve["R"][j], median_curve["R"][j]],
                 [median_curve["pitch_s1up"][j],median_curve["pitch_s1down"][j]], color="black")

        plt.plot([median_curve["R_s2up"][j], median_curve["R_s2down"][j]],
                 [median_curve["pitch"][j],median_curve["pitch"][j]], color="black")
    
        plt.plot([median_curve["R"][j], median_curve["R"][j]],
                 [median_curve["pitch_s2up"][j],median_curve["pitch_s2down"][j]], color="black", linewidth=0.5)
    

    plt.xlabel("R (pixels)")
    plt.axhline(y=0., color='black', linestyle='--', linewidth=3)
    plt.ylabel("Pitch angle (degrees)")
    plt.title("Pitch angle - MonteCarlo simulations") 


    return(output_magnetic_pitch_angle_profile)


def measure_median_pitch_angle(pitch_angle_array):
    median_pitch_angle_boot = np.zeros(pitch_angle_array.shape[0])
    for i in tqdm(range(pitch_angle_array.shape[0])):
        nvalid_pixels = pitch_angle_array.shape[1]
        nsimul = int(nvalid_pixels*np.log(nvalid_pixels))
        median_pitch_angle_boot[i] = bootmedian_angles(pitch_angle_array[i,:], 100)["median"]
        
    plt.hist(median_pitch_angle_boot, bins=15)
    median_pitch_angle = bootmedian_angles(median_pitch_angle_boot, 1000)["median"]
    median_pitch_angle_Ddown = np.nanpercentile(median_pitch_angle_boot, 2.5)
    median_pitch_angle_Dup = np.nanpercentile(median_pitch_angle_boot, 97.5)    
    plt.axvline(median_pitch_angle)
    plt.axvline(median_pitch_angle_Ddown)
    plt.axvline(median_pitch_angle_Dup)   
    return({"median": median_pitch_angle,
            "e95_down": median_pitch_angle_Ddown,
            "e95_up": median_pitch_angle_Dup, "boot": median_pitch_angle_boot})


def apply_mask(mode, mask_fits, header, I, dI, Q, dQ, U, dU):
    #mask_reprojected, footprint = reproject_interp(mask_fits[0], header)
    mask_reprojected = mask_fits[0].data

    if (mode == "arm"):
        print("Arm mode selected")
        bool_remove = np.logical_or((mask_reprojected == 1), (mask_reprojected == 2))

    if (mode == "interarm"):
        print("Interarm mode selected")    
        bool_remove = np.logical_or(np.logical_or((mask_reprojected == 0), (mask_reprojected == 4)), (mask_reprojected == 2)) 
        # np.logical_and((mask_reprojected == 0), (mask_reprojected == 2), (mask_reprojected == 4))
        #save_fits(mask_reprojected, image_input.replace(".fits", "_mask.fits"))

    if (mode=="north_arm"):
        print("North arm mode selected")
        bool_remove = (mask_reprojected != 4)
        #save_fits(mask_reprojected, image_input.replace(".fits", "_mask.fits"))

    if (mode=="south_arm"):
        print("South arm mode selected")
        bool_remove = (mask_reprojected != 0)
        #save_fits(mask_reprojected, image_input.replace(".fits", "_mask.fits"))
        
    if (mode=="nan"):
        print("Quality nan mode selected")
        bool_remove = np.logical_and(np.isnan(mask_reprojected))
    
    bool_integrer = bool_remove.astype("int")    
    #a = np.array([True,True,False,False,False,False,True,False,True,True,False])
    #print(a.astype("int"))
    plt.imshow(bool_integrer)  
    plt.colorbar()
    plt.show()

    if (mode!="nan"):
       #smoothed_mask = signal.convolve2d(bool_integrer, np.array([[1, 1, 1],[1, 1, 1],[1, 1, 1]])/9., boundary='symm', mode='same')
       smoothed_mask = bool_integrer
    else:
       smoothed_mask = bool_integrer
       
    plt.imshow(smoothed_mask)  
    plt.colorbar()
    plt.show()
    bool_remove_smoothed = (smoothed_mask == 1)
    I[bool_remove_smoothed] = np.nan  
    dI[bool_remove_smoothed] = np.nan
    Q[bool_remove_smoothed] = np.nan
    dQ[bool_remove_smoothed] = np.nan
    U[bool_remove_smoothed] = np.nan
    dU[bool_remove_smoothed] = np.nan

    return([I, dI, Q, dQ, U, dU])




def generate_pitch_model(pitch_profile, shape, header, xcen, ycen, PA, incl, output):
        
    q  = np.cos(np.radians(incl))
    radial_mask = create_radial_mask(xsize=shape[1], ysize=shape[0], q=q, theta=PA,
                                     center=[xcen, ycen], radius=None)

    angle_mask = create_angle_mask(xsize=shape[1], ysize=shape[0], q=q, theta=PA,
                                   center=[xcen, ycen], radius=None, pitch=0)
    save_fits(radial_mask, "radial_mask_test.fits")
    save_fits(angle_mask, "angle_mask_test.fits")
    for i in range(len(pitch_profile["R"])-1):
        if i == 0:
            xmin = 0
        else:
            xmin = xmax
        xmax = pitch_profile["R"][i+1]
    
        #print("xmin:" + str(xmin) + " - xmax :" + str(xmax))

        radial_indexes = np.where((radial_mask > xmin) & (radial_mask <= xmax))
        angle_mask[radial_indexes] = angle_mask[radial_indexes] + pitch_profile["pitch"][i]
    

    save_fits(array=angle_mask, name=output, header=header)
    return(angle_mask)


def save_fits(array, name, header=None):
    hdu = fits.PrimaryHDU(header=header, data=array)
    hdul = fits.HDUList([hdu])
    os.system("rm " + name)
    hdul.writeto(name)



def plot_pitch_model(I, pol_obs, pitch_model, SNR_int, SNR_pol, SNRi_cut = 10.0, SNRp_cut = 3.0, step=4,
                     scalevec = 2.5, header=None, save_fig="plot_pitch_model.pdf", vmin=None, vmax=None, alpha_model=1,
                     pol_fraction=None, title=" ", colorscale="viridis", color_model="red", color_obs="black", recenter=None, figsize=6.5, colorbar_label=r'Intensity (Jy arcsec$^{-2}$)'):
    # pol map cuts
    vector_scale = np.full(SNR_int.shape, 1.0)
    vector_scale[(SNR_pol < SNRp_cut)] = np.nan
    vector_scale[np.isnan(SNR_int)] = np.nan    
    vector_scale[(SNR_int < SNRi_cut)] = np.nan
    
    if pol_fraction is not None:
        vector_scale = vector_scale * pol_fraction 
    
    save_fits(vector_scale, "vector_scale.fits", header)
    vec_legend = 5
    pxscale = np.abs(header["CDELT2"])
        
    # Plot zone
    fig = plt.figure(figsize=(figsize,figsize))
    gc = aplpy.FITSFigure(I, figure=fig)
    #gc.show_grayscale()
    #gc.show_colorscale(cmap='gist_heat', vmin=32.25, vmax=30)
    
    #if header != None:
    #    gc.add_scalebar(1/60, "1 arcmin", color='black', corner='bottom left', lw=4)

    gc.show_vectors(pdata="vector_scale.fits", phdu=0, adata=pol_obs, ahdu=0,
                linewidth=3.0, step=step, scale=1.3*scalevec, color="black")
                
    gc.show_vectors(pdata="vector_scale.fits", phdu=0, adata=pol_obs, ahdu=0,
                linewidth=1.7, step=step, scale=1.0*scalevec, color=color_obs)
    
    #gc.show_vectors(pdata="vector_scale.fits", phdu=0, adata=pitch_model, ahdu=0,
    #                color="black", linewidth=2.8, step=step, scale=1.4*scalevec)

    gc.show_vectors(pdata="vector_scale.fits", phdu=0, adata=pitch_model, ahdu=0,
                    color=color_model, linewidth=1.4, step=step, scale=1.1*scalevec, alpha=alpha_model)
    
                
    gc.show_colorscale(cmap=colorscale, vmin=vmin, vmax=vmax)
    # Get the current axis 
    #ax = plt.gca()        
    # Get the images on an axis
    #im = ax.images        
    # Assume colorbar was plotted last one plotted last
    #cbar = im[-1].colorbar   
    gc.add_colorbar()
    gc.colorbar.set_axis_label_text(colorbar_label)
    #gc.colorbar.set_powerlimits((0, 0))


    #legend vector
    vecscale = scalevec * pxscale
    
    if pol_fraction is not None:
        gc.add_scalebar(vec_legend*vecscale,'P ='+np.str(vec_legend)+'%',\
	    			corner='bottom right',frame=True,color='black',facecolor='blue')
    #gc.add_scalebar(scalevec,'Rotated 90?? Pol. angle',corner='bottom right',frame=True,color='black')
    #gc.add_scalebar(scalevec,'Pitch angle model',corner='bottom right',frame=True,color='red')
    #gc.set_title(title,fontsize=15)
    
    gc.add_label(x=0.5, y=1.063, text=title, relative=True, size=13)
    
    try:
        gc.add_beam(color='red')
    except:
        print("No beam size found")
    
    if recenter is not None:
        gc.recenter(x=recenter[0], y=recenter[1], width=recenter[2], height=recenter[3])
    #fig.tight_layout()
    #fig.tight_layout()
    fig.subplots_adjust(top=0.6)     # Add space at top
    plt.savefig(save_fig, dpi=300, bbox_inches='tight')

    

    
def create_radial_mask(xsize, ysize, q=1, theta=0, center=None, radius=None):
    if center is None: # use the middle of the image
        center = (int(xsize/2), int(ysize/2))
        
    if radius is None: # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], xsize-center[0], ysize-center[1])
    X, Y = np.ogrid[:xsize, :ysize]

    radial_grid = np.sqrt((X - center[0])**2 + (Y-center[1])**2)
    
    x_image = np.linspace(np.min(X - center[0]),np.max(X - center[0]), xsize)
    y_image = np.linspace(np.min(Y - center[1]),np.max(Y - center[1]), ysize)
    
    X_image, Y_image = np.meshgrid(x_image,y_image) # Images with the observer X and Y coordinates 
    
    X_gal = (X_image*np.cos(np.radians(-theta))-Y_image*np.sin(np.radians(-theta)))/q # X in galactic frame  
    Y_gal = (X_image*np.sin(np.radians(-theta))+Y_image*np.cos(np.radians(-theta)))   # Y in galactic frame

    radial_array = np.sqrt(X_gal**2 + Y_gal**2)
    return(radial_array)



def create_angle_mask(xsize, ysize, q, theta, center=None, radius=None, pitch=90):
    if center is None: # use the middle of the image
        center = (int(xsize/2), int(ysize/2))
        
    if radius is None: # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], xsize-center[0], ysize-center[1])
    X, Y = np.ogrid[:xsize, :ysize]

    radial_grid = np.sqrt((X - center[0])**2 + (Y-center[1])**2)
    
    x_image = np.linspace(np.min(X - center[0]),np.max(X - center[0]), xsize)
    y_image = np.linspace(np.min(Y - center[1]),np.max(Y - center[1]), ysize)
    
    X_image, Y_image = np.meshgrid(x_image,y_image) # Images with the observer X and Y coordinates 
    
    X_gal = (X_image*np.cos(np.radians(theta))-Y_image*np.sin(np.radians(theta)))/q # X in galactic frame  
    Y_gal = (X_image*np.sin(np.radians(theta))+Y_image*np.cos(np.radians(theta)))   # Y in galactic frame
    
    # Calculate pitch angle in the galactic plane coordinate frame (Radial direction-90 + pitch)
    rotation = pitch - 90
    U_gal_pitch = X_gal*np.cos(np.radians(rotation)) - Y_gal*np.sin(np.radians(rotation))  
    V_gal_pitch = X_gal*np.sin(np.radians(rotation)) + Y_gal*np.cos(np.radians(rotation))   

    # Blot back the angles to the observer frame  
    U_ima_pitch = (U_gal_pitch*q*np.cos(np.radians(-theta))-V_gal_pitch*np.sin(np.radians(-theta))) # 
    V_ima_pitch = (U_gal_pitch*q*np.sin(np.radians(-theta))+V_gal_pitch*np.cos(np.radians(-theta))) #      

    #U_ima = (U_gal_pitch*q*np.cos(np.radians(theta))-V_gal_pitch*np.sin(np.radians(theta)))
    #V_ima = (U_gal_pitch*q*np.sin(np.radians(theta))+V_gal_pitch*np.cos(np.radians(theta))) 
    angle_array = np.degrees(np.arctan2(U_ima_pitch,V_ima_pitch))
    # angle_array[angle_array < 0] = angle_array[angle_array < 0] + 360
    return(np.flip(angle_array,axis=1))

    
       
# TEST AVERAGE ANGLES
def bootstrap_resample(X, weights=False, seed=None):
    dataframe = pd.DataFrame(X)
    if not isinstance(weights, bool):
        if bn.nansum(weights) == 0:
            weights = np.ones(len(weights))
        weights = weights/np.max(weights)
        weights_pd = pd.Series(weights)
        sample_pd = dataframe.sample(len(X), weights=weights_pd, replace=True, random_state = seed)
        X_resample = np.ndarray.flatten(np.array(sample_pd))
    else:
        sample_pd = dataframe.sample(len(X), replace=True, random_state = seed)
        X_resample = np.ndarray.flatten(np.array(sample_pd))

    return X_resample



def median_angle(input_sample):
    x_boot = np.cos(np.radians(2*input_sample))
    y_boot = np.sin(np.radians(2*input_sample))
    x_boot_median = bn.nanmedian(x_boot)
    y_boot_median = bn.nanmedian(y_boot)
    return(np.degrees(np.arctan2(y_boot_median,x_boot_median))/2.)

    
def bootmedian_angles(input_sample, nsimul, weights=False):
    # Clean those elements that might be NaN in input or weights
    if isinstance(weights, (list,np.ndarray)):
        index_nan = np.isnan(np.array(input_sample)* np.array(weights))
        weights = weights[~index_nan]
        weights = weights / np.max(weights)
    else:
        index_nan = (np.isnan(input_sample))

    input_sample = input_sample[~index_nan]
    
    indexes = np.linspace(0, len(input_sample)-1, len(input_sample), dtype="int")
    median_angle_boot = np.zeros(nsimul)
    
    
    
    for i in range(nsimul):
        if isinstance(weights, (list,np.ndarray)):
            #print("Weighted bootstrap")
            boot_index = bootstrap_resample(indexes, weights)
        else:        
            #print("No weights")
            boot_index = bootstrap_resample(indexes)
            
        x_boot = np.cos(np.radians(2*input_sample[boot_index]))
        y_boot = np.sin(np.radians(2*input_sample[boot_index]))
        x_boot_median = bn.nanmedian(x_boot)
        y_boot_median = bn.nanmedian(y_boot)
        median_angle_boot[i] = np.degrees(np.arctan2(y_boot_median,x_boot_median))/2.

    median_angle = bn.nanmedian(median_angle_boot)
    median_angle_s1_down = np.nanpercentile(median_angle_boot, 100*(1-sigma1)/2)
    median_angle_s1_up = np.nanpercentile(median_angle_boot, 100*(1-(1-sigma1)/2))
    median_angle_s2_down = np.nanpercentile(median_angle_boot, 100*(1-sigma2)/2)
    median_angle_s2_up = np.nanpercentile(median_angle_boot, 100*(1-(1-sigma2)/2))
    
    return({"median": median_angle,
            "s1_down": median_angle_s1_down,
            "s1_up": median_angle_s1_up,
            "s2_down": median_angle_s2_down,
            "s2_up": median_angle_s2_up})
            
            
            
def rotated_polarization_angle(U, Q):
    pol90 = (90/np.pi) * np.arctan2(U, Q) + 90             
    return(pol90)
            

def inv_rotated_polarization_angle(pol90):
    arctan2_U_Q = (pol90 - 90.)*np.pi/90
    U = np.sin(arctan2_U_Q)
    Q = np.cos(arctan2_U_Q)
    
    return([U,Q])
            
            
def plot_profile(profile, color, linestyle, linewidth, marker, label):
    # Line + Points
    ax.plot(profile["R"]*pixsize_hawc, profile["pitch"], color=color, linestyle=linestyle,
            linewidth=linewidth, label=label, marker=marker, markerfacecolor=color,
            markersize=10, markeredgecolor="black")
    #ax.scatter(profile["R"]*pixsize_hawc, profile["pitch"], color=color, marker=marker,
    #           label='')
    # Error bars
    ax.fill_between(profile["R"]*pixsize_hawc, profile["pitch_s1up"], profile["pitch_s1down"],
                    where=(profile["pitch_s1up"] > profile["pitch_s1down"]), facecolor=color,
                    alpha=0.5, label="")
    ax.fill_between(profile["R"]*pixsize_hawc, profile["pitch_s2up"], profile["pitch_s2down"],
                    where=(profile["pitch_s2up"] > profile["pitch_s2down"]), facecolor=color,
                    alpha=0.12, label="")
         
            
def single_magnetic_pitch_angle(xcen, ycen, I, dI, Q, dQ, U, dU, pol_level, dpol_level, PA, dPA, incl, dincl, nbins, nsimul,
                                save_temp=False, SNR_int_limit=5, SNR_pol_limit=1, plot_verbose=False, name="default_", header=None, bin_limits=None):
        image_shape = I.shape
        
        #########################
        ### 1- Monte Carlo generation 
        #########################
        # Debiased pol array
        pol_level = 100*np.sqrt((Q/I)**2 + (U/I)**2)
        dpol_level_A = ((Q*dQ)**2 + (U*dU)**2)/(Q**2+U**2)
        dpol_level_B = ((Q/I)**2 + (U/I)**2)*dI**2
        dpol_level = np.abs(100*np.sqrt(dpol_level_A + dpol_level_B)/I)
        pol_dbias = np.sqrt(pol_level**2 - dpol_level**2)
        #print("Shape pol_dbias: " + str(pol_dbias.shape))
        SNR_pol = pol_dbias/dpol_level
        SNR_int = I/dI
        save_fits(SNR_int, "SNR_int.fits")
        save_fits(SNR_pol, "SNR_pol.fits")

        # Calculating MonteCarlo Polarization Angle
        I_mc = np.random.normal(I,dI)        
        Q_mc = np.random.normal(Q,dQ)
        U_mc = np.random.normal(U,dU)
        # Calculating MonteCarlo PA and MC Inclination 
        PA_mc = np.random.normal(PA, dPA)
        q_mc  = np.cos(np.radians(np.random.normal(incl, dincl)))
        # Rotated pol Angle
        pol_mc = rotated_polarization_angle(U_mc, Q_mc)        


        #########################
        ### 2- Radial and angle masks - Pitch angle 0 vector array  
        #########################

        # Here we generate an array of projected vectors, that have pitch angle 0 in the galaxy reference frame.        
        angle_mask = create_angle_mask(xsize=image_shape[1], ysize=image_shape[0], q=q_mc, theta=PA_mc,
                                       center=[xcen, ycen], radius=None, pitch=0)
        angle_mask = 360 - angle_mask

        radial_mask = create_radial_mask(xsize=image_shape[1], ysize=image_shape[0], q=q_mc, theta=PA_mc,
                                                center=[xcen, ycen], radius=None)


        #########################
        ### 3- Vector sweeping  
        #########################    
        # Here, put every polarization vector in the clockwise direction. 
        # 1 - Calculate the distance between pitch 0 angle mask and polarization vector
        signed_phi = (angle_mask - pol_mc + 360) % 360
        signed_phi[signed_phi > 180] = 360 - signed_phi[signed_phi > 180]
        # Switch those with angles larger than 90 
        pol_corrected = np.copy(pol_mc)
        pol_corrected[(signed_phi >= 90)] = pol_corrected[(signed_phi >= 90)] - 180
        pol_corrected[(signed_phi <= -90)] = pol_corrected[(signed_phi <= -90)] + 180        
        
        
        
        #########################
        ### 4- Saving arrays for checking 
        #########################
        
        if save_temp:
            save_fits(I_mc, name + "I_MC.fits", header=header)
            save_fits(Q_mc, name + "Q_MC.fits", header=header)
            save_fits(U_mc, name + "U_MC.fits", header=header)
            save_fits(pol_mc, name + "pol_MC.fits", header=header)
            save_fits(angle_mask, name + "angle_mask.fits", header=header)
            save_fits(radial_mask, name + "radial_mask.fits", header=header)
            save_fits(signed_phi, name + "signed_phi.fits", header=header)
            save_fits(pol_corrected, name + "pol_corrected.fits", header=header)


        # After combing all the vectors to the same sense, we can deproject and measure the 
        # magnetic pitch angle. 

        # Now, deproject Polarization corrected map    
        x_image = np.linspace(0, image_shape[0]-1, image_shape[0]) - int(image_shape[0]/2)
        y_image = np.linspace(0, image_shape[1]-1, image_shape[1]) - int(image_shape[1]/2)
        X_image, Y_image = np.meshgrid(y_image,x_image)
    
        U_image = np.cos(np.radians(pol_corrected+90))/np.sqrt(dpol_level)
        V_image = np.sin(np.radians(pol_corrected+90))/np.sqrt(dpol_level)
    
        X_gal = (X_image*np.cos(np.radians(-PA_mc))-Y_image*np.sin(np.radians(-PA_mc)))/q_mc
        Y_gal = (X_image*np.sin(np.radians(-PA_mc))+Y_image*np.cos(np.radians(-PA_mc)))     
        R_gal = np.sqrt(X_gal**2 + Y_gal**2)
    
        U_gal = (U_image*np.cos(np.radians(-PA_mc))-V_image*np.sin(np.radians(-PA_mc)))/q_mc
        V_gal = (U_image*np.sin(np.radians(-PA_mc))+V_image*np.cos(np.radians(-PA_mc)))     
    
    
        if plot_verbose:
            #### Static Figure! #### 
            fig, ax = plt.subplots(figsize=(10,10))
            qax = ax.quiver(X_gal, Y_gal, U_gal, V_gal, alpha=1, scale=50) 
            qax = ax.quiver(X_image, Y_image, U_image, V_image, scale=50, alpha=0.5, color="red")

            plt.gray()
            plt.xlim(np.min(X_gal), np.max(X_gal))
            plt.ylim(np.min(Y_gal), np.max(Y_gal))

            plt.xlabel("X (pixels)")
            plt.ylabel("Y (pixels)")
            plt.title("Deprojected corrected polarization map HAWC+")
            plt.show()
            
            fig, ax = plt.subplots(figsize=(10,10))
            plt.scatter(X_gal, Y_gal, c=np.log10(I_mc), s=20, alpha=0.5)
            plt.gray()

            plt.scatter(X_image, Y_image, c=np.log10(I_mc), s=20, alpha=0.5)
            plt.viridis()
            plt.show()

                
        # Now calculate the pitch angle 0 position angle and make the profile. 
        U_pitch_zero = (X_gal*np.cos(np.radians(-90))-Y_gal*np.sin(np.radians(-90)))
        V_pitch_zero = (X_gal*np.sin(np.radians(-90))+Y_gal*np.cos(np.radians(-90)))     


        #if plot_verbose:
        #    fig, ax = plt.subplots(figsize=(20,20))
        #    qax = ax.quiver(X_gal, Y_gal, U_gal, V_gal, alpha=0.5, scale=50, label="Polarization map") 
        #    qax = ax.quiver(X_gal, Y_gal, U_pitch_zero, V_pitch_zero, alpha=0.5, color="blue", scale=1000, label="Pitch angle zero lines") 
        #    plt.xlabel("X (pixels)")
        #    plt.ylabel("Y (pixels)")
        #    plt.title("Comparing pitch angle zero lines with B field") 
        #    plt.legend()
        #    plt.show()
            
        pitch_angle = np.degrees(np.arctan2(U_pitch_zero, V_pitch_zero) - np.arctan2(U_gal, V_gal))
        
        while len(np.where(pitch_angle > 90)[0]) > 0:
            pitch_angle[pitch_angle > 90] = pitch_angle[pitch_angle > 90] - 180

        while len(np.where(pitch_angle < -90)[0]) > 0:    
            pitch_angle[pitch_angle < -90] = pitch_angle[pitch_angle < -90] + 180

        
        pitch_angle_quality = np.copy(pitch_angle)
        pitch_angle_quality[np.where((SNR_int < SNR_int_limit) & (SNR_pol < SNR_pol_limit))] = np.nan
        save_fits(pitch_angle_quality, name + "pitch_angle.fits", header=header)  
        
        #########################
        ### 5- Generating profile of residual angle (pitch angle profile) 
        #########################       
        if not isinstance(bin_limits, (list,np.ndarray)):
            if bin_limits == None:
                bin_limits = np.linspace(0, np.max(R_gal[~np.isnan(pitch_angle_quality)]), nbins+1)
        pitch_angle_MC = []
        R_gal_MC = []
    
        pitch_angle_single = pitch_angle[np.where((SNR_int >= SNR_int_limit) & (SNR_pol >= SNR_pol_limit))]

        return([pitch_angle_single, pitch_angle_quality, R_gal])


def magnetic_pitch_angle(xcen, ycen, I, dI, Q, dQ, U, dU, PA, dPA, incl, dincl, nsimul=100,
                         nbins=10, plot_verbose=False, SNR_int_limit=5, SNR_pol_limit=1, name="default_", header=None, bin_limits=None, save_temp=False, force_bootmedian=False):
    #####################################################
    # ### Magnetic pitch angle ###
    # Alejandro Borlaff - a.s.borlaff@nasa.gov / asborlaff@gmail.com
    # 
    # Objective: Calculate the magnetic pitch angle of a galaxy observed at position angle
    #            PA and inclination incl, using a set of arrays containing the Stokes parameters (I, Q, U).  
    #
    # Input arrays: Intensity + Error, Stokes Q + Error, Stokes U + Error. 
    # Input numeric: PA + Error, incl + Error, nsimul, nbins
    # Input bool: plot_verbose
    # 
    # Output: A two element list containing:
    #         median_curve (Pandas DataFrame): Median pitch angle curve (R_bin + errors vs. pitch angle + errors) 
    #         pitch_angle_curves: A list of dataframes with the pitch angle curve of each MonteCarlo simulation (N = nsimuls)
    #-----------------------------------------
    # 
    #  v.1.0 = First working version, release to Slite 
    # 
    #-----------------------------------------
    #  To be done:
    #  - Input control: All arrays must have same shape
    #  - Externalize quiver plot 
    #  - Check all plots save, close and clean
    #  - Recheck uncertainties combination at the end of MC 
    # 
    ####################################################
    
    # Clean files to be written: 
    #os.system(name + "pitch_angle*.fits")  
    
    nsimul_boot=100
    # If bin_limits is not None, then replace nbins
    if isinstance(bin_limits, (list, np.ndarray)):
        nbins = len(bin_limits)-1
     
    # Calculate the polarization level and the error.
    pol_level = 100*np.sqrt((Q/I)**2 + (U/I)**2)
 
    dpol_level_A = ((Q*dQ)**2 + (U*dU)**2)/(Q**2+U**2)
    dpol_level_B = ((Q/I)**2 + (U/I)**2)*dI**2
    dpol_level = np.abs(100*np.sqrt(dpol_level_A + dpol_level_B)/I)

    # dpol_level = np.sqrt(())
    
    save_fits(pol_level, name + "pol_level.fits", header=header)
    save_fits(dpol_level, name + "dpol_level.fits", header=header)
    
    save_fits(pol_level/dpol_level, name + "SNR_pol.fits", header=header)
    save_fits(I/dI, name + "SNR_int.fits", header=header)
    

    
    #########################
    ### 1- Monte Carlo generation 
    #########################
    # Debiased pol array
    pol_level = 100*np.sqrt((Q/I)**2 + (U/I)**2)
    dpol_level_A = ((Q*dQ)**2 + (U*dU)**2)/(Q**2+U**2)
    dpol_level_B = ((Q/I)**2 + (U/I)**2)*dI**2
    dpol_level = np.abs(100*np.sqrt(dpol_level_A + dpol_level_B)/I)
    pol_dbias = np.sqrt(pol_level**2 - dpol_level**2)
    save_fits(pol_dbias, name + "pol_dbias.fits", header=header)
    SNR_pol = pol_dbias/dpol_level
    SNR_int = I/dI
    ###########################################
    
    pol_90_rotated = rotated_polarization_angle(U, Q)
    pol_90_rotated[np.where((SNR_int < SNR_int_limit) & (SNR_pol < SNR_pol_limit))] = np.nan
    save_fits(pol_90_rotated, name + "pol90.fits", header=header)
    
    
    # To be done: Check is Q, dQ, U, dU are all of the same shape 
    pitch_angle_array = []
    # Calculate Polarization angle
    
    pitch_angle_cube = np.zeros((nsimul, I.shape[0], I.shape[1])) 
    R_gal_cube = np.zeros((nsimul, I.shape[0], I.shape[1]))    
    
    for i in tqdm(range(nsimul)):
    # xcen, ycen, I, dI, Q, dQ, U, dU, pol_level, dpol_level, PA, dPA, incl, dincl, save_temp=False, SNR_limit=100
        pitch_angle_single, pitch_angle_quality, R_gal = single_magnetic_pitch_angle(xcen=xcen, ycen=ycen, I=I, dI=dI, Q=Q, dQ=dQ, U=U, dU=dU, PA=PA, dPA=dPA, incl=incl, dincl=dincl, 
                                                                           pol_level=pol_level, dpol_level=dpol_level, save_temp=save_temp, nbins=nbins, nsimul=nsimul, SNR_int_limit=SNR_int_limit,
                                                                           SNR_pol_limit=SNR_pol_limit, plot_verbose=plot_verbose, name=name, header=header, bin_limits=bin_limits)
        #os.system("mv " + name + "pitch_angle.fits " + name + "pitch_angle_n" + str(i).zfill(5) + ".fits ")      
                        
        pitch_angle_cube[i,:,:] =  pitch_angle_quality  
        R_gal_cube[i,:,:] =  R_gal                
        pitch_angle_array.append(pitch_angle_single)
            
    hdu1 = fits.PrimaryHDU(pitch_angle_cube)
    hdu2 = fits.ImageHDU(R_gal_cube)

    new_hdul = fits.HDUList([hdu1, hdu2])
    if header is not None:
        new_hdul[0].header = header
        #new_hdul[1].header = header

    new_hdul.verify("silentfix")
    new_hdul.writeto(name + "pitch_angle_cube.fits", overwrite=True)
    
    # Now we have a list of dataframes with the R and pitch (+errors). 
    # We need to measure the median value and the quantile, taking into account the errors. 

    R = np.zeros(nbins)*np.nan
    R_s1up = np.zeros(nbins)*np.nan
    R_s1down = np.zeros(nbins)*np.nan
    R_s2up = np.zeros(nbins)*np.nan
    R_s2down = np.zeros(nbins)*np.nan
    R_s3up = np.zeros(nbins)*np.nan
    R_s3down = np.zeros(nbins)*np.nan
    pitch = np.zeros(nbins)*np.nan
    pitch_s1up = np.zeros(nbins)*np.nan
    pitch_s1down = np.zeros(nbins)*np.nan
    pitch_s2up = np.zeros(nbins)*np.nan
    pitch_s2down = np.zeros(nbins)*np.nan
    pitch_s3up = np.zeros(nbins)*np.nan
    pitch_s3down = np.zeros(nbins)*np.nan
    
    #########################
    ### 5- Generating profile of residual angle (pitch angle profile) 
    #########################       
    if not isinstance(bin_limits, (list,np.ndarray)):
        if bin_limits == None:
            bin_limits = np.linspace(0, np.max(R_gal[~np.isnan(pitch_angle_quality)]), nbins+1)

    pitch_angle_boot_list = []
    print("Simulations done, generating profile from cube")
    for i in tqdm(range(len(bin_limits)-1)):
        pitch_angle_boot = np.zeros(nsimul)
        pitch_angle_boot[:] = np.nan
        R_gal_boot = np.zeros(nsimul)
        R_gal_boot[:] = np.nan


        for j in range(nsimul):       
            R_gal = R_gal_cube[j,:,:]
            pitch_angle = pitch_angle_cube[j,:,:]
            indexes = np.where((R_gal > bin_limits[i]) & (R_gal <= bin_limits[i+1]))
            pitch_angle_sample = pitch_angle[indexes] 
            R_gal_sample = R_gal[indexes] 
            weights_sample = I[indexes]
            
            if force_bootmedian:
                pitch_angle_boot[j] = ab.bootmedian.bootmedian(sample_input = pitch_angle_sample, nsimul = nsimul_boot, mode="angles", weights=weights_sample)["median"]
                R_gal_boot[j] = bn.nanmedian(np.array(R_gal_sample)) #ab.bootmedian.bootmedian(sample_input = np.array(R_gal_sample), nsimul = nsimul_boot, mode="median")["median"]
                               
            else:
                pitch_angle_boot[j] = median_angle(pitch_angle_sample) #ab.bootmedian.bootmedian(sample_input = pitch_angle_sample, nsimul = nsimul_boot, mode="angles")["median"]
                R_gal_boot[j] = bn.nanmedian(np.array(R_gal_sample)) #ab.bootmedian.bootmedian(sample_input = np.array(R_gal_sample), nsimul = nsimul_boot, mode="median")["median"]


        pitch_angle_boot_list.append(pitch_angle_boot)                                                  
        R_gal_median = bn.nanmedian(R_gal_boot) #ab.bootmedian.bootmedian(sample_input = R_gal_boot, nsimul = nsimul_boot, mode="median")
        pitch_angle_median = bn.nanmedian(pitch_angle_boot) #ab.bootmedian.bootmedian(sample_input = pitch_angle_boot, nsimul = nsimul_boot, mode="median")
       
        R[i] = R_gal_median
        R_s1up[i] = np.nanpercentile(R_gal_boot, s1_up_q*100)
        R_s1down[i] = np.nanpercentile(R_gal_boot, s1_down_q*100)
        R_s2up[i] = np.nanpercentile(R_gal_boot, s2_up_q*100)
        R_s2down[i] = np.nanpercentile(R_gal_boot, s2_down_q*100)
        R_s3up[i] = np.nanpercentile(R_gal_boot, s3_up_q*100)
        R_s3down[i] = np.nanpercentile(R_gal_boot, s3_down_q*100)
        
        pitch[i] = pitch_angle_median
        pitch_s1up[i] = np.nanpercentile(pitch_angle_boot, s1_up_q*100)
        pitch_s1down[i] = np.nanpercentile(pitch_angle_boot, s1_down_q*100)
        pitch_s2up[i] = np.nanpercentile(pitch_angle_boot, s2_up_q*100)
        pitch_s2down[i] = np.nanpercentile(pitch_angle_boot, s2_down_q*100)
        pitch_s3up[i] = np.nanpercentile(pitch_angle_boot, s3_up_q*100)
        pitch_s3down[i] = np.nanpercentile(pitch_angle_boot, s3_down_q*100)
        

    with open(name + "_pitch_angle_pdd.csv", "wb") as fp:   #Pickling
        pickle.dump(pitch_angle_boot_list, fp)
           
           
    median_curve = pd.DataFrame({"R":R, "R_s1up": R_s1up, "R_s1down": R_s1down,
                                 "R_s2up": R_s2up, "R_s2down": R_s2down,
                                 "pitch": pitch, "pitch_s1up": pitch_s1up, "pitch_s1down": pitch_s1down,
                                 "pitch_s2up": pitch_s2up, "pitch_s2down": pitch_s2down})
    


            
    median_curve.to_csv(name + "profile.csv")
    # Plot the polatization angles and the model 
    # def generate_pitch_model(pitch_profile, shape, header, ext, xcen, ycen, PA, incl, output):
    generate_pitch_model(pitch_profile=median_curve, shape=I.shape, header=header, xcen=xcen, ycen=ycen, PA=PA, incl=incl, output=name + "pitch_model.fits")
    print("Pitch angle model generated: " + name + "pitch_model.fits")
    print("Pitch angle profile generated: " + name + "profile.csv")
    
    
    return([median_curve, np.median(pitch_angle_cube, axis=0)])


