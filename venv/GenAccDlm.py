import csv
import glob2
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import pprint as pp
import numpy as np
import shutil
import os
import re
from matplotlib.backends.backend_pdf import PdfPages


def main():
    lens_tests = create_thrupower_tests()
    job_search = re.compile(r'(VER[\w]?[\d]?)')
    lens_list = ['VERD1', 'VERD2', 'VERD3', 'VERC', 'VER1', 'VER0']
    ddf_search_dictionary = {
        'DBP Best Fit Tx': '',
        'DBP Best Fit Ty': '',
        'DBP Best Fit Rz': '',
        'FULL_LENS GMC': '',
        'Center GMC': '',
        'Center Power PV': '',
        'Center Power Average': ''
    }
    file_count = 1
    ddf_data_tracker = []
    #test_result_figure_dictionary = {}
    for fast_tool_file_path in glob2.glob('GENERATOR_ACCEPTANCE\**\FT*'): #for each fast tool directory found
        pdf_lab, pdf_generator, pdf_fast_tool = genacc_filename_get(os.path.abspath(fast_tool_file_path))
        with PdfPages('InternalGenAcc_' + pdf_lab + '_' + pdf_generator + '_' + pdf_fast_tool + '.pdf') as pdf:
            for item in lens_list: #for each lens in that fast tool directory
                lens_figure = plt.figure(file_count, figsize=(21,11)) #create a figure for that fast tool's data
                image_count = 1 # set the image count (for placing the image in the right position in the figure) to 1
                for measure_type_file_path in glob2.glob(fast_tool_file_path + '\*'): # for each type of measure (RTC and DBP)
                    for pmf_file in glob2.glob(measure_type_file_path + '\\' + item + '*.PMF'): #for each .PMF file in the current fast tool, lens, and RTC or DBP folder
                        job_identifier = item#re.search(job_search, pmf_file) # figure out which
                        abs_filepath = os.path.abspath(pmf_file)
                        ddf_file = re.sub('.PMF','',abs_filepath + '.DDF')
                        ddf_data = DdfDataGet(ddf_file, ddf_search_dictionary).ddf_contents
                        property_names, property_values, error_values, passing_status = ddf_results_prep(ddf_data)
                        ddf_table(property_names, property_values, error_values, passing_status, image_count, item)
                        image_count = image_count+1
                        lab, generator, fast_tool, measure = genacc_figurename_get(abs_filepath)
                        for tests, testparams in lens_tests.items():
                            testparams.update({'JOB': item + ' ' + measure})
                        for tests, testparams in lens_tests.items():
                            testparams.update({'POWERMAP': PmfDataGet(pmf_file,testparams).powermap})
                            visualize_powermap(testparams, image_count)
                            image_count = image_count + 1
                lens_figure.suptitle('GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool + ', Lens ' + item)  # add a title to that figure
                file_count = file_count + 1
            #lens_figure.subplots_adjust(left = .16, right=.95, top=.95, bottom=0.08)
                pdf.savefig(lens_figure)
                plt.close()

        #plt.show()
        # plt.savefig(job + '_' + measure_type + '_' + power_quantity + '_' + measured_power_type + '.png',
        #            bbox_inches='tight')


def genacc_filename_get(abs_filepath):
    abs_filepath_regex = re.compile('\\\([\w]+)\\\([\d]+[\w]?)\\\(\w\w\d)')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    return lab, generator_number, fast_tool


def genacc_figurename_get(abs_filepath):
    abs_filepath_regex = re.compile('\\\([\w]+)\\\([\d]+[\w]?)\\\(\w\w\d)\\\(\w\w\w)_DATA')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    measure_type = search_result.group(4)
    return lab, generator_number, fast_tool, measure_type

def create_thrupower_tests():
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
    thrupower_tests = {
        'dpt': test_dpt,
        'cyl': test_cyl
    }
    return thrupower_tests

def test_ddf():
    infile = 'GENERATOR_ACCEPTANCE\TEST_LAB_1\\26001\FT1\DBP_DATA\VERD3_2018-10-18_17.15.38.DDF'
    image_count = 1
    item = 'VERD3'
    ddf_search_dictionary = {
        'DBP Best Fit Tx':'',
        'DBP Best Fit Ty':'',
        'DBP Best Fit Rz':'',
        'FULL_LENS GMC':'',
        'Center GMC':'',
        'Center Power PV':'',
        'Center Power Average':''
    }
    ddf_data = DdfDataGet(infile, ddf_search_dictionary).ddf_contents
    property_names, property_values, error_values, passing_status = ddf_results_prep(ddf_data)
    ddf_table(property_names, property_values, error_values, passing_status, image_count, item)

def ddf_results_prep(results_dictionary):
    graphable_error_values = []
    error_values = []
    passing_status = []
    property_names = list(results_dictionary.keys())
    property_values = list(results_dictionary.values())
    graphable_property_values = []
    float_property_values = []
    max_val = 0
    min_val = 0
    for row in property_values:
        float_property_values.append([float(i) for i in row])
    for row in float_property_values:
        graphable_property_values.append(row[1])
    for row in float_property_values:
        error = abs(row[1])-row[2]
        if row[0] == 1:
            passing_status.append("PASS")
        else:
            passing_status.append("FAIL")
        error_values.append(error)

    return property_names, graphable_property_values, error_values, passing_status


def get_bar_multiplier(max_val,min_val,val):
    return (val-min_val)/(max_val-min_val)


def ddf_table(property_names, property_values, error_values, passing_status, figure_index, lens_name):
    ax = plt.subplot(230 + figure_index)
    #print(property_names)
    #print(property_values)
    colors = []
    for x in passing_status:
        if x == 'PASS':
            colors.append((0,1,0))#(255,0,0))
        else:
            colors.append((1,0,0))#(0,255,0))

    #print(colors)
    table_cells = row_to_column(passing_status)
    property_names_list = property_names
    table_cells = add_column(table_cells,property_values)
    table_cells = add_column(table_cells,error_values)
    #print(table_cells)
    ax.axis('tight')
    ax.axis('off')
    plt.table(cellText=table_cells,rowLabels=property_names, colLabels = ['Passing Status', 'Measure Value', 'Error'],rowColours=colors,loc='center')
    ax.set_title(lens_name + ', Go-No-Go')
    #plt.imshow(ax)
    #plt.yticks(range(property_names),property_names)
    #plt.show()

def add_column(list1,list2):
    for index, row in enumerate(list1):
        row.append(list2[index])
        #print(row)
    return list1

def row_to_column(list):
    transposed_list = []
    for i in range(len(list)):
        transposed_list.append([list[i]])
    return transposed_list


def ddf_plot(property_names, property_values, passing_status, figure_index, lens_name):
    ax = plt.subplot(230 + figure_index)
    #print(property_names)
    #print(property_values)
    plt.barh(property_names, property_values)
    ax.set_title(lens_name + ', GNG')
    #plt.imshow(ax)
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
                row[i] = re.sub('\?', '0', row[
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


def visualize_powermap(powermap_params, figure_index):
    job = powermap_params.get('JOB')
    powermap = powermap_params.get('POWERMAP') #
    measure_type = powermap_params.get('MEASURE_TYPE') #error value, measure value, or refernce value
    power_quantity = powermap_params.get('POWER_QUANTITY') # cylinder or spherical equivalent diopter
    measured_power_type = powermap_params.get('MEASURED_POWER_TYPE') #reflection or transmission
    subplot_name = job + ', ' + measure_type + ', ' + power_quantity + ', ' + measured_power_type
    #fig = plt.figure()
    ax1 = plt.subplot(230 + figure_index)
    ax1.set_ylabel('Y position, mm')
    ax1.set_xlabel('X position, mm')
    ax1.set_title(subplot_name)
    copy_colormap = plt.cm.nipy_spectral
    palette = copy_colormap
    palette.set_bad('w', 1.0)
    masked_powermap = np.ma.masked_where(powermap > 20, powermap)
    plt.imshow(masked_powermap, cmap=palette, interpolation='bilinear', vmin=-0.25, vmax=0.3)

    plt.colorbar(label='Power, dpt')
    #plt.savefig(job + '_' + measure_type + '_' + power_quantity + '_' + measured_power_type + '.png',
    #            bbox_inches='tight')

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
    #test_list = ['FAIL', 'FAIL', 'FAIL', 'FAIL', 'PASS']
    #list1 = row_to_column(test_list)
    #test = add_column(list1,list1)
    #print(test)
    #test_ddf()

    main()