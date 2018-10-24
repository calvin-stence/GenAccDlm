import csv
import glob2
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import pprint as pp
import numpy as np
import shutil
import os
import re


def main():
    lens_tests = create_tests()
    job_search = re.compile(r'(VER[\w]?[\d]?)')
    infile = 'dlm_data\VERD3_2018-10-18_17.15.38.DDF'
    ddf_search_dictionary = {
        'DBP Best Fit Tx': '',
        'DBP Best Fit Ty': '',
        'DBP Best Fit Rz': '',
        'FULL_LENS GMC': '',
        'Center GMC': '',
        'Center Power PV': '',
        'Center Power Average': ''
    }
    test = DdfDataGet(infile, ddf_search_dictionary).ddf_contents
    property_names, property_values = ddf_results_prep(test)
    ddf_plot(property_names, property_values)
    for file in glob2.glob('*\VERD3_2018-10-18_17.15.38.PMF'):
        job_identifier = re.search(job_search, file)
        for tests, testparams in lens_tests.items():
            testparams.update({'JOB': job_identifier.group(1)})
        for tests, testparams in lens_tests.items():
            testparams.update({'POWERMAP': PmfDataGet(file,testparams).powermap})
            visualize_powermap(testparams)
    plt.show()

def test_ddf():
    infile = 'dlm_data\VERD3_2018-10-18_17.15.38.DDF'
    ddf_search_dictionary = {
        'DBP Best Fit Tx':'',
        'DBP Best Fit Ty':'',
        'DBP Best Fit Rz':'',
        'FULL_LENS GMC':'',
        'Center GMC':'',
        'Center Power PV':'',
        'Center Power Average':''
    }
    test = DdfDataGet(infile,search_dictionary).ddf_contents
    ddf_results_prep(test)
    #read_ddf_contents(test)


def create_tests():
    test_dpt = {
        'JOB': '',
        'MEASURE_TYPE': 'E',
        'POWER_QUANTITY': 'D',
        'MEASURED_POWER_TYPE': 'T'
    }
    test_cyl = {
        'JOB': '',
        'MEASURE_TYPE': 'E',
        'POWER_QUANTITY': 'C',
        'MEASURED_POWER_TYPE': 'T'
    }
    lens_tests = {
        'dpt': test_dpt,
        'cyl': test_cyl
    }
    return lens_tests

def ddf_results_prep(results_dictionary):
    graphable_error_values = []
    error_values = []
    property_names = list(results_dictionary.keys())
    property_values = list(results_dictionary.values())
    float_property_values = []
    max_val = 0
    min_val = 0
    for row in property_values:
        float_property_values.append([float(i) for i in row])
    for row in float_property_values:
        if max(row) > max_val:
            max_val = max(row)
        if min(row) < min_val:
            min_val = min(row)
    print(min_val)
    for row in float_property_values:
        error = abs(row[1])-row[2]
        error_values.append(error)
        scaled_error = get_bar_multiplier(max_val,min_val,error)
        graphable_error_values.append(scaled_error)
    return property_names, graphable_error_values


def get_bar_multiplier(max_val,min_val,val):
    return (val-min_val)/(max_val-min_val)

def ddf_plot(property_names, property_values):
    fig, ax = plt.subplots()
    print(property_names)
    print(property_values)
    plt.barh(property_names, property_values)
    #plt.yticks(range(property_names),property_names)
    plt.show()

class DdfDataGet():
    # todo get DBP Tx, Ty, Rz, Full Lens GMC, Center GMC, Center Power PV, Center Power Average
    def __init__(self, file, search_dictionary):
        self.file = file
        with open(self.file) as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';', lineterminator='\n')
            filedata = DdfDataGet.preprocess_ddf(self, list(file_reader))
            output_dictionary = {}
            for search, val in search_dictionary.items():
                for row in filedata:
                    if search in output_dictionary.keys():
                        pass
                    for i in range(len(row)):
                        if re.search(search,row[i]):
                            output_dictionary.update({search:row[3:6]})
            self.ddf_contents = output_dictionary


    def preprocess_ddf(self, list):  # take in the entire pmf file in the form of a list
        for row in list:  # for all rows in the input list form pmf
            for i in range(len(row)):  # iterate across each row of the pmf
                row[i] = re.sub('DD=', '', row[i])  # remove all instances of pp at the beginning of powermap rows
                row[i] = re.sub('\?', '99999', row[
                    i])  # set unmeasured parts of the powermap (represented by '?' in the raw data to 99999 so they can be masked later
        return list  # return the list-form ready pmf for powermap extraction


class PmfDataGet():
    def __init__(self, file, powermap_params):
        self.file = file
        self.powermap_params = powermap_params
        pmfmt_search = re.compile(r'PMFMT=')

        with open(self.file) as csvfile:
            file_reader = csv.reader(csvfile, delimiter=';', lineterminator='\n')
            filedata = PmfmtParse.preprocess_pmf(self, list(file_reader))
            powermaps = []
            for index, row in enumerate(filedata):
                if re.search(pmfmt_search, row[0]):
                    power_matrix_properties = PmfmtParse(row)
                    measure_type_bool = power_matrix_properties.measure_type == self.powermap_params.get('MEASURE_TYPE')
                    power_quantity_bool = power_matrix_properties.power_quantity == self.powermap_params.get(
                        'POWER_QUANTITY')
                    measured_power_type_bool = power_matrix_properties.measured_power_type == self.powermap_params.get(
                        'MEASURED_POWER_TYPE')
                    if measure_type_bool and power_quantity_bool and measured_power_type_bool:
                        powermap_raw = np.array(filedata[index + 1:index + 1 + power_matrix_properties.x_col_count])
                        powermap = powermap_raw.astype(float)
                        self.powermap = powermap


def visualize_powermap(powermap_params):
    job = powermap_params.get('JOB')
    powermap = powermap_params.get('POWERMAP')
    measure_type = powermap_params.get('MEASURE_TYPE')
    power_quantity = powermap_params.get('POWER_QUANTITY')
    measured_power_type = powermap_params.get('MEASURED_POWER_TYPE')
    figure_name = job + ', ' + measure_type + ', ' + power_quantity + ', ' + measured_power_type
    fig = plt.figure()
    fig.subplots_adjust(top=0.9)
    ax1 = fig.add_subplot(111)
    ax1.set_ylabel('Y position, mm')
    ax1.set_xlabel('X position, mm')
    ax1.set_title(figure_name)
    copy_colormap = plt.cm.nipy_spectral
    palette = copy_colormap
    palette.set_bad('w', 1.0)
    masked_powermap = np.ma.masked_where(powermap > 20, powermap)
    plt.imshow(masked_powermap, cmap=palette, interpolation='bilinear', vmin=-0.25, vmax=0.3)
    plt.colorbar(label='Power, dpt')
    plt.savefig(job + '_' + measure_type + '_' + power_quantity + '_' + measured_power_type + '.png',
                bbox_inches='tight')


def gen_acc_test():
    return 0


class PmfmtParse():
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
                row[i] = re.sub('\?', '99999', row[
                    i])  # set unmeasured parts of the powermap (represented by '?' in the raw data to 99999 so they can be masked later
        return list  # return the list-form ready pmf for powermap extraction

if __name__ == "__main__":
    main()
