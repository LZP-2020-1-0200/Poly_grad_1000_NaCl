def load_andor_asc(filename, data=None):
    if data is not None:
        lines= data.decode('ascii').splitlines()
    else:
        with open(filename, "r") as andor_asc_file:
            lines = andor_asc_file.readlines()
    floatFields = [
        'Temperature (C)',  # -55
        'Exposure Time (secs)',  # 1
        'Accumulate Cycle Time (secs)',  # 1
        'Frequency (Hz)',  # 1
        'Number of Accumulations',  # 10
        'Horizontal binning',  # 1
        'Vertical Shift Speed (usecs)',  # 8.25
        'Pixel Readout Time (usecs)',  # 10
        'Pre-Amplifier Gain',  # 1.000000
        'Wavelength (nm)',  # 600
        'Grating Groove Density (l/mm)'  # 600
    ]

    rezult = {}
    col1, col2 = [], []

    for full_line in lines:
        line = full_line.strip(" \t\n\r")
        # print(line)
        header_fields = line.split(':', 1)
        if len(header_fields) == 2:
            key = header_fields[0]
            val = header_fields[1].strip()
            if key in floatFields:
                #print (val)
                rezult[key] = float(val.replace(",", ".").replace('x', ''))
            else:
                rezult[key] = val

        data_fields = line.split('\t')
        if len(data_fields) == 2:
            col1.append(float(data_fields[0].replace(",", ".")))
            col2.append(float(data_fields[1].replace(",", ".")))
    rezult['col1'] = col1
    rezult['col2'] = col2

    return rezult


# load_andor_asc('Exp_PBS\\P0001x0001.asc')
