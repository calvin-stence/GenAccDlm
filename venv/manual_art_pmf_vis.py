import importlib
import glob2
import os
import shutil
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.image as mpimg
import numpy as np
import matplotlib.patheffects as path_effects
import pmf_extractor
import ddf_extractor


dspc_network_datapath = 'Z:\\*first_polar*'
eto_dspc_datapath = 'test_input/eto_dspc/**/'
datapath_tac = 'test_input/tac_deformation/Onbit TAC DLM Measures/**/'
datapath = {#'ETO_DSPC':eto_dspc_datapath,
            'PLATFORM_DSPC': dspc_network_datapath}#,
            #'ONBIT_TAC': datapath_tac}
for names, paths in datapath.items():
    figure_count = 1
    figure_index = 0
    with PdfPages(names+'.pdf') as pdf:
        for file in glob2.glob(paths + '*.PMF'):
            #ddf_filepath = re.sub('PMF','DDF',file)
            print('Generating figures for file ' + file)
            pmf_obj = pmf_extractor.PmfPowermapsGet(file, figures_to_generate=['RFCM','RFDM'])
            #ddf_obj = ddf_extractor.DdfDataGet(ddf_filepath)
            if pmf_obj.lens_id_search:
                lens_id = pmf_obj.base
            else:
                lens_id = os.path.basename(file)
            fig, axs = plt.subplots(nrows=2, ncols=len(pmf_obj.figures_to_generate), figsize=(30, 14))
            plt.suptitle(pmf_obj.lens_description, size=40)
            figure_index = 0
            for fig_ids in pmf_obj.figures_to_generate:
                pmf_id = pmf_extractor.PmfId(fig_ids)
                graph_text_size=20
                plt.sca(axs[0][figure_index])
                try:
                    pmf_obj.visualize_dlm_pmf(fig_ids,v_max=.25,v_min=-.25)
                except KeyError:
                    no_data_label = plt.text(.5,.5,'Missing\nData',
                                             size=35)  # add a label to the DBP figure row (the positions are hardcoded, foresight would have used axes and zip to do this in a dynamic way
                    no_data_label.set_path_effects([path_effects.Normal()])
                    figure_index+=1
                    continue
                x0, y0 = 5, 20
                x1, y1, = 35, 20
                x0_90, y0_90 = 20, 5
                x1_90, y1_90 = 20, 35
                output_data = pmf_obj.powermaps.get(fig_ids)
                output_data[abs(output_data) > 9999] = np.nan
                zi, x, y = pmf_extractor.array_transect(x0, y0, x1, y1, output_data,smooth='cubic')
                zi_90, x_90, y_90 = pmf_extractor.array_transect(x0_90, y0_90, x1_90, y1_90, output_data,smooth='cubic')
                plt.sca(axs[0][figure_index])
                plt.plot([x0-20, x1-20], [y0-20, y1-20], 'ro-',linewidth=5,markersize=20,alpha=.8)
                plt.plot([x0_90-20, x1_90-20], [y0_90-20, y1_90-20], 'bo-',linewidth=5,markersize=20,alpha=.8)
                plt.sca(axs[1][figure_index])
                plt.plot(x-20, zi,'r',linewidth=4)
                plt.plot(y_90-20, zi_90,'b',linewidth=4)
                plt.title('Transect Curves of\n ' + pmf_id.pmf_id_minimal,size=18)
                plt.xlabel('Position, mm')
                plt.ylabel('Power, dpt')
                figure_index += 1
            figure_count+=1
            plt.subplots_adjust(wspace=.23)
            pdf.savefig(fig)
            print('Figures created: ' + str(figure_count-1))
            plt.close(fig)

