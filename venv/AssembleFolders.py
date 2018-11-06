import glob2
import re
import shutil
import os

#todo lab/generator/fast tool/rtc_or_dbp

def main():
    raw_data_and_extension_pmf = 'RAW_DATA_DUMP\*.PMF'
    raw_data_and_extension_ddf = 'RAW_DATA_DUMP\*.DDF'
    file_structure_location = 'STRUCTURED_GENACC_DATA'
    create_and_move_dlm_data(raw_data_and_extension_pmf,file_structure_location)
    create_and_move_dlm_data(raw_data_and_extension_ddf, file_structure_location)
    #for file in glob2.glob('RAW_DATA_DUMP\*.PMF'):
    #    #print(file)
    #    lab, generator_number, fast_tool, lens, measure_type = genacc_filename_get(file)
    #    structured_data_path = 'STRUCTURED_GENACC_DATA\\'+lab+'\\'+generator_number+'\\'+fast_tool+'\\'+measure_type+'_DATA'
    #    try:
    #        os.makedirs(structured_data_path)
    #    except FileExistsError:
    #        pass
    #    shutil.copy(file,structured_data_path)
    #for file in glob2.glob('RAW_DATA_DUMP\*.PMF'):
    #    #print(lab + generator_number + fast_tool + measure_type)
    #print(lab_dictionary)
    return 0

def create_and_move_dlm_data(raw_data_and_extension,file_structure_location):
    for file in glob2.glob(raw_data_and_extension):
        #print(file)
        lab, generator_number, fast_tool, lens, measure_type = genacc_rawdata_filename_get(file)
        structured_data_path = file_structure_location+'\\'+lab+'\\'+generator_number+'\\'+fast_tool+'\\'+measure_type+'_DATA'
        try:
            os.makedirs(structured_data_path)
        except FileExistsError:
            pass
        shutil.copy(file,structured_data_path)

def genacc_rawdata_filename_get(abs_filepath):
    abs_filepath_regex = re.compile(r'([\w]+[\d]?)_([\d]+[\w]?)_(\w\w\d)_(\w\w\w\w[\W]?[\d]?)_(\w\w\w)')
    search_result = re.search(abs_filepath_regex, abs_filepath)
    lab = search_result.group(1)
    generator_number = search_result.group(2)
    fast_tool = search_result.group(3)
    lens = search_result.group(4)
    measure_type = search_result.group(5)
    return lab, generator_number, fast_tool, lens, measure_type

if __name__ == "__main__":
    main()