import csv
import glob2
import time
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import os
import re
import shutil
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patheffects as path_effects

#Main does several things:
# 1. Find raw data
# 2. Reorganize raw data into a lab\generator\fast tool\dbp or rtc file structure
# 3. Access that file structure to create figures of powermaps and a table of go-no-go results for each fast tool
# 4. Concatenate all the figures into an output file and save it as a PDF
# 5. Loop over all available fast tools to create multiple reports in a single mouse click
def main():
    raw_data_and_extension_pmf = 'RAW_DATA_DUMP\*.PMF'
    raw_data_and_extension_ddf = 'RAW_DATA_DUMP\*.DDF'
    file_structure_location = 'STRUCTURED_GENACC_DATA'
    create_and_move_dlm_data(raw_data_and_extension_pmf, file_structure_location)
    create_and_move_dlm_data(raw_data_and_extension_ddf, file_structure_location)
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
        'Center Power Average': '',
        'FULL_LENS Power Average': ''
    }
    file_count = 1
    ddf_data_tracker = []
    test_result_figure_dictionary = {}
    rtc_fail_dictionary = {}
    dbp_fail_dictionary = {}
    print('--------------------')
    for fast_tool_file_path in glob2.glob('STRUCTURED_GENACC_DATA\**\FT*'):  # for each fast tool directory found
        print('Started job in ' + os.path.abspath(fast_tool_file_path))
        pdf_lab, pdf_generator, pdf_fast_tool = genacc_filename_get(os.path.abspath(fast_tool_file_path))
        report_destination = 'COMPLETED_REPORTS' + '\\' + pdf_lab
        try:
            pdf_filename = report_destination+ '\\InternalGenAcc_' + pdf_lab + '_' + pdf_generator + '_' + pdf_fast_tool + '.pdf'
            with PdfPages(pdf_filename) as pdf:
                start = time.time()
                print('Begin measure of lens ')
                for item in lens_list:  # for each lens in that fast tool directory
                    figure_height = 11
                    figure_width = 21
                    lens_figure = plt.figure(file_count, figsize=(21, 11))  # create a figure for that fast tool's data

                    image_count = 1  # set the image count (for placing the image in the right position in the figure) to 1
                    print(item, end=" ")
                    for measure_type_file_path in glob2.glob(
                            fast_tool_file_path + '\*'):  # for each type of measure (RTC and DBP)
                        for pmf_file in glob2.glob(measure_type_file_path + '\\*' + item + '*.PMF'):  # for each .PMF file in the current fast tool, lens, and RTC or DBP folder
                            job_identifier = item  # re.search(job_search, pmf_file) # figure out which
                            abs_filepath = os.path.abspath(pmf_file)
                            ddf_file = re.sub('.PMF', '', abs_filepath + '.DDF')
                            ddf_data = DdfDataGet(ddf_file, ddf_search_dictionary).ddf_contents
                            property_names, property_values, error_values, passing_status, failing_values = ddf_results_prep(
                                ddf_data)
                            if 'RTC' in measure_type_file_path:
                                rtc_fail_dictionary[item] = failing_values
                                rtc_or_dbp = 'RTC'
                            if 'DBP' in measure_type_file_path:
                                dbp_fail_dictionary[item] = failing_values
                                rtc_or_dbp = 'DBP'
                            ddf_data_tracker.append(passing_status)
                            ddf_table(property_names, property_values, error_values, passing_status, image_count, item, rtc_or_dbp)
                            image_count = image_count + 1
                            lab, generator, fast_tool, measure = genacc_figurename_get(abs_filepath)
                            for tests, testparams in lens_tests.items():
                                testparams.update({'JOB': item + ' ' + measure})
                            for tests, testparams in lens_tests.items():
                                testparams.update({'POWERMAP': PmfDataGet(pmf_file, testparams).powermap})
                                visualize_powermap(testparams, image_count)
                                image_count = image_count + 1
                    lens_figure.suptitle('GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool + ', Lens ' + item, size=25)  # add a title to that figure
                    dbp_label = lens_figure.text(.03,.68,'DBP',size=35)
                    dbp_label.set_path_effects([path_effects.Normal()])
                    rtc_label = lens_figure.text(.03, .22, 'RTC', size=35)
                    rtc_label.set_path_effects([path_effects.Normal()])
                    file_count = file_count + 1
                    lens_figure.subplots_adjust(left=.20,right=.95, bottom=.05,top=.9)
                    test_result_figure_dictionary[item] = lens_figure
                    plt.close()
                lens_verdict_dictionary, test_result = determine_genacc_test_pass(rtc_fail_dictionary, dbp_fail_dictionary,
                                                                                  lens_list)
                print('\nLens Tests And Figures Complete')
                print('Overall Test Result: ' + test_result)
                title_fig = plt.figure(figsize=(21, 11))
                title_text = title_fig.text(.5, .5,
                                      'Generator Acceptance Internal Report\n' + 'GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool + '\n' + 'Essilor Global Engineering Dallas',
                                      ha='center', va='center', size=40)
                title_text.set_path_effects([path_effects.Normal()])
                print('Begin PDF Saving')
                pdf.savefig(title_fig)
                plt.close()
                print('Lens Results: ' + str(lens_verdict_dictionary))
                result_table_figure = acceptance_result_figure(lens_verdict_dictionary, test_result, lens_list)
                pdf.savefig(result_table_figure)
                plt.close()
                for item in lens_list:
                    #plt.tight_layout()
                    powermap = test_result_figure_dictionary[item]
                    pdf.savefig(powermap)
                print(
                    'PDF Saved: ' + 'Generator Acceptance Internal Report' + ' GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool)
                end = time.time()
                print('Script Completed in ' + str(end - start) + ' Seconds')
                print('--------------------')
        except PermissionError:
            print('File ' + 'InternalGenAcc_' + pdf_lab + '_' + pdf_generator + '_' + pdf_fast_tool + '.pdf' + ' seems to be open already--please close it!')
            print('--------------------')

#This function returns the different DCS (data communication standard) tags used in the pmfmt line (which indicates what
# sort of powermap is being described) of the .pmf file to indicate to the script which powermaps to use.

#Test prep
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
        'cyl': test_cyl,
        'dpt': test_dpt
    }
    return thrupower_tests

#DDF Processing and Figure Creation
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
                        continue
                    for i in range(len(row)):
                        if re.search(search, row[i]):
                            output_dictionary.update({search: row[3:6]})
            self.ddf_contents = output_dictionary

    def preprocess_ddf(self, list):  # take in the entire pmf file in the form of a list
        for row in list:  # for all rows in the input list form pmf
            for i in range(len(row)):  # iterate across each row of the pmf
                row[i] = re.sub('DD=', '', row[i])  # remove all instances of pp at the beginning of powermap rows
                row[i] = re.sub('\?', '0', row[
                    i])  # set unmeasured parts of the powermap (represented by '?' in the raw data to 99999 so they can be masked later
        return list  # return the list-form ready pmf for powermap extraction


def ddf_results_prep(results_dictionary):
    error_values = []
    passing_status = []
    property_names = list(results_dictionary.keys())
    property_values = list(results_dictionary.values())
    float_property_values = []
    failing_values = []
    measure_vals = []
    for row in property_values:
        float_property_values.append([float(i) for i in row])
    for index, row in enumerate(float_property_values):
        measure_vals.append(float_property_values[index][1])
        if abs(row[2]) < abs(row[1]):
            error = abs(row[1]) - row[2]
        else:
            error = 'N/A'
        str_error = str(error)
        error_values.append(str_error[0:5])
        if int(row[0]) == 1:
            passing_status.append("PASS")
        else:
            passing_status.append("FAIL")
            failing_values.append(property_names[index])
    return property_names, measure_vals, error_values, passing_status, failing_values


def ddf_table(property_names, property_values, error_values, passing_status, figure_index, lens_name, dbp_or_rtc):
    ax = plt.subplot(230 + figure_index)
    colors = []
    for x in passing_status:
        if x == 'PASS':
            colors.append((0, 1, 0))  # (255,0,0))
        else:
            colors.append((1, 0, 0))  # (0,255,0))

    table_cells = row_to_column(passing_status)
    property_names_list = property_names
    table_cells = add_column(table_cells, property_values)
    table_cells = add_column(table_cells, error_values)
    #ax.axis('tight')
    ax.axis('off')
    data_table = plt.table(cellText=table_cells, rowLabels=property_names, colLabels=['Passing\nStatus', 'Measured\nValue', 'Exceeds Spec\nLimit By'],
              rowColours=colors, loc='center')
    data_table.scale(1,2.2)
    ax.set_title(lens_name + ', ' + dbp_or_rtc + ', Go-No-Go')


#PMF Processing and Figure Creation
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
                        rotated_powermap = np.rot90(powermap,2)
                        self.powermap = rotated_powermap


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


def visualize_powermap(powermap_params, figure_index):
    job = powermap_params.get('JOB')
    powermap = powermap_params.get('POWERMAP')  #
    measure_type = powermap_params.get('MEASURE_TYPE')  # error value, measure value, or refernce value
    power_quantity = powermap_params.get('POWER_QUANTITY')  # cylinder or spherical equivalent diopter
    measured_power_type = powermap_params.get('MEASURED_POWER_TYPE')  # reflection or transmission
    if power_quantity == 'C':
        power_label = 'Cylinder (dpt)'
    if power_quantity == 'D':
        power_label = 'Power (dpt)'
    if measured_power_type == 'T':
        measured_power_type_label = 'Transmission'
    subplot_name = job + ', ' + measure_type + ', ' + power_label + ', ' + measured_power_type_label
    # fig = plt.figure()
    ax1 = plt.subplot(230 + figure_index)
    ax1.set_ylabel('Y position, mm')
    ax1.set_xlabel('X position, mm')
    ax1.set_title(subplot_name)
    copy_colormap = plt.cm.nipy_spectral
    palette = copy_colormap
    palette.set_bad('w', 1.0)
    masked_powermap = np.ma.masked_where(powermap > 20, powermap)
    if power_quantity == 'C':
        v_max = 0.3
        v_min = -.3
    if power_quantity == 'D':
        v_max = 0.25
        v_min = -0.25
    plt.imshow(masked_powermap, cmap=palette, interpolation='gaussian', vmin=v_min, vmax=v_max)
    plt.colorbar(label='Power, dpt')

#This function takes in the failing RTC and DBP measurements produced by ddf_results_prep and decides if the generator
#has passed the generator acceptance process.
def determine_genacc_test_pass(rtc_failing_results, dbp_failing_results, lens_list):
    lens_verdict_dictionary = {}
    for item in lens_list:
        lens_verdict_dictionary[item] = ''
    fail_count = 0
    for lens, failing_params in rtc_failing_results.items():
        if re.search('FULL_LENS GMC',str(failing_params)):
            if re.search('FULL_LENS GMC',str(dbp_failing_results[lens])):
                fail_count = fail_count + 1
                lens_verdict_dictionary[lens] = 'FULL_LENS GMC; '
        if re.search('Center Power Average',str(failing_params)) or re.search('Center GMC',str(failing_params)):
            if re.search('Center Power Average', str(dbp_failing_results[lens])) or re.search('Center GMC', str(dbp_failing_results[lens])):
                lens_verdict_dictionary[lens] = lens_verdict_dictionary[lens] + ' CENTER DEFECT;'
        if re.search('FULL_LENS Power Average',str(failing_params)):
            if re.search('FULL_LENS Power Average',dbp_failing_results[lens]):
                lens_verdict_dictionary[lens] = lens_verdict_dictionary[lens] + ' CENTER THICKNESS; '
        if re.search('DBP Best Fit',str(failing_params)):
            lens_verdict_dictionary[lens] = lens_verdict_dictionary[lens] + ' POSITIONING; '

    if fail_count > 1:
        test_result = 'FAIL'
    else:
        test_result = 'ACCEPTED'
    return lens_verdict_dictionary, test_result


def acceptance_result_figure(test_result_dictionary, test_result, lens_list):
    test_result_fig = plt.figure(99, figsize=(21, 11)) #figure number is 99 to prevent interference with other figures
    ax = plt.subplot(335)
    #ax.axis('tight')
    ax.axis('off')
    colors = []
    acceptance_list = []
    row_labels = []
    row_labels.append('Overall Test Result')
    row_labels = row_labels + lens_list
    acceptance_list.append([test_result])
    if test_result == 'ACCEPTED':
        colors.append((0, 1, 0))
    if test_result != 'ACCEPTED':
        colors.append((1, 0, 0))
    for lens, acceptance in test_result_dictionary.items():
        acceptance_string = str(acceptance)
        if acceptance_string == '':
            acceptance_list.append(['PASS'])
            colors.append((0, 1, 0))
            continue
        if acceptance_string == 'FAIL':
            acceptance_list.append(['FAIL'])
            colors.append((1, 0, 0))
            continue
        if acceptance_string != '':
            acceptance_list.append(['DEFECTS: ' + acceptance])
            if re.search('FULL_LENS GMC',acceptance_string):
                colors.append((1,0,0))
                continue
            colors.append((1, .5, 0))  # (255,0,0))
    table_cells = acceptance_list
    acceptance_table = plt.table(cellText=table_cells, rowLabels=row_labels, colLabels=['Result'],
              rowColours=colors, loc='center',fontsize=25)
    acceptance_table.scale(1, 3)
    #ax.set_title('Overall and Invidual Lens Results')


#Filename and File Manipulation
#This function takes in disogranized DLM data with a regular filename (LAB_GENERATORNUMBER_FASTTOOL_LENS_DBPORRTC.pmf/ddf)
#and organizes it in a lab\generator\fast tool\dbp or rtc file structure for easy access and human readability
def create_and_move_dlm_data(raw_data_and_extension,file_structure_location):
    for file in glob2.glob(raw_data_and_extension):
        lab, generator_number, fast_tool, lens, measure_type = genacc_rawdata_filename_get(file)
        structured_data_path = file_structure_location+'\\'+lab+'\\'+generator_number+'\\'+fast_tool+'\\'+measure_type+'_DATA'
        try:
            os.makedirs(structured_data_path)
        except FileExistsError:
            pass
        shutil.copy(file,structured_data_path)
#The next three functions are all very similar implementaions of a regex search which returns different parts of a filename.
#Each is only used once or twice in the rest of the code, but including them inline would clutter things and perhaps
#cause even more confusion than having three similar functions.

#This function gets the different parts contained in a filepath (i.e., ddf and pmf filename as saved at the DLM)
#and returns them for use. It's used in main to name the .pdf file for saving.
def genacc_filename_get(abs_filepath):
    abs_filepath_regex = re.compile(r'\\([\w]+[\d]?)\\([\d]+[\w]?)\\(\w\w\d)')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    return lab, generator_number, fast_tool

#This function gets the different parts contained in the raw DLM data filename (i.e., ddf and pmf filename as saved at the DLM)
#and returns them for use in other functions (such as create_and_move_dlm_data)
def genacc_rawdata_filename_get(abs_filepath):
    abs_filepath_regex = re.compile(r'([\w]+[\d]?)_([\d]+[\w]?)_(\w\w\d)_(\w\w\w\w[\W]?[\d]?)_(\w\w\w)')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    lens = search_result.group(4)
    measure_type = search_result.group(5)
    return lab, generator_number, fast_tool, lens, measure_type

#This function gets the different parts contained in a filepath (i.e., ddf and pmf filename as saved at the DLM)
#and returns them for use. It's used in main to name the figures contained within the .pdf.
def genacc_figurename_get(abs_filepath):
    abs_filepath_regex = re.compile('\\\([\w]+)\\\([\d]+[\w]?)\\\(\w\w\d)\\\(\w\w\w)_DATA')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    measure_type = search_result.group(4)
    return lab, generator_number, fast_tool, measure_type

#List Manipulation Tools
def add_column(list1, list2):
    for index, row in enumerate(list1):
        row.append(list2[index])
        # print(row)
    return list1


def row_to_column(list):
    transposed_list = []
    for i in range(len(list)):
        transposed_list.append([list[i]])
    return transposed_list


if __name__ == "__main__":
    main()