AIR = 'Air'
H2O = 'Water'
EtOH = 'EtOH'
NaCl_04 = 'NaCl04'
NaCl_10 = 'NaCl10'
NaCl_16 = 'NaCl16'
NaCl_22 = 'NaCl22'
VEGF1000 = 'VEGF1000'
VEGF500 = 'VEGF500'
VEGF100 = 'VEGF100'
BSA = 'BSA'
DNS2h = 'DNS2h'
DNS = 'DNS'
PBS = 'PBS'


POL = 'pol'
P_POL = 'P-pol'
S_POL = 'S-pol'
UNPOL = 'unpol'
NM = 'nm'

RI = {AIR: 1.0,
      H2O: 1.333,
      EtOH: 1.3630,
      NaCl_04: 1.3400,
      NaCl_10: 1.3505,
      NaCl_16: 1.3612,
      NaCl_22: 1.3721}

COLR = {AIR: u'#1f77b4',
        H2O: u'#ff7f0e',
        EtOH: u'#2ca02c',
        NaCl_04: u'#d62728',
        NaCl_10: u'#9467bd',
        NaCl_16: u'#8c564b',
        NaCl_22: u'#e377c2'}


S1409 = 's1409poly'
S0709 = 's0709mono'

DARK = 'dark'
DARK_FOR_WHITE = 'dark_for_white'
WHITE = 'white'
SPECTRUM = 'spectrum'

COL_DARK = DARK
COL_DARK_FOR_WHITE = DARK_FOR_WHITE
COL_WHITE = WHITE


COL_REF_TYPE = 'ref_type'
COL_FILE_TYPE = 'file_type'

DBFILE = 'sensorfilm.sqlite3'

FILE_TABLE = 'files'
JPG_FILE_TABLE = 'jpg_files'
EXPERIMENTS_TABLE = 'experiments'
SPOTS_TABLE = 'spots'
REF_SETS_TABLE = 'ref_sets'


COL_MEMBER_FILE_NAME = 'member_file_name'
COL_JPG_FILE_NAME = 'jpg_file_name'
COL_SIF_FILE = 'sif_file'
COL_TXT_FILE = 'txt_file'
COL_ASC_FILE = 'asc_file'
COL_SPOT = 'spot'
COL_SERIES = 'series'
COL_TSTAMP = 'tstamp'
COL_SAMPLE = 'sample'
COL_MEDIUM = 'medium'
COL_MASTERFILE = 'masterfile'
COL_XPOS = 'xpos'
COL_YPOS = 'ypos'
COL_DAY = 'day'
COL_RI = 'ri'
COL_POL = 'pol'
COL_LINE = 'line'
COL_NAME = 'name'
COL_START_TIME = 'start_time'

REFS = {DARK_FOR_WHITE: {S0709: 'tumsa_balt_ref_2diena', S1409: 'tumsa_balta1509'},
        DARK: {S0709: '2_tumsa_merijumiem', S1409: 'tumsa1509'},
        WHITE: {S0709: '2_balt_ref_kvarcs_2diena', S1409: 'ref_uz_kvarca1509'}}

YLIM = {S0709: [-0.05, 0.35],
        S1409: [-0.01, 0.08]}


ZLIM = {S0709: [0.05, 0.4],
        S1409: [0.01, 0.08]}

ZLIM2 = {S0709: [-0.1, 0.1],
         S1409: [-0.03, 0.03]}


INDEX_JSON = '00_index.json'

A4_width_in = 8.27
A4_height_in = 11.69
A4_size_in = (A4_width_in, A4_height_in)

OUTPUTTYPE = ".pdf"
DPI = 300
