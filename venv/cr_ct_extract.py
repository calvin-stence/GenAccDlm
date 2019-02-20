import csv
import glob2
import time
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patheffects as path_effects
from matplotlib.patches import Ellipse
import numpy as np
import os
import re
import shutil
import pandas as pd
import scipy.interpolate
import scipy.ndimage
import importlib

def main():
    paths = ['SF PVA', 'FIN PVA', 'SF TAC', 'FIN TAC']
    with PdfPages('tac_curves_sf_fin.pdf') as pdf:

        files = []
        for path in paths:
            fig = plt.figure('curves')

            for file in glob2.glob('test_input/Multi Thickness Surfacing Test/structured_data/*'+path+'*/**/*.mcr'):
                   #center_thick = 2.23
                front_transmission_data_measure = open_cr_ct(file)
                #back_transmission_data_measure = open_cr_ct("test_input/tac_deformation/Onbit TAC DLM Measures/first_polar_test_tac.mcr")
                lens_61061671_5_front = front_transmission_data_measure.matrix_data.get('PosZ')# - transmission_data_theory.matrix_data.get('Dpt')
                #lens_61061671_5_back = back_transmission_data_measure.matrix_data.get('PosZ')# - transmission_data_theory.matrix_data.get('Dpt')
                #lens_thickness = center_thick + abs(lens_61061671_5_back) - abs(lens_61061671_5_front)



                front = FrontCurvePlots(lens_61061671_5_front)
                #back = FrontCurvePlots(lens_61061671_5_back)


                plt.plot(front.x, front.radii_of_curvature_x)
                plt.plot(front.y_90,front.radii_of_curvature_x_90)
                files.append(os.path.basename(file)[0:7])
            plt.title('Front Curve by Job Number - '+path)
            plt.legend(files,loc='best')
            plt.show()
            plt.close(fig)

        #orma_index = 1.498
#        #thickness_x = thickness.x
        #thickness_z = thickness.zi
        #front_x = front.x#
        #front_radius = abs(front.radii_of_curvature_x)/1000
        #back_x = back.x
        #back_radius = abs(back.radii_of_curvature_x)/1000

    # plt.figure(44)
    # plt.subplot(131)
    # plt.imshow(lens_61061671_5_back)
    # plt.colorbar()
    # plt.subplot(132)
    # plt.imshow(lens_61061671_5_front)
    # plt.colorbar()
    # plt.subplot(133)

    # plt.imshow(lens_thickness)
    # plt.colorbar()
    # plt.show()
    # plt.figure(5)
    # plt.contourf(lens_61061671_5_back,cmap='nipy_spectral')
    # plt.colorbar(0)
    # plt.show()
    # thickness = FrontCurvePlots(lens_thickness)
    #D1 = (orma_index-1)/front_radius
    #D2 = (orma_index-1)/back_radius
    #Dn = D1-D2
    #De = Dn[2:24] + thickness_z[2:24]/orma_index*D1[2:24]**2

    #plt.figure(2)
    #plt.plot(front.x,D1,front.x,D2,front.x,Dn)
    #
    #plt.plot(front.x[2:24],De)
    #plt.legend(['D1', 'D2', 'Dn','De'])
    #plt.figure(3)
    #plt.plot(thickness_x,thickness_z)

    plt.show()
class FrontCurvePlots:
    def __init__(self, data, plots=None):
        input_matrix = data
        x0, y0 = 5, 20
        x1, y1, = 35, 20
        x0_90, y0_90 = 20, 5
        x1_90, y1_90 = 20, 35
        # Extract the values along the line, using cubic interpolation
        self.zi, self.x, self.y = array_transect(x0, y0, x1, y1, input_matrix)
        self.zi_90, self.x_90, self.y_90 = array_transect(x0_90, y0_90, x1_90, y1_90, input_matrix)
        self.radii_of_curvature_x = curvature_splines(self.x, self.zi)
        self.radii_of_curvature_x_90 = curvature_splines(self.y_90, self.zi_90)
        if plots == 'on':
            fig, axes = plt.subplots(nrows=3, ncols=1)
            axes[0][0].contourf(input_matrix,cmap='nipy_spectral')
            axes[0][0].plot([x0, x1], [y0, y1], 'ro-')
            axes[0][0].plot([x0_90, x1_90], [y0_90, y1_90], 'bo-')
            axes[0][0].axis('image')
            axes[1][0].plot(self.x,self.zi)
            axes[1][0].plot(self.y_90,self.zi_90)
            axes[2][0].plot(self.x[np.logical_not(np.isnan(zi))], curvature_splines(x,zi))
            #axes[2][0].plot(y_90, zi_90)
            plt.show()

