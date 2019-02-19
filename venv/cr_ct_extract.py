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
from scipy import odr

def main():
    #transmission_data_measure = open_cr_ct("Z:\\PRIME_26467_FT1_VERD1_DBP.mct")
    #transmission_data_theory = open_cr_ct("Z:\\PRIME_26467_FT1_VERD1_DBP.rct")
    transmission_data_measure = open_cr_ct("test_input/tac_deformation/Onbit TAC DLM Measures/first_polar_test_tac.mcr")
    #transmission_data_theory = open_cr_ct("RAW_DATA_DUMP\\ETO_26653_FT1_VERD1_RTC.rcr")
    #output_data = np.sqrt(np.square(mcr_data.matrix_data.get('MinCurvX'))+np.square(mcr_data.matrix_data.get('MinCurvY'))+np.square(mcr_data.matrix_data.get('MinCurvZ')))
    output_data = transmission_data_measure.matrix_data.get('PosZ')# - transmission_data_theory.matrix_data.get('Dpt')
    #output_data = mcr_data_theory.matrix_data.get('DeformInclH')
    x0, y0 = 5, 20
    x1, y1, = 35, 20
    x0_90, y0_90 = 20, 5
    x1_90, y1_90 = 20, 35
    # Extract the values along the line, using cubic interpolation
    zi, x, y = array_transect(x0, y0, x1, y1, output_data)
    zi_90, x_90, y_90 = array_transect(x0_90, y0_90, x1_90, y1_90, output_data)
    fig, axes = plt.subplots(nrows=2,ncols=2)
    axes[0][0].contourf(output_data,cmap='nipy_spectral')
    axes[0][0].plot([x0, x1], [y0, y1], 'ro-')
    axes[0][0].plot([x0_90, x1_90], [y0_90, y1_90], 'bo-')
    axes[0][0].axis('image')
    axes[1][0].plot(x,zi)
    axes[1][0].plot(y_90,zi_90)
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

if __name__ == "__main__":
    main()
