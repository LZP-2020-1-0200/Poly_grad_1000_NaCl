import helper as h

h.prepare_clean_tmp_folder('tmp_k7')

es = h.ExpSession('08.02.23_Poly_grad_1000_NaCl.zip')
es.create_tables()
es.find_session_json()
es.fill_file_table('08.02.23/andor_ts_8-9_feb2023.txt')
# quit()
es.fill_spots_table()


es.fill_jpg_file_table('clickerino_ts_8-9_feb2023.txt')
