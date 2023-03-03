import cnst as c
import helper as h

h.prepare_clean_tmp_folder('tmp_k7')

es = h.ExpSession('08.02.23_Poly_grad_1000_NaCl.zip')
es.create_tables()
es.find_session_json()
es.fill_file_table('08.02.23/andor_ts_8-9_feb2023.txt')
# quit()
es.fill_spots_table()
es.fill_jpg_file_table('clickerino_ts_8-9_feb2023.txt')

es.update_spectra_timestamps_in_file_table()

# es.print_reference_file_names()
es.fill_reference_sets((
    ('08.02.23/refs/white01.asc',
     '08.02.23/refs/darkForWhite01.asc',
     '08.02.23/refs/dark01.asc',
     c.UNPOL),
    ('08.02.23/refs/white02.asc',
     '08.02.23/refs/darkForWhite02.asc',
     '08.02.23/refs/dark02.asc',
     c.P_POL),
    ('08.02.23/refs/white03.asc',
     '08.02.23/refs/darkForWhite03.asc',
     '08.02.23/refs/dark03.asc',
     c.S_POL),
    ('08.02.23/refs/white04.asc',
     '08.02.23/refs/darkForWhite04.asc',
     '08.02.23/refs/dark04.asc',
     c.UNPOL),
    ('08.02.23/refs/white05.asc',
     '08.02.23/refs/darkForWhite05.asc',
     '08.02.23/refs/dark05.asc',
     c.S_POL),
    ('08.02.23/refs/white06.asc',
     '08.02.23/refs/darkForWhite06.asc',
     '08.02.23/refs/dark06.asc',
     c.P_POL)
))

es.plot_reference_sets()

es.config_series()

es.assign_img_to_spectra()
es.plotspectra()
