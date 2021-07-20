# Magnetic field analysis tools for SOFIA/HAWC+ M51

## Summary
This repository contains the analysis tools used in the SOFIA Legacy Program publication "Extragalactic Magnetism with SOFIA (Legacy Program) I: The magnetic field in the multi-phase interstellar medium of M51", which is available on ArXiv on the following webpage: https://arxiv.org/abs/2105.09315. The tools contained in sofia_toolbox.py contain most of the software developed for the analysis of the far-infrared polarization observations of the M51 galaxy, plus the ancillary radio polarization observations from Fletcher et al. 2011 (https://ui.adsabs.harvard.edu/abs/2011MNRAS.412.2396F/abstract). 

![M51 HAWC+ Magnetic Pitch angle](https://raw.githubusercontent.com/Borlaff/M51_HAWC/main/HAWC_full__pitch_model_mode_full.png)


## Functions

### plot_profile(profile, color, linestyle, linewidth, marker, label):
This function plots the magnetic pitch angle profile in an existing matplotlib figure using the profile objects generated with magnetic_pitch_angle function. 

### magnetic_pitch_angle_profile_plot(output_magnetic_pitch_angle_profile):
This is an auxiliary function to generate plots with the full output from magnetic_pitch_angle function. 

### measure_median_pitch_angle(pitch_angle_array):
This function uses the datacubes generated by magnetic_pitch_angle function to estimate the median pitch angle. Those datacubes contain the Montecarlo simulations used to estimate the errorbars for each pixel. 

Input: pitch_angle_array: A datacube generated by magnetic_pitch_angle containing the MonteCarlo simulations of the pitch angle arrays. 

Output: (Dict) 
- median_pitch_angle: Median pitch angle value of the array. 

- e95_down: 2.5% percentile of the median pitch angle probability distribution

- e95_up: 97.5% percentile of the median pitch angle probability distribution.  

### apply_mask(mode, mask_fits, header, I, dI, Q, dQ, U, dU):

This function applies the morphological arm / interarm mask to the I, dI, Q, dQ, U, and dU Stokes arrays. Defined to be used before inputing the Stokes arrays to magnetic_pitch_angle. 

### generate_pitch_model(pitch_profile, shape, header, xcen, ycen, PA, incl, output):

Given a certain pitch angle profile from the magnetic_pitch_angle function (input: pitch_profile) it will return a pitch angle array with dimensions defined by the input parameter "shape (x,y)" where each pixel has the expected value from its azimuthal pitch angle profile. 
xcen and ycen are the central coordinates of the galaxy model in pixels 
PA is the position angle, measured counter-clockwise from the North direction (degrees)
incl is the inclination of the galactic disk 
output is a string, which will be used as the name of the fits file to store the new pitch angle array. 

### save_fits(array, name, header=None):
A function to save arrays in new fits files. 

Array: The input array to save

name: Name of the new fits file

header: Header of the new fits file


### plot_pitch_model(I, pol_obs, pitch_model, SNR_int, SNR_pol, SNRi_cut = 10.0, SNRp_cut = 3.0, step=4, scalevec = 2.5, header=None, save_fig="plot_pitch_model.pdf", vmin=None, vmax=None, alpha_model=1 pol_fraction=None, title=" ", colorscale="viridis", color_model="red", color_obs="black", recenter=None, figsize=6.5, colorbar_label=r'Intensity (Jy arcsec$^{-2}$)')
                     
This is a function to generate 2D images with the overplotted polarization vectors. 

I : The intensity array for the background

pol_obs: The array with the position angles to be plotted. 

Pitch_model: The array with a secondary set of position angles to the plotted. 

SNR_int: Signal-to-noise ratio array for the intensity

SNR_pol: Signal-to-noise ratio array for the polarization

SNRi_cut: Limit for the intensity Signal to noise ratio

SNRp_cut: Limit for the polarization Signal to noise ratio 

Step: Plotting density factor. If 1, all vectors are plotted. Derive a vector only from every ‘step’ pixels. You will normally want this to be >1 to get sensible 

vector spacing. See https://aplpy.readthedocs.io/en/stable/api/aplpy.FITSFigure.html show_vectors function. 

header: Header of the fits files containing a valid WCS

save_fig: Name of the output figure file.

vmin: Minimum limit for the background intensity image color scale

vmax: Maximum limit for the background intensity image color scale

alpha_model: Transparency control for the secondary pitch angle model vectors

pol_fraction (testing): Array containing polarization % measurements, to be used as scaling factor for the lengths of the vectors.

title: (string) Title of the plot.

colorscale: Matplotlib colormap name. See https://matplotlib.org/stable/tutorials/colors/colormaps.html

color_model: Color for the model vectors (secondary). 

color_obs: Color for the observational vectors (primary).

recenter: Input parameters for the recenter function -  gc.recenter(x=recenter[0], y=recenter[1], width=recenter[2], height=recenter[3]). See https://aplpy.readthedocs.io/en/stable/api/aplpy.FITSFigure.html#aplpy.FITSFigure.recenter

figsize: Figure size. See https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.figure.html

colorbar_label: String. Label for the colorbar of the background intensity array. 


### create_radial_mask(xsize, ysize, q=1, theta=0, center=None, radius=None)
This function generates an array where each pixel contains its own radius, defined from the center as defined in the input. The dimensions of the array are defined in xsize and ysize. q is minor/major axis ratio of the ellipses (to take into account the inclination of the galaxy), theta is the position angle of the major axis, measured as counter-clock wise from the North direction.

### create_angle_mask(xsize, ysize, q, theta, center=None, radius=None, pitch=90):
This function generates an array where each pixel contains the position angle of an spiral polarization field array with pitch angle equal as the input. pitch=90 generates a radial field, with vectors pointing outwards from the center. pitch=0 generates a pure azimuthal field, taking into account the position angle and ellipticity of the disk. The dimensions of the array are defined in xsize and ysize. q is minor/major axis ratio of the ellipses (to take into account the inclination of the galaxy), theta is the position angle of the major axis, measured as counter-clock wise from the North direction.

### bootstrap_resample(X, weights=False, seed=None):
This function generates a random resampling with replacement (see https://en.wikipedia.org/wiki/Bootstrapping_(statistics)) with weights as defined in the input. Seed is the random generation python seed, useful for parallel processing.  

### median_angle(input_sample):
This function calculates the median of a sample of angles that are defined periodic between (-90, +90) degrees. 

input: An array with a sample of angles
output: pi periodic median of the input sample

### bootmedian_angles(input_sample, nsimul, weights=False):
Bootstrapping version of the median_angle function. This function calculates the median of a sample of angles that are defined periodic between (-90, +90) degrees. 

input: An array with a sample of angles
output: pi periodic median of the input sample


### rotated_polarization_angle(U, Q):
This function calculates the 90º rotated polarization angle (B-field) from the two Stokes arrays (U,Q). 


### inv_rotated_polarization_angle(pol90):
This function calculates the two Stokes arrays (U,Q) from the 90º rotated polarization angle (B-field).  


### magnetic_pitch_angle(xcen, ycen, I, dI, Q, dQ, U, dU, PA, dPA, incl, dincl, nsimul=100, nbins=10, plot_verbose=False, SNR_int_limit=5, SNR_pol_limit=1, name="default_", header=None, bin_limits=None, save_temp=False, force_bootmedian=False)

Magnetic_pitch_angle: A wrapper-function to single_magnetic_pitch_angle. 

Input: (see  single_magnetic_pitch_angle) 

Output: 
- Files: 
1 - name + "pitch_model.fits" : This file contains an array with the same shape than the input I,Q,U, that contains the pitch angle for every pixel, according to the median azimuthal model generated from the pitch angle profile.
2 - name + "profile.csv": This file contains a Pandas dataframe with the following columns: 
      - R, R_s1up, R_s1down, R_s2up, R_s2down: Radius of the bin, plus 1sigma and 2sigma upper and lower limits of its probability distribution.  
       - pitch, pitch_s1up, pitch_s1down, pitch_s2up, pitch_s2down. Median pitch angle of the radial bin, plus 1sigma and 2sigma upper and lower limits of its probability distribution.
       
3 - name + "pitch_angle_cube.fits": This fits file contains two datacubes. In the first extension, it contains a datacube with the same (x, y) dimensions than the input I,Q,U frames, and with a z dimension as large as nsimul. This datacube represents the variation of the 2 dimensional distribution of the pitch angle with the uncertainty of the input parameters. In the second dimension, it contains the Montecarlo simulations of the radial mask with the uncertainty in PA and incl. 

- Command line: 
A two element list that contains:
1 - The profile pandas dataframe (same as name + "profile.csv")
2 - pitch_angle_cube (same as name + "pitch_angle_cube.fits")
   
    
    return([median_curve, np.median(pitch_angle_cube, axis=0)])

### single_magnetic_pitch_angle(xcen, ycen, I, dI, Q, dQ, U, dU, pol_level, dpol_level, PA, dPA, incl, dincl, nbins, nsimul, save_temp=False, SNR_int_limit=5, SNR_pol_limit=1, plot_verbose=False, name="default_", header=None, bin_limits=None, force_bootmedian=False):
 
Objective: Calculate the magnetic pitch angle of a galaxy observed at position angle, PA and inclination incl, using a set of arrays containing the Stokes parameters (I, Q, U).  

Input: 

- Center of the galaxy in pixels (xcen, ycen)

- Total intensity + Uncertainty (I, dI)

- Stokes Q + Uncertainty (Q, dQ)

- Stokes U + Uncertainty (U, dU). 

- pol_level: Debiased polarization % array

- dpol_level: Debiased polarization % uncertainty 

- PA: Position angle (degrees)

- dPA: Uncertainty in position angle (degrees)

- incl: Inclination angle (degrees, 0: face-on, 90: edge-on)

- dincl: Uncertainty in inclination angle (degrees)

- nbins: Number of radial bins for the pitch angle profile (pixels)

- nsimul: Number of MonteCarlo simulations for the analysis

- save_temp: Bool flag - True if you want to save the temporary files. 

- SNR_int_limit: Minimum limit for the signal to noise ratio in intensity. 

- SNR_pol_limit: Minimum limit for the signal to noise ratio in polarization. 

- plot_verbose: True if you want to see some extra plots. 

- name: String, name for the output files header.

- bin_limits: Optional, default None: Add an array to define a user-defined limits for the radial bins. 

- force_bootmedian: Optical, default: False. Force bootstrapping calculation for the median value of the pitch angle inside the radial bins. Warning, setting this parameter to True might lead to very long computation times. 



