import csv
import glob2
import matplotlib.colors as colors
import time
import matplotlib.pyplot as plt
import numpy as np
import os
import re
import shutil
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patheffects as path_effects
import scipy.misc
import scipy.ndimage
from scipy.interpolate import interp1d
import copy


def test():
    pmf_file = glob2.glob('.PMF')[0]
    pmf_obj = PmfPowermapsGet(pmf_file, figures_to_generate=['RTCT', 'RTDT', 'RTCE', 'RTDE'])
    figure_index = 0
    plt.figure('test', figsize=(12, 25))
    fig, axs = plt.subplots(nrows=2, ncols=4)
    for fig_ids in pmf_obj.figures_to_generate:
        plt.sca(axs[0][figure_index])
        pmf_obj.visualize_dlm_pmf(fig_ids)
        x0, y0 = 5, 20
        x1, y1, = 35, 20
        x0_90, y0_90 = 20, 5
        x1_90, y1_90 = 20, 35
        # Extract the values along the line, using cubic interpolation
        output_data = pmf_obj.powermaps.get(fig_ids)
        output_data[output_data > 9999] = np.nan
        zi, x, y = array_transect(x0, y0, x1, y1, output_data)
        zi_90, x_90, y_90 = array_transect(x0_90, y0_90, x1_90, y1_90, output_data)
        axs[0][figure_index].plot([x0, x1], [y0, y1], 'ro-')
        axs[0][0].plot([x0_90 - 40, x1_90 - 40], [y0_90 - 40, y1_90 - 40], 'bo-')
        axs[0][0].axis('image')
        axs[1][figure_index].plot(x, zi)
        axs[1][figure_index].plot(y_90, zi_90)
        figure_index += 1
    plt.show()

def test_compare_powermaps():
    pmf_obj1 = PmfPowermapsGet('test_input/tac_deformation/61064671_B200_Rx-8_24_unsurfaced.PMF')
    pmf_obj2 = PmfPowermapsGet('test_input/tac_deformation/61064671_B200_Rx-8_24_surfaced.PMF')
    pmf_obj_test = compare_pmf(pmf_obj1,pmf_obj2)
    pmf_obj_test.visualize_dlm_pmf('RTDE', v_max=.25, v_min=-.25)
    plt.show()


class PmfId:
    def __init__(self, powermap_type):
        self.eye = powermap_type[0]
        self.front_or_through_measure = powermap_type[1]  # error value, measure value, or refernce value
        self.power_quantity = powermap_type[2]  # cylinder or spherical equivalent diopter
        self.measured_power_type = powermap_type[3]  # reflection or transmission
        self.eye_dict = {'R': 'Right',
                         'L': 'Left'}
        self.front_or_through_measure_dict = {'F': 'Front Reflection',
                                              'T': 'Transmission'}
        self.power_quantity_dict = {'A': 'Axis Angle',
                                    'C': 'Cylinder',
                                    'D': 'Diopter'}
        self.measured_power_type_dict = {'T': 'Reference',
                                         'M': 'Measure',
                                         'E': 'Error'}

        self.pmf_id_minimal = self.power_quantity_dict.get(self.power_quantity) + ' ' + self.measured_power_type_dict.get(self.measured_power_type) + ' ' + self.front_or_through_measure_dict.get(self.front_or_through_measure)
        self.pmf_id_verbose = self.eye_dict.get(self.eye) + ' ' + self.power_quantity_dict.get(self.power_quantity) + ' ' + self.front_or_through_measure_dict.get(self.front_or_through_measure) + ', ' + self.measured_power_type_dict.get(self.measured_power_type)
        self.pmf_id_debug = powermap_type + '\n' + self.pmf_id_verbose

def array_transect(x0, y0, x1, y1, z, smooth=None):
    """

    :type smooth: optional, 'cubic' for smoothing
    """
    length = int(np.hypot(x1 - x0, y1 - y0))
    x, y = np.linspace(x0, x1, length), np.linspace(y0, y1, length)
    coarse_x = x.astype(np.int)
    coarse_y = y.astype(np.int)

    #zi = scipy.ndimage.map_coordinates(np.transpose(z), np.vstack((x, y)))
    z_vals = z[coarse_x, coarse_y]
    #length_vector_coarse = length_vector.astype(np.int)
    nonan_z_vals = []
    if max(coarse_x)-min(coarse_x)>1:
        interp_x = coarse_x
    else:
        interp_x = coarse_y
    nonan_x_vals = interp_x[np.logical_not(np.isnan(z_vals))]
    nonan_z_vals = z_vals[np.logical_not(np.isnan(z_vals))]
    length_vector = np.linspace(min(nonan_x_vals)*1.05, max(nonan_x_vals)*.95, num=200, endpoint=True)
    #for index, item in enumerate(z_vals):
    #    if item != nan:
    #        nonan_x_vals.append(coarse_x[index])
    #        nonan_z_vals.append(z_vals[index])
    if smooth is not None:
        try:
            spline_data = interp1d(nonan_x_vals, nonan_z_vals, kind='cubic')
            zi = spline_data(length_vector)
        except ValueError:
            zi = z_vals
            print('Interpolation values set to nearest!\nThere was a problem fitting a spline to the data--perhaps the data is missing?')
            return zi, x, y
    else:
        zi = z_vals
    return zi, length_vector, length_vector

