import os
import zipfile
import sqlite3
import cnst as c
import json
from matplotlib import pyplot as plt
from andor_asc import load_andor_asc
import numpy as np
import matplotlib.cm as cm
from subprocess import check_output
import matplotlib.image as mpimg
from io import BytesIO
from PIL import Image
# ===========================================================


def prepare_clean_tmp_folder(folder_name):
    global OUTFOLDER
    OUTFOLDER = folder_name
    if os.path.exists(folder_name):
        for f in os.listdir(folder_name):
            os.remove(os.path.join(folder_name, f))
    else:
        os.mkdir(folder_name)


class ExpSession:

    def __init__(self, zipfilename):  # ===========================================================
        self.session_json_filename = None
        self.spectra_timestamps_file_name = None
        self.zf = zipfile.ZipFile(zipfilename, "r")
        print('ZipFile opened')
        self.con = sqlite3.connect(f"{OUTFOLDER}/{c.DBFILE}")
        self.cur = self.con.cursor()
        self.cur.execute("PRAGMA foreign_keys = ON")

    def __del__(self):  # ===========================================================
        self.zf.close()
        print('ZipFile closed')
        self.con.commit()
        print('DB committed')
        check_output(
            f"pdftk {OUTFOLDER}\\*.pdf cat output all_spectra.pdf", shell=True).decode()

    # ===========================================================

    def find_session_json(self):
        for member_file_name in self.zf.namelist():
            if 'session.json' in member_file_name:
                self.session_json_filename = member_file_name
                print(f"session_json_filename = {self.session_json_filename}")

    def create_tables(self):  # ===========================================================
        self.cur.execute(f"DROP TABLE IF EXISTS {c.JPG_FILE_TABLE}")
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.JPG_FILE_TABLE}(
            {c.COL_JPG_FILE_NAME} TEXT PRIMARY KEY,
            {c.COL_TSTAMP} TEXT UNIQUE NOT NULL) """)

        self.cur.execute(f"DROP TABLE IF EXISTS {c.EXPERIMENTS_TABLE}")
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.EXPERIMENTS_TABLE}(
            {c.COL_SERIES} TEXT PRIMARY KEY,
            {c.COL_DARK} TEXT,
            {c.COL_DARK_FOR_WHITE} TEXT,
            {c.COL_WHITE} TEXT,
            {c.COL_MEDIUM} TEXT,
            {c.COL_POL} TEXT,
            {c.COL_NAME} TEXT,
            {c.COL_START_TIME} TEXT
            )""")

        self.cur.execute(f"DROP TABLE IF EXISTS {c.SPOTS_TABLE}")
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.SPOTS_TABLE}(
            {c.COL_SPOT} TEXT PRIMARY KEY,
            {c.COL_XPOS} INTEGER,
            {c.COL_YPOS} INTEGER,
            {c.COL_LINE} INTEGER )""")

        self.cur.execute(f"DROP TABLE IF EXISTS {c.FILE_TABLE}")
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.FILE_TABLE}(
            {c.COL_MEMBER_FILE_NAME} TEXT PRIMARY KEY,
            {c.COL_FILE_TYPE} TEXT NOT NULL,
            {c.COL_SERIES} TEXT,
            {c.COL_SPOT} TEXT,
            {c.COL_TSTAMP} TEXT,
            {c.COL_JPG_FILE_NAME} TEXT,
            FOREIGN KEY ({c.COL_SERIES}) REFERENCES {c.EXPERIMENTS_TABLE} ({c.COL_SERIES}) ,
            FOREIGN KEY ({c.COL_SPOT}) REFERENCES {c.SPOTS_TABLE} ({c.COL_SPOT}),
            FOREIGN KEY ({c.COL_JPG_FILE_NAME}) REFERENCES {c.JPG_FILE_TABLE} ({c.COL_JPG_FILE_NAME})
            )""")

        self.cur.execute(f"DROP TABLE IF EXISTS {c.REF_SETS_TABLE}")
        self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.REF_SETS_TABLE}(
            {c.COL_WHITE} TEXT PRIMARY KEY,
            {c.COL_DARK_FOR_WHITE} TEXT NOT NULL,
            {c.DARK} TEXT NOT NULL,
            {c.COL_POL} TEXT NOT NULL,
            FOREIGN KEY ({c.COL_WHITE}) REFERENCES {c.FILE_TABLE} ({c.COL_MEMBER_FILE_NAME}),
            FOREIGN KEY ({c.COL_DARK_FOR_WHITE}) REFERENCES {c.FILE_TABLE} ({c.COL_MEMBER_FILE_NAME}),
            FOREIGN KEY ({c.DARK}) REFERENCES {c.FILE_TABLE} ({c.COL_MEMBER_FILE_NAME})
            )""")

    # ===========================================================
    def fill_spots_table(self):
        with self.zf.open(self.session_json_filename) as session_jsf:
            session_json_object = json.load(session_jsf)
        print(session_json_object.keys())
        points = session_json_object['points']
        point_nr = 0
        lines = {}
        for point in points:
            #        print(point)
            line = point_nr // 100
            lines[line] = line
    #        print(line)
            self.cur.execute(f"""UPDATE {c.SPOTS_TABLE} SET
                {c.COL_XPOS} = ?,
                {c.COL_YPOS} = ?,
                {c.COL_LINE} = ?
            WHERE {c.COL_SPOT} = ? """,
                             [point['x'], point['y'], line, point['filename']])
            if self.cur.rowcount != 1:
                print(point)
            point_nr += 1

    # ===========================================================
    def fill_jpg_file_table(self, jpg_timestamps_fn):
        for member_file_name in self.zf.namelist():
            if jpg_timestamps_fn in member_file_name:
                jpg_ts_filename = member_file_name
                with self.zf.open(jpg_ts_filename) as jpg_timestamps_file:
                    jpg_timestamps_data = jpg_timestamps_file.read()
                    jpg_timestamps_lines = jpg_timestamps_data.decode(
                        'ascii').splitlines()
                    for timestamps_line in jpg_timestamps_lines:
                        # print(timestamps_line)
                        jpg_ts_parts = timestamps_line.strip(
                            "\n\r").split("\t")
                        if '.jpg' in jpg_ts_parts[0]:
                            jpg_filename = jpg_ts_parts[0][3:]
                            jpg_ts = jpg_ts_parts[1]
                            # print(jpg_filename)
                            self.cur.execute(f"""INSERT INTO {c.JPG_FILE_TABLE}
                                ({c.COL_JPG_FILE_NAME},{c.COL_TSTAMP})
                                VALUES (?,?)""",
                                             [jpg_filename.replace("\\", "/"), jpg_ts])
                print('JPG Timestamps loaded')
                break

    # ===========================================================
    def fill_file_table(self, andor_timestamps_file_name):
        ignorelist = ('08.02.23/session.json',
                      '08.02.23/pieraksti.txt',
                      'xyz',
                      'xyz',
                      'xyz'
                      )

        for member_file_name in self.zf.namelist():
            if member_file_name in ignorelist:
                continue
            if member_file_name[-1] == '/':
                continue
            if 'clickerino' in member_file_name:
                continue
            if 'Thumbs.db' in member_file_name:
                continue
            if '/imgs/experiments' in member_file_name:
                continue
            if '/refs/white' in member_file_name:
                self.cur.execute(f"""INSERT INTO {c.FILE_TABLE}
                    ({c.COL_MEMBER_FILE_NAME},{c.COL_FILE_TYPE})
                    VALUES (?,?)""",
                                 [member_file_name, c.WHITE])
                continue
            if '/refs/darkForWhite' in member_file_name:
                self.cur.execute(f"""INSERT INTO {c.FILE_TABLE}
                    ({c.COL_MEMBER_FILE_NAME},{c.COL_FILE_TYPE})
                    VALUES (?,?)""",
                                 [member_file_name, c.DARK_FOR_WHITE])
                continue
            if '/refs/dark' in member_file_name:
                self.cur.execute(f"""INSERT INTO {c.FILE_TABLE}
                    ({c.COL_MEMBER_FILE_NAME},{c.COL_FILE_TYPE})
                    VALUES (?,?)""",
                                 [member_file_name, c.DARK])
                continue
            if member_file_name.endswith(".asc"):
                file_name_parts = member_file_name.split('/')
                series = file_name_parts[2]
                self.cur.execute(f"""INSERT OR IGNORE INTO {c.EXPERIMENTS_TABLE}
                    ({c.COL_SERIES}) VALUES (?)""", [series])
                spot = file_name_parts[3]
                # print(spot)
                self.cur.execute(f"""INSERT OR IGNORE INTO {c.SPOTS_TABLE}
                    ({c.COL_SPOT}) VALUES (?)""", [spot])
                self.cur.execute(f"""INSERT INTO {c.FILE_TABLE}
                ({c.COL_MEMBER_FILE_NAME},{c.COL_FILE_TYPE},{c.COL_SERIES},{c.COL_SPOT})
                    VALUES (?,?,?,?)""",
                                 [member_file_name, c.SPECTRUM, series, spot])
                continue
            if andor_timestamps_file_name in member_file_name:
                self.spectra_timestamps_file_name = member_file_name
                continue

            print(member_file_name)
        print(
            f"spectra_timestamps_file_name = {self.spectra_timestamps_file_name}")

    # ===========================================================
    def update_spectra_timestamps_in_file_table(self):
        with self.zf.open(self.spectra_timestamps_file_name) as spectra_timestamps_file:
            spectra_timestamps_data = spectra_timestamps_file.read()
            timestamps_lines = spectra_timestamps_data.decode(
                'ascii').splitlines()
        for timestamps_line in timestamps_lines:
            timestamps_line_parts = timestamps_line.split("\t")
            # print(timestamps_line_parts)
            timestamp = timestamps_line_parts[1]
            member_file_name = timestamps_line_parts[0][3:].replace('\\', '/')
            # print(member_file_name)

            self.cur.execute(f"""UPDATE {c.FILE_TABLE} SET
                {c.COL_TSTAMP} = ?
            WHERE {c.COL_MEMBER_FILE_NAME} = ? """,
                             [timestamp, member_file_name])
            if self.cur.rowcount > 1:
                print(self.cur.rowcount)
                print(timestamps_line_parts)

    # ===========================================================
    def print_reference_file_names(self):
        self.cur.execute(f"""SELECT
                    {c.COL_TSTAMP},
                    {c.COL_MEMBER_FILE_NAME},
                    {c.COL_FILE_TYPE}
            FROM    {c.FILE_TABLE}
            WHERE   {c.COL_FILE_TYPE} ='{c.DARK}'
                OR  {c.COL_FILE_TYPE} ='{c.DARK_FOR_WHITE}'
                OR  {c.COL_FILE_TYPE} ='{c.WHITE}'
            ORDER BY {c.COL_TSTAMP}
            """)
        for sel_refs_rez in self.cur.fetchall():
            print(sel_refs_rez)

    # ===========================================================
    def fill_reference_sets(self, reference_sets):
        for refset in reference_sets:
            #print(f"refset = {refset}")
            self.cur.execute(f"""INSERT INTO {c.REF_SETS_TABLE}
            ({c.COL_WHITE},{c.COL_DARK_FOR_WHITE},{c.DARK},{c.COL_POL})
            VALUES (?,?,?,?)""", refset)

    # ===========================================================
    def plot_reference_sets(self):
        self.cur.execute(f"""SELECT
                    {c.COL_WHITE},
                    {c.COL_DARK_FOR_WHITE},
                    {c.DARK},
                    {c.COL_POL}
            FROM    {c.REF_SETS_TABLE}
            ORDER BY {c.COL_WHITE}
            """)

        fig = plt.figure()
        plt.rcParams.update({'font.size': 8})
        fig.set_figheight(c.A4_width_in)
        fig.set_figwidth(c.A4_height_in)
        subplot_shape = (2, 4)
        ax_white = plt.subplot2grid(
            shape=subplot_shape, loc=(0, 1), colspan=2, rowspan=1)
        ax_dfw = plt.subplot2grid(
            shape=subplot_shape, loc=(1, 0), colspan=2, rowspan=1)
        ax_dark = plt.subplot2grid(
            shape=subplot_shape, loc=(1, 2), colspan=2, rowspan=1)
        axs = (ax_white, ax_dfw, ax_dark)

        for sel_refsets_rez in self.cur.fetchall():
            # print(sel_refsets_rez)
            polarization = sel_refsets_rez[3]
            for ref_type_n in range(3):
             #               print(ref_type_n)
                raw_ref = load_andor_asc(
                    '', self.zf.read(sel_refsets_rez[ref_type_n]))

                axs[ref_type_n].plot(
                    raw_ref['col1'], raw_ref['col2'], label=f"{sel_refsets_rez[ref_type_n].split('/')[-1]}, {polarization}")

        subplot_titles = (c.WHITE, c.DARK_FOR_WHITE, c.DARK)
        for ref_type_n in range(3):
            axs[ref_type_n].set(xlabel='$\\lambda$, nm')
            axs[ref_type_n].set(ylabel='counts')
            axs[ref_type_n].set(
                xlim=[min(raw_ref['col1']), max(raw_ref['col1'])])
            axs[ref_type_n].legend(loc="best")
            axs[ref_type_n].grid()
            axs[ref_type_n].title.set_text(subplot_titles[ref_type_n])
        plt.tight_layout()
        # plt.show()
        plt.savefig(f"{OUTFOLDER}/0_references{c.OUTPUTTYPE}", dpi=c.DPI)
        plt.close()

        print("REFERENCES OK")

        # self.cur.execute(f"""CREATE TABLE IF NOT EXISTS {c.REF_SETS_TABLE}(
        #     {c.COL_WHITE} TEXT PRIMARY KEY,
        #     {c.COL_DARK_FOR_WHITE} TEXT NOT NULL,
        #     {c.DARK} TEXT NOT NULL,
        #     {c.COL_POL} TEXT NOT NULL,
# ===========================================================
    def config_series(self):
        with self.zf.open(self.session_json_filename) as session_jsf:
            session_json_object = json.load(session_jsf)
            experiments = session_json_object['experiments']
            print(experiments[0].keys())
            for experiment in experiments:
             #               print(experiment)
                series = experiment['folder'].split('\\')[-1]
                white = None
                dark_for_white = None
                dark = None
                reference_polarization = None
                ref_search = 'undefined'

                medium = None
                pol = None
                name = experiment['name']
                start_time = experiment['timestamp']

                if 'reflectance' in name:
                    pol = c.UNPOL
                elif 's-pol' in name:
                    pol = c.S_POL
                elif 'p-pol' in name:
                    pol = c.P_POL

                if series in ['001']:
                    ref_search = 'white01'
                elif series in ['002']:
                    ref_search = 'white02'
                elif series in ['003']:
                    ref_search = 'white03'
                elif pol == c.UNPOL:
                    ref_search = 'white04'
                elif pol == c.S_POL:
                    ref_search = 'white05'
                elif pol == c.P_POL:
                    ref_search = 'white06'

                self.cur.execute(f"""SELECT
                            {c.COL_WHITE},
                            {c.COL_DARK_FOR_WHITE},
                            {c.DARK},
                            {c.COL_POL}
                    FROM    {c.REF_SETS_TABLE}
                    WHERE   {c.COL_WHITE}  LIKE ?
                    ORDER BY {c.COL_WHITE}
                    """, ['%'+ref_search+'.asc'])

                for sel_refsets_rez in self.cur.fetchall():
                    white = sel_refsets_rez[0]
                    dark_for_white = sel_refsets_rez[1]
                    dark = sel_refsets_rez[2]
                    reference_polarization = sel_refsets_rez[3]

                if c.VEGF1000 in name:
                    medium = c.VEGF1000
                elif c.VEGF500 in name:
                    medium = c.VEGF500
                elif c.VEGF100 in name:
                    medium = c.VEGF100
                elif c.BSA in name:
                    medium = c.BSA
                elif c.DNS2h in name:
                    medium = c.DNS2h
                elif c.DNS in name:
                    medium = c.DNS
                elif c.PBS in name:
                    medium = c.PBS

                elif c.NaCl_22 in name:
                    medium = c.NaCl_22
                elif c.NaCl_16 in name:
                    medium = c.NaCl_16
                elif c.NaCl_10 in name:
                    medium = c.NaCl_10
                elif 'NaCl4' in name:
                    medium = c.NaCl_04
                elif 'ater' in name:
                    medium = c.H2O
                elif c.AIR in name:
                    medium = c.AIR
                elif 'air-' in name:
                    medium = c.AIR

                insert = [white, dark_for_white, dark,
                          medium, pol, name, start_time, series]
#                print (insert)

                if pol == reference_polarization:
                    self.cur.execute(f"""UPDATE {c.EXPERIMENTS_TABLE} SET
                        {c.COL_WHITE} = ?,
                        {c.COL_DARK_FOR_WHITE} = ?,
                        {c.COL_DARK} = ?,
                        {c.COL_MEDIUM} = ?,
                        {c.COL_POL} = ?,
                        {c.COL_NAME} = ?,
                        {c.COL_START_TIME} =?
                    WHERE {c.COL_SERIES} = ? """,
                                     insert)
#                    if self.cur.rowcount != 1:
#                       print(insert)
# ===========================================================

    def assign_img_to_spectra(self):
        self.cur.execute(f"""SELECT
                {c.COL_MEMBER_FILE_NAME},
                {c.COL_TSTAMP}
                    FROM {c.FILE_TABLE}
                    WHERE {c.COL_SPOT} NOT NULL
                    AND {c.COL_JPG_FILE_NAME} IS NULL
                    ORDER BY {c.COL_TSTAMP}
            """)
        for rez_spot_wo_jpg in self.cur.fetchall():
            # print(rez_spot_wo_jpg)
            self.cur.execute(
                f"""SELECT {c.COL_JPG_FILE_NAME}, {c.COL_TSTAMP}
                    FROM {c.JPG_FILE_TABLE}
                    WHERE {c.COL_TSTAMP} < ?
                    ORDER BY {c.COL_TSTAMP} DESC
                    LIMIT 1""", [rez_spot_wo_jpg[1]])
            for rez_jpg_select in self.cur.fetchall():
                # print(rez_jpg_select)
                self.cur.execute(f"""UPDATE {c.FILE_TABLE} SET
                        {c.COL_JPG_FILE_NAME} = ?
                    WHERE {c.COL_MEMBER_FILE_NAME} = ? """,
                                 [rez_jpg_select[0], rez_spot_wo_jpg[0]])
                if self.cur.rowcount != 1:
                    print(rez_jpg_select)

    # ===========================================================
    def plotspectra(self):
        for pol in (c.UNPOL, c.S_POL, c.P_POL):
            print(f"pol = {pol}")
            self.cur.execute(f"""SELECT
                {c.COL_SPOT},
                {c.COL_XPOS},
                {c.COL_YPOS},
                {c.COL_LINE}
                    FROM {c.SPOTS_TABLE}
                    ORDER BY {c.COL_SPOT}
                    LIMIT 333
            """)
            for sel_spots_rez in self.cur.fetchall():
                selected_spot = sel_spots_rez[0]
                selected_xpos = sel_spots_rez[1]
                selected_ypos = sel_spots_rez[2]
                selected_line = sel_spots_rez[3]

                fig = plt.figure()
                plt.rcParams.update({'font.size': 8})
                fig.set_figheight(c.A4_width_in)
                fig.set_figwidth(c.A4_height_in)

                subplot_shape = (4, 4)
                ax_spectra = plt.subplot2grid(
                    shape=subplot_shape, loc=(0, 0), colspan=2, rowspan=2)
                ax_delta = plt.subplot2grid(
                    shape=subplot_shape, loc=(2, 0), colspan=2, rowspan=2)
                ax_img0 = plt.subplot2grid(
                    shape=subplot_shape, loc=(0, 2))
                ax_img1 = plt.subplot2grid(
                    shape=subplot_shape, loc=(0, 3))
                ax_img2 = plt.subplot2grid(
                    shape=subplot_shape, loc=(1, 2))
                ax_img3 = plt.subplot2grid(
                    shape=subplot_shape, loc=(1, 3))
                ax_img4 = plt.subplot2grid(
                    shape=subplot_shape, loc=(2, 2))
                ax_img5 = plt.subplot2grid(
                    shape=subplot_shape, loc=(2, 3))
                ax_img6 = plt.subplot2grid(
                    shape=subplot_shape, loc=(3, 2))
                ax_imgs = (ax_img0, ax_img1, ax_img2,
                           ax_img3, ax_img4, ax_img5, ax_img6)

                self.cur.execute(f"""SELECT
                    {c.COL_SERIES},
                    {c.COL_DARK},
                    {c.COL_DARK_FOR_WHITE},
                    {c.COL_WHITE},
                    {c.COL_MEDIUM},
                    {c.COL_NAME},
                    {c.COL_START_TIME}
                        FROM    {c.EXPERIMENTS_TABLE}
                        WHERE   {c.COL_POL}  = ?
                        ORDER BY {c.COL_START_TIME}
                """, [pol])

                plot_index = -1
                for sel_experiment_rez in self.cur.fetchall():
                    plot_index += 1

                    selected_series = sel_experiment_rez[0]
                    selected_dark = sel_experiment_rez[1]
                    selected_dark_for_white = sel_experiment_rez[2]
                    selected_white = sel_experiment_rez[3]
                    selected_medium = sel_experiment_rez[4]
                    selected_name = sel_experiment_rez[5]
                    selected_start_time = sel_experiment_rez[6]

                    self.cur.execute(f"""SELECT
                        {c.COL_MEMBER_FILE_NAME},
                        {c.COL_FILE_TYPE},
                        {c.COL_TSTAMP},
                        {c.COL_JPG_FILE_NAME}
                            FROM    {c.FILE_TABLE}
                            WHERE   {c.COL_SERIES} = ?
                            AND     {c.COL_SPOT} =?
                        ORDER BY {c.COL_TSTAMP}
                        """, [selected_series, selected_spot])
                    for sel_file_rez in self.cur.fetchall():
                        sel_file_name = sel_file_rez[0]
                        sel_file_type = sel_file_rez[1]
                        sel_tstamp = sel_file_rez[2]
                        sel_jpg_file_name = sel_file_rez[3]

                        andor_dark = load_andor_asc(
                            '', self.zf.read(selected_dark))
                        series_nm = np.array(andor_dark['col1'])
                        series_dark = np.array(andor_dark['col2'])
                        series_dfw = load_andor_asc(
                            '', self.zf.read(selected_dark_for_white))['col2']
                        series_white = load_andor_asc(
                            '', self.zf.read(selected_white))['col2']
                        ref = np.array(series_white)-np.array(series_dfw)
                        raw_spec = np.array(load_andor_asc(
                            '', self.zf.read(sel_file_name))['col2'])
                        Q = np.divide(raw_spec-series_dark, ref)
                        ax_spectra.plot(series_nm, Q,
                                        label=f"{sel_file_name[21:24]}, {selected_name}", color=cm.jet(plot_index/7))
                        
                        pfit = np.polyfit(series_nm, Q, 1)
                        pval=np.polyval(pfit,series_nm)
                        delta=Q-pval
                        ax_delta.plot(series_nm, delta, color=cm.jet(plot_index/7))
                        


                        zimg = self.zf.read(sel_jpg_file_name)
                        with open("tmp_img.jpg", "wb") as tmpjpgfile:
                            tmpjpgfile.write(zimg)
                        original_jpg = mpimg.imread("tmp_img.jpg")
                        ax_imgs[plot_index].imshow(original_jpg)
                        ax_imgs[plot_index].set(title=selected_medium)

  #                      read(file_in_zip)
                        # Image.open(ifile)#
                        #dataEnc = StringIO(data)
                        #img = Image.open(zimg)
#                        original_jpg = Image.open(BytesIO(zimg))
 #                       ax_imgs[plot_index].imshow(original_jpg)

                ax_spectra.legend(bbox_to_anchor=(0.0, -0.1),
                                  loc='upper left', ncol=3)
                ax_spectra.set(title=selected_spot)

                for ax in [ax_spectra, ax_delta]:
                    ax.set(xlabel="λ, nm")
                    ax.set(ylabel="counts")
                    ax.grid()
                    ax.set(xlim=[min(series_nm), max(series_nm)])

                for ax_img in ax_imgs:
                    ax_img.axis('off')

                plt.tight_layout()
                # plt.show()
                plt.savefig(
                    f"{OUTFOLDER}/{pol}_{selected_spot.split('.')[0]}{c.OUTPUTTYPE}", dpi=c.DPI)
                plt.close()
