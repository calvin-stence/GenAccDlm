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


# Main does several things:
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
    test_result_figure_dictionary = {}
    rtc_fail_dictionary = {}
    dbp_fail_dictionary = {}
    figure_height = 11  # figure height is 2100x1100 pixels , about size to fit modern monitors
    figure_width = 21  # size could be dynamic and not hardcoded, but padding wasn't implemented early enough so figure size was increased to fit everything
    print('--------------------')
    for fast_tool_file_path in glob2.glob('STRUCTURED_GENACC_DATA\**\FT*'):  # for each fast tool directory found
        print('Started job in ' + os.path.abspath(
            fast_tool_file_path))  # Let the user know that the script has found a job and where that job is
        lab, generator, fast_tool = genacc_filename_get(os.path.abspath(fast_tool_file_path))  # from the fast tool directory found above, extract the data needed to name the PDF and other figures
        report_destination = 'COMPLETED_REPORTS' + '\\' + lab  # the PDFs will be saved in this location, in a folder within the COMPLETED_REPORTS folder by the lab name found in the line above
        try:
            pdf_filename = report_destination + '\\InternalGenAcc_' + lab + '_' + generator + '_' + fast_tool + '.pdf'  # where the .pdf is created. It is created first, then filled with figures.
            try:
                os.makedirs(report_destination)
            except(FileExistsError):
                pass
            with PdfPages(pdf_filename) as pdf:  # open a pdf which each fast tool's figures will be saved in
                start = time.time()  # begin measuring how long the script takes for each fast tool
                print(
                    'Lenses completed: ')  # let the user know that a lens is being measured, helps inform the user of progress
                for lens in lens_list:  # for each lens in that fast tool directory
                    lens_figure = plt.figure(file_count, figsize=(figure_width, figure_height))  # create a figure for that fast tool's data
                    image_count = 1  # set the image count (for placing the image in the right position in the figure)
                    print(lens, end=" ")  # let the user know which lens data is currently being processed
                    for measure_type_file_path in glob2.glob(fast_tool_file_path + '\\*'):  # for each type of measure (RTC and DBP) *within* the fast tool folder
                        for pmf_file in glob2.glob(measure_type_file_path + '\\*' + lens + '*.PMF'):  # for each .PMF file in the current fast tool, lens, and RTC or DBP folder
                            pmf_abs_filepath = os.path.abspath(
                                pmf_file)  # return the absolute filepath (i.e., the entire file structure between the script and the .pmf file)
                            ddf_abs_filepath = re.sub('.PMF', '',
                                                      pmf_abs_filepath + '.DDF')  # replace the .pmf extension on the .ddf file to find the .ddf file for this lens
                            ddf_data = DdfDataGet(ddf_abs_filepath,
                                                  ddf_search_dictionary).ddf_contents  # get the relevant ddf contents (defined in the ddf search dictionary)
                            property_names, property_values, error_values, passing_status, failing_values = ddf_results_prep(
                                ddf_data)  # look at the ddf contents and return the relevant results
                            if 'RTC' in measure_type_file_path:  # if this is an RTC file
                                rtc_or_dbp = 'RTC'  # remember that this is an RTC file
                                rtc_fail_dictionary[
                                    lens] = failing_values  # the failing DDF results for this lens are stored in the RTC failing results list
                            if 'DBP' in measure_type_file_path:  # if this is a DBP file
                                rtc_or_dbp = 'DBP'  # remember that this is a DBP file
                                dbp_fail_dictionary[
                                    lens] = failing_values  # the failing DDF results for this  lens are stored in the DBP failing results list
                            ddf_table(property_names, property_values, error_values, passing_status, image_count, lens, rtc_or_dbp)  # created the go-no-go table from the DDF results
                            image_count = image_count + 1  # the go-no-go table from the DDF has been greated, increment the figure counter to move to the next slot
                            for tests, testparams in lens_tests.items():  # for each test in lens_tests, get the test parameters. lens_tests is defined towards the top of main, it defines which measurements are extracted from the .pmf data.
                                testparams.update({'JOB': lens + ' ' + rtc_or_dbp})  # update the testparams with the lens the script is currently on and wheter it's dbp or rtc
                            for tests, testparams in lens_tests.items():  # iterate over the updated lens_tests dictionary
                                try:
                                    testparams.update({'POWERMAP': PmfDataGet(pmf_file,testparams).powermap})  # add a powermap to each testparams key
                                    visualize_powermap(testparams, image_count, figure_dimensions=230)  # create a figure from that powermap
                                except AttributeError:
                                    print('\nThe PMF for lens ' + lens + ' has an issue--maybe the PMF is missing?')
                                    plt.subplot(230+image_count)
                                image_count = image_count + 1  # increment the figure counter to populate the next spot in the overall pdf page figure
                    lens_figure.suptitle('GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool + ', Lens ' + lens, size=25)  # add a title to the figure for this lens
                    dbp_label = lens_figure.text(.03, .68, 'DBP', size=35)  # add a label to the DBP figure row (the positions are hardcoded, foresight would have used axes and zip to do this in a dynamic way
                    dbp_label.set_path_effects([path_effects.Normal()])  # this makes the text of the above label appear
                    rtc_label = lens_figure.text(.03, .22, 'RTC', size=35)  # add a label to the RTC figure row
                    rtc_label.set_path_effects([path_effects.Normal()])  # this makes the text of the above label appear
                    lens_figure.subplots_adjust(left=.20, right=.95, bottom=.05, top=.9)  # adjust the figures to fit, this is hardcoded and will not dynamically adjust
                    test_result_figure_dictionary[lens] = lens_figure  # append the lens figure (i.e., a page of the .pdf) to dictionary entry for the lens
                    file_count = file_count + 1  # increment the lens figure counter to prevent the next page of figures from being written on top of the first
                    plt.close()  # close the open figures
                lens_verdict_dictionary, test_result = determine_genacc_test_pass(rtc_fail_dictionary,
                                                                                  dbp_fail_dictionary,
                                                                                  lens_list)  # takes in the failing parameters from the .ddf and the list of lenses tested, outputs the lens_verdict_dictionary (a record of the failing results for each lens) and the test_result, a pass/fail criterion for the entire generator acceptance test
                print('\nLens Tests And Figures Complete')  # let the user know that the test has completed generating all figures
                print('Overall Test Result: ' + test_result)  # let the user know if the test passed or failed
                title_fig = plt.figure(figsize=(21, 11))  # add a title page
                # populate the title page with the title
                title_fig_title = 'Generator Acceptance Internal Report\n' + 'GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool + '\n' + 'Essilor Global Engineering Dallas'
                title_text = title_fig.text(.5, .5, title_fig_title, ha='center', va='center', size=40)  # create the title text
                title_text.set_path_effects([path_effects.Normal()])  # make the title text appear
                print('Begin PDF Saving')  # let the user know that the .pdf is beginning to be filled with figures
                pdf.savefig(title_fig)  # add the title figure to the pdf
                plt.close()  # close the title figure
                print('Lens Results: ' + str(lens_verdict_dictionary))
                # create the result table from the test result and lens verdict dictionary. this is the table displayed after the title page which summarizes the test results and says whether the test passed
                result_table_figure = acceptance_result_figure(lens_verdict_dictionary, test_result, lens_list)
                pdf.savefig(result_table_figure)  # add the result table to the pdf
                plt.close()  # close the result table figure
                for lens in lens_list:
                    # plt.tight_layout()
                    lens_results = test_result_figure_dictionary[lens]  # get the powermaps and go-no-go ddf tables for each lens lens
                    pdf.savefig(lens_results)  # add lens_results to the pdf
                print('PDF Saved: ' + 'Generator Acceptance Internal Report' + ' GenAcc Lab ' + lab + ', Generator ' + generator + ', ' + fast_tool)
                end = time.time()  # find the time at the end of the pdf generation
                print('Script Completed in ' + str(
                    end - start) + ' Seconds')  # let the user know how long it took to process the data and generate the pdf
                print('--------------------')
        except PermissionError:  # let the user know if the file the script is trying to create is already open and skip that file
            print('File ' + 'InternalGenAcc_' + lab + '_' + generator + '_' + fast_tool + '.pdf' + ' seems to be open already--please close it!')
            print('--------------------')


# Test prep
# This function returns the different DCS (data communication standard) tags used in the pmfmt line (which indicates what
# sort of powermap is being described) of the .pmf file to indicate to the script which powermaps to use.

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


# DDF Processing and Figure Creation
class DdfDataGet():
    # todo get DBP Tx, Ty, Rz, Full Lens GMC, Center GMC, Center Power PV, Center Power Average
    def __init__(self, file, search_dictionary):
        self.file = file
        try:
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
        except FileNotFoundError:
            print('\nNo .DDF found for ' + os.path.basename(file) + '--check if it is missing')
            self.ddf_contents = search_dictionary

    def preprocess_ddf(self, list):  # take in the entire pmf file in the form of a list
        for row in list:  # for all rows in the input list form pmf
            for i in range(len(row)):  # iterate across each row of the pmf
                row[i] = re.sub('DD=', '', row[i])  # remove all instances of pp at the beginning of powermap rows
                row[i] = re.sub('\?', '0', row[i])  # set unmeasured parts of the powermap (represented by '?' in the raw data to 99999 so they can be masked later
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
        try:
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
        except IndexError:
            print('\nSomething went wrong in the .DDF results prep--maybe it is missing?')
            passing_status = 'ERROR - MISSING DATA'
            failing_values = 'ERROR - MISSING DATA'
    return property_names, measure_vals, error_values, passing_status, failing_values


def ddf_table(property_names, property_values, error_values, passing_status, figure_index, lens_name, dbp_or_rtc):
    try:
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
        # ax.axis('tight')
        ax.axis('off')
        data_table = plt.table(cellText=table_cells, rowLabels=property_names,
                               colLabels=['Passing\nStatus', 'Measured\nValue', 'Exceeds Spec\nLimit By'],
                               rowColours=colors, loc='center')
        data_table.scale(1, 2.2)
        ax.set_title(lens_name + ', ' + dbp_or_rtc + ', Go-No-Go')
    except IndexError:
        print('Something went wrong with the DDF table, replacing it with placeholder, perhaps the DDF is missing?')
        ax = plt.subplot(230 + figure_index)
        ax.set_title('Error -- check if DDF exists')


# PMF Processing and Figure Creation
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
                        rotated_powermap = np.rot90(powermap, 2)
                        flipped_powermap = np.fliplr(rotated_powermap)
                        self.powermap = flipped_powermap


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

def display_dspc():
    pdf_filename = 'VFT ORBIT PLATFORM DSPC DATA.pdf'
    with PdfPages(pdf_filename) as pdf:
        for file in glob2.glob('Z:\\DSPC\\*DSPCVFT*.PMF'):
            powermap_figure = test_pmf(file,'POWERMAP','DSPC')
            plt.suptitle(os.path.basename(file))
            pdf.savefig(powermap_figure)
            plt.close(powermap_figure)

def average_pmf():
    test_dpt = {
        'JOB': 'dpt',
        'MEASURE_TYPE': 'E',
        'POWER_QUANTITY': 'D',
        'MEASURED_POWER_TYPE': 'T'
    }
    test_cyl = {
        'JOB': 'cyl',
        'MEASURE_TYPE': 'E',
        'POWER_QUANTITY': 'C',
        'MEASURED_POWER_TYPE': 'T'
    }

    #lens_tests = create_thrupower_tests()
    dpt_maps = []
    powermap_count = 1
    figure_index = 1
    measure_searches = ['COMPLETED_REPORTS\\**\*VERD*_RTC.PMF', 'COMPLETED_REPORTS\\**\*VERD*_DBP.PMF']
    for measure_search in measure_searches:
        lens_tests = [test_dpt, test_cyl]
        for test_used in lens_tests:
            powermap_count = 1
            for pmf_file in glob2.glob(measure_search):
                try:
                    print(pmf_file)
                    if powermap_count == 1:
                        test_used.update({'POWERMAP': np.square(PmfDataGet(pmf_file, test_used).powermap)})
                        powermap_count += 1
                        #visualize_powermap(test_dpt, 1, 110)
                        continue
                    test_used.update({'POWERMAP': test_used.get('POWERMAP') + np.square(PmfDataGet(pmf_file, test_used).powermap)})
                    #visualize_powermap(test_dpt, 1, 110)
                    #plt.show()
                    powermap_count += 1
                except:
                    continue
            test_used.update({'JOB': measure_search})
            average_powermap = test_used.update({'POWERMAP': np.sqrt(test_used.get('POWERMAP')/powermap_count)})
            visualize_powermap(test_used,figure_index,220)
            figure_index += 1
            #plt.show()
            print('Files averaged: ' + str(powermap_count))
    plt.show()


def angle_to_unit_vectors(angle_array):
    return np.cos(np.deg2rad(angle_array), np.sin(np.deg2rad(angle_array)))


def test_pmf(pmf_file,rtc_or_dbp,lens):
    powermap_figure = plt.figure('Powermap Data',figsize=(21,11))
    lens_tests = create_thrupower_tests()
    for tests, testparams in lens_tests.items():  # for each test in lens_tests, get the test parameters. lens_tests is defined towards the top of main, it defines which measurements are extracted from the .pmf data.
        testparams.update({'JOB': lens + ' ' + rtc_or_dbp})  # update the testparams with the lens the script is currently on and wheter it's dbp or rtc
    figure_count = 0
    for tests, testparams in lens_tests.items():  # iterate over the updated lens_tests dictionary
        figure_count = figure_count + 1
        testparams.update(
            {'POWERMAP': PmfDataGet(pmf_file, testparams).powermap})  # add a powermap to each testparams key
        #plt.subplots(120+figure_count)
        visualize_powermap(testparams,figure_count,120)
    return powermap_figure

def visualize_powermap(powermap_params, figure_index, figure_dimensions):
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
    ax1 = plt.subplot(figure_dimensions + figure_index)
    ax1.set_ylabel('Y position, mm')
    ax1.set_xlabel('X position, mm')
    ax1.set_title(subplot_name)
    copy_colormap = plt.cm.get_cmap('nipy_spectral', 30)
    colormap_list = [copy_colormap(i) for i in range(copy_colormap.N)]
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
    #plt.show()


# This function takes in the failing RTC and DBP measurements produced by ddf_results_prep and decides if the generator
# has passed the generator acceptance process.
def determine_genacc_test_pass(rtc_failing_results, dbp_failing_results, lens_list):
    lens_verdict_dictionary = {}
    for item in lens_list:
        lens_verdict_dictionary[item] = ''
    fail_count = 0
    for lens, failing_params in rtc_failing_results.items():
        if re.search('FULL_LENS GMC', str(failing_params)):
            if re.search('FULL_LENS GMC', str(dbp_failing_results[lens])):
                fail_count = fail_count + 1
                lens_verdict_dictionary[lens] = 'FULL_LENS GMC; '
        if re.search('Center Power Average', str(failing_params)) or re.search('Center GMC', str(failing_params)):
            if re.search('Center Power Average', str(dbp_failing_results[lens])) or re.search('Center GMC', str(
                    dbp_failing_results[lens])):
                lens_verdict_dictionary[lens] = lens_verdict_dictionary[lens] + ' CENTER DEFECT;'
        if re.search('FULL_LENS Power Average', str(failing_params)):
            if re.search('FULL_LENS Power Average', dbp_failing_results[lens]):
                lens_verdict_dictionary[lens] = lens_verdict_dictionary[lens] + ' CENTER THICKNESS; '
        if re.search('DBP Best Fit', str(failing_params)):
            lens_verdict_dictionary[lens] = lens_verdict_dictionary[lens] + ' POSITIONING; '
        if re.search('ERROR', str(failing_params)):
            lens_verdict_dictionary[lens] = 'ERROR CHECK FOR MISSING DATA'

    if fail_count > 1:
        test_result = 'FAIL'
    else:
        test_result = 'ACCEPTED'
    return lens_verdict_dictionary, test_result


def acceptance_result_figure(test_result_dictionary, test_result, lens_list):
    test_result_fig = plt.figure(99, figsize=(21, 11))  # figure number is 99 to prevent interference with other figures
    ax = plt.subplot(335)
    # ax.axis('tight')
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
            if re.search('FULL_LENS GMC', acceptance_string):
                colors.append((1, 0, 0))
                continue
            colors.append((1, .5, 0))  # (255,0,0))
    table_cells = acceptance_list
    acceptance_table = plt.table(cellText=table_cells, rowLabels=row_labels, colLabels=['Result'],
                                 rowColours=colors, loc='center', fontsize=25)
    acceptance_table.scale(1, 3)
    return test_result_fig


# Filename and File Manipulation
# This function takes in disogranized DLM data with a regular filename (LAB_GENERATORNUMBER_FASTTOOL_LENS_DBPORRTC.pmf/ddf)
# and organizes it in a lab\generator\fast tool\dbp or rtc file structure for easy access and human readability
def create_and_move_dlm_data(raw_data_and_extension, file_structure_location):
    for file in glob2.glob(raw_data_and_extension):
        lab, generator_number, fast_tool, lens, measure_type = genacc_rawdata_filename_get(file)
        structured_data_path = file_structure_location + '\\' + lab + '\\' + generator_number + '\\' + fast_tool + '\\' + measure_type + '_DATA'
        try:
            os.makedirs(structured_data_path)
        except FileExistsError:
            pass
        shutil.move(file, structured_data_path)


# The next three functions are all very similar implementaions of a regex search which returns different parts of a filename.
# Each is only used once or twice in the rest of the code, but including them inline would clutter things and perhaps
# cause even more confusion than having three similar functions.

# This function gets the different parts contained in a filepath (i.e., ddf and pmf filename as saved at the DLM)
# and returns them for use. It's used in main to name the .pdf file for saving.
def genacc_filename_get(abs_filepath):
    abs_filepath_regex = re.compile(r'\\([\w]+[\d]?)\\([\d]+[\w]?)\\(\w\w\d)')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    return lab, generator_number, fast_tool


# This function gets the different parts contained in the raw DLM data filename (i.e., ddf and pmf filename as saved at the DLM)
# and returns them for use in other functions (such as create_and_move_dlm_data)
def genacc_rawdata_filename_get(abs_filepath):
    abs_filepath_regex = re.compile(r'([\w]+[\d]?)_([\d]+[\w]?)_(\w\w\d)_(\w\w\w\w[\W]?[\d]?)_(\w\w\w)')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    lens = search_result.group(4)
    measure_type = search_result.group(5)
    return lab, generator_number, fast_tool, lens, measure_type


# This function gets the different parts contained in a filepath (i.e., ddf and pmf filename as saved at the DLM)
# and returns them for use. It's used in main to name the figures contained within the .pdf.
def genacc_figurename_get(abs_filepath):
    abs_filepath_regex = re.compile('\\\([\w]+)\\\([\d]+[\w]?)\\\(\w\w\d)\\\(\w\w\w)_DATA')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    measure_type = search_result.group(4)
    return lab, generator_number, fast_tool, measure_type


# List Manipulation Tools
def add_column(list1, list2):
    for index, row in enumerate(list1):
        row.append(list2[index])
    return list1


def row_to_column(list):
    transposed_list = []
    for i in range(len(list)):
        transposed_list.append([list[i]])
    return transposed_list


if __name__ == "__main__":
    #display_dspc()
    #test_pmf('Z:\DSPC\DSPCVFT_2019-01-11_11.23.13.PMF','POWERMAP','DSPC')
    main()
    #average_pmf()