def dlm_transect():
    x0, y0 = 5, 20
    x1, y1, = 35, 20
    x0_90, y0_90 = 20, 5
    x1_90, y1_90 = 20, 35
    # Extract the values along the line, using cubic interpolation
    zi, x, y = array_transect(x0, y0, x1, y1, output_data)
    zi_90, x_90, y_90 = array_transect(x0_90, y0_90, x1_90, y1_90, output_data)
    return zi, x, zi_90, x_90

def array_transect(x0,y0,x1,y1,z):
    length = int(np.hypot(x1 - x0, y1 - y0))
    x, y = np.linspace(x0, x1, length), np.linspace(y0, y1, length)
    zi = z[x.astype(np.int), y.astype(np.int)]
    x = x[np.logical_not(np.isnan(zi))]
    y = y[np.logical_not(np.isnan(zi))]
    zi = zi[np.logical_not(np.isnan(zi))]
    return zi, x, y

class open_cr_ct():
    def __init__(self, file):
        self.file = file
        with open(self.file) as csvfile:
            file_data = list(csv.reader(csvfile, delimiter='\t', lineterminator='\n'))
            self.x_dim = int(file_data[13][1])
            self.y_dim = int(file_data[13][2])
            self.measure_data = file_data[15:len(file_data)]
            count = 0
            self.matrix_data = {}
            blank_matrix = np.zeros((self.x_dim,self.y_dim))
            for row in self.measure_data:
                if count == 0:
                    for item in row:
                        if item == 'NotUse':
                            continue
                        self.matrix_data.update({item: blank_matrix})
                    count +=1
                    continue
                x_index = int(float(row[0]))+20
                y_index = int(float(row[1]))+20
                for index, item in enumerate(row):
                    current_key = self.measure_data[0][index]
                    if current_key in self.matrix_data:
                        if float(item) > 99990:
                            item = np.nan
                        current_matrix = np.copy(self.matrix_data.get(current_key))
                        current_matrix[y_index,x_index] = item
                        self.matrix_data.update({current_key: current_matrix})
                count += 1

def curvature_splines(x, y=None, error=0.1):
    """Calculate the signed curvature of a 2D curve at each point
    using interpolating splines.
    Parameters
    ----------
    x,y: numpy.array(dtype=float) shape (n_points, )
         or
         y=None and
         x is a numpy.array(dtype=complex) shape (n_points, )
         In the second case the curve is represented as a np.array
         of complex numbers.
    error : float
        The admisible error when interpolating the splines
    Returns
    -------
    curvature: numpy.array shape (n_points, )
    Note: This is 2-3x slower (1.8 ms for 2000 points) than `curvature_gradient`
    but more accurate, especially at the borders.
    """

    # handle list of complex case
    if y is None:
        x, y = x.real, x.imag
    t = np.arange(x.shape[0])
    std = error * np.ones_like(x)

    fx = scipy.interpolate.UnivariateSpline(t, x, k=4, w=1 / np.sqrt(std))
    fy = scipy.interpolate.UnivariateSpline(t, y, k=4, w=1 / np.sqrt(std))
    #plt.figure(222)
    #plt.plot(fx(x),fy(x))
    #plt.plot(x,y)
    #plt.show()
    #plt.close()
    x_first_derivative = fx.derivative(1)(t)
    x_second_derivative = fx.derivative(2)(t)
    y_first_dervative = fy.derivative(1)(t)
    y_second_derivative = fy.derivative(2)(t)
    curvature = (x_first_derivative*y_second_derivative - y_first_dervative*x_second_derivative) / np.power(x_first_derivative**2 + y_first_dervative**2, 1.5)
    return 1/curvature

if __name__ == "__main__":
    main()
