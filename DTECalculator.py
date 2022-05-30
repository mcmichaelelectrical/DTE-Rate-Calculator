# DTE Calculator
# This reads in an energy usage csv report from DTE and compares different rate plans

from datetime import datetime
import csv
import tkinter as tk
from tkinter import filedialog
# ------------------------------------------------------------------------------------------
# Calculates the hourly price based on regular pricing, returns $
def calcReg(dateRef, energyRef):
    return energyRef * 0.1918 # 0.1918cents per kWh
# ------------------------------------------------------------------------------------------
# Calculates the hourly price based on Time-Of-Day pricing, returns $
def calcTimeOfDay(dateRef, energyRef):

    # Weekday (1-5)
    if dateRef.isoweekday() <= 5:

        # On-peak (11am through 7pm. 18=6pm hour)
        if dateRef.hour in range(11, 18):

            # Jume through October is 0.23/kWh
            if dateRef.month in range(6, 10):
                multiplier = 0.23
            else:
                multiplier = 0.20

        # Off-peak
        else:
            multiplier = 0.12

    else:
        # Weekend (6 and 7)
        multiplier = 0.12 # 12 cents per kWh

    return energyRef * multiplier
# ------------------------------------------------------------------------------------------
# Calculates the hourly price based on Dynamic Peak pricing, returns $
# ASSUMES 0 CRITICAL EVENTS
def calcDynamicPeak(dateRef, energyRef):

    # Weekday (1-5)
    if dateRef.isoweekday() <= 5:

        # Mid-Peak (7am-3pm. 14=2pm hour)
        if dateRef.hour in range(7, 14):
            multiplier = 0.158 # 15.8 cents/kWh (9.2c + 6.6c distribution charge)

        # On-Peak (3pm-7pm. 18=6pm hour)
        elif dateRef.hour in range(15, 18):
            multiplier = 0.232 # 23.2 cents/kWh (16.6c + 6.6c distribution charge)

        # Off-peak
        else:
            multiplier = 0.12

    else:
        # Weekend (6 and 7)
        multiplier = 0.114 # 11.4 cents/kWh (4.8c + 6.6c distribution charge)

    return energyRef * multiplier
# ------------------------------------------------------------------------------------------
def runAnalysis(filepath):

    reportPath = ('File: ' + filepath)
    print(reportPath)
    if createReport:
        f.write(reportPath)

    # Read CSV and create a 2D list
    data = list(csv.reader(open(filepath)))

    # Create list with only the important data
    del data[0]  # delete headers

    # If DTE has no data in some hours, this try/catch will handle it until it works (or fails after 5 tries)
    retry = 0
    while True:
        try:
            data = [[row[2] + " " + row[3], float(row[4])] for row in data]  # ['MM/DD/YYYY 12:00PM', 0.427]
            break
        except:
            print('Fucking DTE had a no data period.')
            retry = retry + 1
            if retry >= 5:
                print('We could not fix the issue after 5 tries. We give up.')
                break
            dataFix = []
            for row in data:
                if row[4] != 'No Data':
                    dataFix.append(row)
            data = dataFix

    totalReg = 0  # total $ from regular
    totalTOD = 0  # total $ from time-of-day
    totalDynamic = 0  # total $ from dynamic
    for row in data:
        testDate = datetime.strptime(row[0], "%m/%d/%Y %I:%M %p")  # converts string to datetime for Month/Day/Year Hour:Min AM/PM

        reg = calcReg(testDate, row[1])
        totalReg = totalReg + reg

        toD = calcTimeOfDay(testDate, row[1])
        totalTOD = totalTOD + toD

        dynamic = calcDynamicPeak(testDate, row[1])
        totalDynamic = totalDynamic + dynamic

        if verbose:
            print('%s -- %0.3f kWh' % (testDate, row[1]))
            print('\tRegular: %0.2f TOD: %0.2f Dynamic: %0.2f\n' % (reg, toD, dynamic))

    reportText = ('\nRegular: %5.2f\nTime-Of-Day: %5.2f\nDynamic: %5.2f' % (totalReg, totalTOD, totalDynamic))
    reportDelimiter = ('\n------------------------------------------\n')
    if createReport:
        f.write(reportText + reportDelimiter)
    print(reportText, reportDelimiter)
    return
# ------------------------------------------------------------------------------------------
verbose = False
createReport= True

root = tk.Tk()
root.withdraw() # removes blank Tk window

# File selection in tkDialog
files = filedialog.askopenfilenames(title = "Select file(s)",filetypes = (("CSV Files","*.csv"),))

if createReport:
    f = open('DTEreport.txt', 'w+')

# Run the cost analysis on all the files
[runAnalysis(file) for file in files]

if createReport:
    f.close()