class PmfPowermapsGet():
    def __init__(self, file, figures_to_generate=[],state=None):
        self.file = file
        self.lens_id_search = re.search(r'(\d+)_(\w\d+)_(\w+-?\d+)_(\d+)', os.path.basename(file))
        self.surfacing_status_search = re.search(r'(_\w*surfaced)', os.path.basename(file))
        self.state=state
        if self.surfacing_status_search:
            self.surfaced_or_unsurfaced = self.surfacing_status_search.group(1)
        else:
            self.surfaced_or_unsurfaced = ''
        if self.lens_id_search:
            #try:
            self.job = self.lens_id_search.group(1)
            self.base = self.lens_id_search.group(2)
            self.rx = self.lens_id_search.group(3)
            self.lens_number = self.lens_id_search.group(4)
            self.lens_description = 'Job ' + self.job + '\n' + self.base + ', ' + self.rx + ', Lens#' + self.lens_number
        else:
            self.lens_description = os.path.basename(file)
            #except:
            #    print('Some identification data in the filename of ' + file + ' seems to be missing, returning placeholders.')
            #    self.job = 'Missing'
            #    self.base = 'Missing'
            #    self.rx = 'Missing'
            #    self.lens_number = 'Missing'
        pmfmt_search = re.compile(r'PMFMT=')
        self.powermaps = {}
        self.powermap_ids = {}
        self.figures_to_generate = figures_to_generate

        with open(self.file) as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';', lineterminator='\n')
            filedata = PowermapDescriptionParse.preprocess_pmf(self, list(file_reader))
            for index, row in enumerate(filedata):
                if re.search(pmfmt_search, row[0]):
                    power_matrix_properties = PowermapDescriptionParse(row)
                    powermap_raw = np.array(filedata[index + 1:index + 1 + power_matrix_properties.x_col_count])
                    powermap = powermap_raw.astype(float)
                    rotated_powermap = np.rot90(powermap, 2)
                    flipped_powermap = np.fliplr(rotated_powermap)
                    power_matrix_id = power_matrix_properties.eye + power_matrix_properties.measured_power_type + power_matrix_properties.power_quantity + power_matrix_properties.measure_type
                    self.powermaps.update({power_matrix_id: flipped_powermap})
                    self.powermap_ids.update({power_matrix_id:PmfId(power_matrix_id)})

    def visualize_dlm_pmf(self, powermap_type, figure_label='DLM Powermap ', title=None, v_max=None, v_min=None,cmap=None):
        powermap = self.powermaps.get(powermap_type)
        pmf_id = self.powermap_ids[powermap_type]
        measured_power_type = pmf_id.measured_power_type  # error value, measure value, or refernce value
        plt.ylabel('Y position, mm')
        plt.xlabel('X position, mm')

        if title is None:
            plt.title(pmf_id.pmf_id_minimal, size=18)
        if title is not None:
            plt.title(title, size=18)
        if measured_power_type == 'M':
            v_max = None
            v_min = None
        if cmap is None:
            copy_colormap = plt.cm.get_cmap('nipy_spectral', 30)
        else:
            copy_colormap = cmap
        palette = copy_colormap
        masked_powermap = np.ma.masked_where(powermap is np.nan, powermap)
        x_axis = np.arange(-20, 21, 1)
        if v_max and v_min is not None:
            v = np.linspace(v_min, v_max, 25, endpoint=True)
            plt.contourf(x_axis, x_axis, masked_powermap, v, cmap=palette, vmin=v_min, vmax=v_max)
        else:
            v = np.linspace(np.nanmin(powermap), np.nanmax(powermap), 25, endpoint=True)
            plt.contourf(x_axis, x_axis, masked_powermap, v, cmap=palette)
        plt.colorbar(label='Power, dpt')
        plt.axis('square')


class PowermapDescriptionParse():
    # this class creates an object which contains all the powermap descriptors contained
    # in the rows that begin with PMFMT= in the powermap.
    def __init__(self, pmfmt_list):
        self.pmfmt_list = pmfmt_list
        self.eye = pmfmt_list[1]  # which eye, left, right or both (L, R, B)
        self.measured_power_type = pmfmt_list[2]  # B, F, or T, back, front, or transmitted power
        self.power_quantity = pmfmt_list[3]  # D, C, or A - spherical equivalent power, cylinder power, or cylinder axis
        self.measure_type = pmfmt_list[4]  # M, T, or E- measured, theoretical, or error
        self.x_col_count = int(pmfmt_list[5])  # number of X columns (integer)
        self.y_col_count = int(pmfmt_list[6])  # number of Y columns (integer)
        self.x_size = pmfmt_list[7]  # x size (in millimeters, the actual physical size of the dataset)
        self.y_size = pmfmt_list[8]  # y size (in millimeters, the actual physical size of the dataset)
        self.index = pmfmt_list[9]  # the index of the material, for generator acceptance lenses

    def preprocess_pmf(self, list):  # take in the entire pmf file in the form of a list
        for row in list:  # for all rows in the input list form pmf
            for i in range(len(row)):  # iterate across each row of the pmf
                row[i] = re.sub('PP=', '', row[i])  # remove all instances of pp at the beginning of powermap rows
                row[i] = re.sub('\?', 'nan', row[i])  # set unmeasured parts of the powermap (represented by '?' in the raw data to 99999 so they can be masked later
        return list  # return the list-form ready pmf for powermap extraction

def compare_pmf(pmf_obj1,pmf_obj2):
    pmf_difference = copy.deepcopy(pmf_obj1)
    for key,item in pmf_obj1.powermaps.items():
        pmf_difference.powermaps.update({key: np.subtract(item,pmf_obj2.powermaps.get(key))})
        pmf_difference.state = 'Difference between ' + pmf_obj1.state + ' and ' + pmf_obj2.state
    return pmf_difference

if __name__ == '__main__':
    test_compare_powermaps()
