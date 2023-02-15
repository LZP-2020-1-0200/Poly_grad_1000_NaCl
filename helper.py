import os
import zipfile
import sqlite3
import cnst as c
import json


def prepare_clean_tmp_folder(folder_name):
    global OUTFOLDER
    OUTFOLDER = folder_name
    if os.path.exists(folder_name):
        for f in os.listdir(folder_name):
            os.remove(os.path.join(folder_name, f))
    else:
        os.mkdir(folder_name)


class ExpSession:

    def __init__(self, zipfilename):
        self.session_json_filename = None
        self.spectra_timestamps_file_name = None
        self.zf = zipfile.ZipFile(zipfilename, "r")
        print('ZipFile opened')
        self.con = sqlite3.connect(f"{OUTFOLDER}/{c.DBFILE}")
        self.cur = self.con.cursor()
        self.cur.execute("PRAGMA foreign_keys = ON")

    def __del__(self):
        self.zf.close()
        print('ZipFile closed')
        self.con.commit()
        print('DB committed')

    def find_session_json(self):
        for member_file_name in self.zf.namelist():
            if 'session.json' in member_file_name:
                self.session_json_filename = member_file_name
                print(f"session_json_filename = {self.session_json_filename}")

    def create_tables(self):
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

    def fill_file_table(self,andor_timestamps_file_name):
        ignorelist = ('08.02.23/session.json',
                      '08.02.23/pieraksti.txt',
                      'xxx',
                      'xxx',
                      'xxx'
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
        print(f"spectra_timestamps_file_name = {self.spectra_timestamps_file_name}")
