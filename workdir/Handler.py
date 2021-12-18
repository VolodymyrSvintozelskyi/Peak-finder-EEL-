import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from scipy.optimize import curve_fit
import random
import eel
import copy

eel.init('www')

class Filter:
    def get_moving_average(x, w):
        # return np.convolve(x, np.ones(w), 'valid') / w
        res = np.copy(x)
        for i in range(1,w+1):
            res += np.pad(x,(0,i),mode="edge")[i:] + np.pad(x,(i,0),mode="edge")[0:-i]
        w_arr = np.arange(0,w,1)
        res = res / (2*w+1)
        slope = (res[w+5]-res[w])/5
        return np.hstack([(res[w] - slope*w) + slope*w_arr  , res[w:-w], x[-w:]]) 

    def secondDerivative(array):
        # wrapped = np.pad(array, (1,1), 'constant', constant_values=(0,0))
        return np.pad(array[0:-2] + array[2:] - 2* array[1:-1], (1,1), mode="constant")

def clarifyBrutePeak(data, start):
    up = data.shape[0]-1
    for i in range(start, len(data)):
        if data[i] >= 0:
            up = i
            break
    down = 0
    for i in range(start, 0, -1):
        if data[i] >= 0:
            down = i
            break
    if up == down: return {"down": down, "up":up, "mean": start,"sigma":0}
    mean = down + np.argmin(data[down:up])
    sigma = up - down - 1
    return {
        "down": down+0.5, 
        "up": up - 0.5, 
        "mean": mean, 
        "sigma": sigma
    }

def foundBrutePeaks(spectra_der, p, a1, a2, a3):
    wrapped = np.pad(spectra_der, (p,p), "edge")
    check_1 = wrapped[:-2*p] > a1
    check_2 = wrapped[p:-p] < -a2
    check_3 = wrapped[2*p:] > a3
    peak_going = False
    peaks = []
    for i,value in enumerate(np.logical_and(check_1, np.logical_and(check_2, check_3))):
        if value and not peak_going:
            peak_going = True
            peak_start = i
        if not value and peak_going:
            peak_going = False
            peak_end = i
            peaks.append([peak_start, peak_end])
    peaks = np.array(peaks)
    # print(peaks.shape)
    if peaks.shape[0] == 0: return []
    peaks = np.mean(peaks, axis=1)
    peaks = [clarifyBrutePeak(spectra_der, int(peak)) for peak in peaks]
    return peaks

def fitZone(begin, end, data,max_peaks, fit_thr, ma_width, ma_iter):
    error_msg = ""
    spectra = data [ begin: end]
    width = end-begin
    center = (begin+end)/2
    p0 = np.array([(spectra[-1]-spectra[0]) / width, (spectra[-1]+spectra[0])/2])
    def gauss(x, pars):
        [A, mu, sigma] = pars
        return A* np.exp(-((x-mu)/2/sigma)**2)
    func = lambda x,*pars: sum([gauss(x,pars[2+i*3:2+i*3+3]) for i in range(int((len(pars)-2)/3))]) + pars[0]*(x-center)+pars[1]
    perr = np.inf
    for num_peaks in range(1,1+max_peaks):
        deviation = spectra - func(np.arange(begin,end),*p0)
        newmu = max(min(deviation.shape[0]-3, np.argmax(deviation) - 1),0)
        dev_derivative = Filter.secondDerivative(deviation)
        for i in range(ma_iter):
            dev_derivative = Filter.get_moving_average(dev_derivative, ma_width)
        peak = clarifyBrutePeak(dev_derivative, newmu)
        newA = deviation[int(peak["mean"])]
        newmu = peak["mean"]
        newsigma = peak["sigma"]
        if (num_peaks > 1 and (newA < fit_thr*np.std(deviation))):
            break
        # if (num_peaks == 3): break
        newmu += begin
        if newsigma != 0:
            p0 = np.hstack([p0, newA, newmu, newsigma])
        try:
            fit, pcov = curve_fit(func, np.arange(begin,end), spectra, p0=p0) 
            perr = np.sqrt(np.diag(pcov))
            p0 = fit
        except RuntimeError:
            error_msg = "Fit error"
            perr = np.zeros_like(p0)
            print("Runtime error")
        if newsigma == 0: break
    if max_peaks == 0:
        fit, pcov = curve_fit(func, np.arange(begin,end), spectra, p0=p0) 
        perr = np.sqrt(np.diag(pcov))
        p0 = fit
    deviation = spectra - func(np.arange(begin,end),*p0)
    return (p0, perr, func, spectra, deviation, error_msg)

def fitSpectra(plot, conf, peaks, spectra):
    group_sep_q = conf["autofit_sep"]
    group_size = conf["autofit_active"]
    group_start = peaks[0]["mean"] - group_size*peaks[0]["sigma"]
    groups = []
    error_msg_global = ""
    for i,peak in enumerate(peaks[:-1]):
        if abs(peak["mean"] - peaks[i+1]["mean"]) > abs(group_sep_q*(peak["sigma"] + peaks[i+1]["sigma"])):
            groupd_end = peak["mean"] + group_size *peak["sigma"]
            groups.append((max(0,group_start), min(groupd_end, spectra.shape[0]-1)))
            group_start = peaks[i+1]["mean"] - group_size*peaks[i+1]["sigma"]
    groupd_end = peaks[-1]["mean"] + 4 *peaks[-1]["sigma"]
    groups.append((max(0,group_start), min(groupd_end, spectra.shape[0]-1)))
    for group in groups:
        (p0, perr, func, fitted_zone, deviation, error_msg) = fitZone(group[0],group[1],spectra, conf["autofit_max_peaks"], conf["autofit_ampl_thr"], conf["ma_width"], conf["ma_iter"])
        if error_msg:
            error_msg_global = error_msg
        plot.add_scatter(func(np.arange(group[0],group[1]),*p0), group[0])
        for i in range(int((p0.shape[0]-2)/3)):
            print("\tPeak: A={}+-{}\t\tmu={}+-{}\t\tsigma={}+-{}".format(p0[2+3*i], perr[2+3*i],p0[2+3*i+1], perr[2+3*i+1],p0[2+3*i+2], perr[2+3*i+2]))
    return error_msg       

class Plot:
    def __init__(self, spectra, xtitle, ytitle):
        self.data = [
            {
                'x':(np.arange(spectra.shape[0])).tolist(),
                'y':(spectra[:]).tolist(),
                'mode':"markers"
            }
        ]
        self.layout = {
            "xaxis": {
                "title": xtitle
            },
            "yaxis": {
                "title": ytitle
            },
            "shapes": []
        }
    def add_scatter(self, spectra, from_ch=0):
        self.data.append(
            {
                'x':(from_ch+np.arange(spectra.shape[0])).tolist(),
                'y':(spectra[:]).tolist(),
                'mode':"markers"
            }
        )
    def add_vline(self, x0, y0, x1, y1, color="red", width=1.5, dash="dot"):
        self.layout["shapes"].append({
                "type": 'line',
                "x0": float(x0),
                "y0": float(y0),
                "x1": float(x1),
                "yref": 'paper',
                "y1": float(y1),
                "line": {
                    "color": color,
                    "width": width,
                    "dash": dash
                }
            }
        )

def plot_data(keys, plots, maxcols, error_msg=""):
    data = []
    for i,spectra in enumerate(plots):
        data.append({
            "key": keys[i],
            "data": plots[i].data,
            "layout": plots[i].layout
        })
    # print(data)
    eel.update_data(data, maxcols, error_msg)

@eel.expose
def update(conf, content):
    # print(conf)
    parsed = [[ float(el) for el in line.split("\t") if el] for line in content.split("\n") if line and line[0]!="#"]
    nparr = np.array(parsed)
    max_column = nparr.shape[1] - 1
    spectra = nparr[:,conf["file_column"]]
    filtered_spectra = spectra
    objs = {}
    objs[0] = Plot(spectra,"channels","Raw data")#[spectra]
    brute_peaks = []
    error_msg_global = ""
    if conf["ma_apply"]:
        for i in range(conf["ma_iter"]):
            filtered_spectra = Filter.get_moving_average(filtered_spectra, conf["ma_width"])
        objs[1] = Plot(filtered_spectra,"channels","Filtered data")
    if conf["second_der_apply"]:
        sec_deriv = Filter.secondDerivative( filtered_spectra)
        objs[2] = Plot(sec_deriv,"channels","Second derivative")#[sec_deriv]
        for peak in foundBrutePeaks(sec_deriv, conf["second_p"], conf["second_a1"], conf["second_a2"], conf["second_a3"]):
            brute_peaks.append(peak)
            objs[2].add_vline(peak["mean"], 0, peak["mean"], 1)
    if conf["autofit_apply"]:
        error_msg = fitSpectra(objs[0], conf, brute_peaks, spectra)
        if error_msg:
            error_msg_global = error_msg

    if conf["manfit_apply"]:
        man_range = conf["manfit_selected_range"]
        print(man_range)
        if man_range:
            if man_range["x"]:
                xstart = min(spectra.shape[0]-1, max(0, int(man_range["x"][0])))
                xend = int(man_range["x"][1])
                (p0, perr, func, fitted_zone, deviation,error_msg) = fitZone(xstart, xend, spectra,conf["manfit_num_peaks"], conf["manfit_ampl_thr"], conf["ma_width"], conf["ma_iter"])
                if error_msg:
                    error_msg_global = error_msg
                objs[0].add_scatter(func(np.arange(xstart,xend),*p0), xstart)
                for i in range(int((p0.shape[0]-2)/3)):
                    print("\tPeak: A={}+-{}\t\tmu={}+-{}\t\tsigma={}+-{}".format(p0[2+3*i], perr[2+3*i],p0[2+3*i+1], perr[2+3*i+1],p0[2+3*i+2], perr[2+3*i+2]))
    print("Error msg: ", error_msg_global)
    plot_data(list(objs.keys()), list(objs.values()), max_column, error_msg_global)

# @eel.expose
# def update_selected_zone(conf, content):
#     parsed = [[ float(el) for el in line.split("\t") if el] for line in content.split("\n") if line and line[0]!="#"]
#     nparr = np.array(parsed)
#     spectra = nparr[:,conf["file_column"]]
#     if conf["manfit_apply"]:
#         man_range = conf["manfit_selected_range"]
#         print(man_range)
#         if man_range:
#             if man_range["x"]:
#                 xstart = min(spectra.shape[0]-1, max(0, int(man_range["x"][0])))
#                 xend = int(man_range["x"][1])
#                 (p0, perr, func, fitted_zone, deviation,error_msg) = fitZone(xstart, xend, spectra,conf["manfit_num_peaks"], conf["manfit_ampl_thr"], conf["ma_width"], conf["ma_iter"])
#                 if error_msg:
#                     error_msg_global = error_msg
#                 res = {
#                     'x':(np.arange(xstart, xend)).tolist(),
#                     'y':(func(np.arange(xstart,xend),*p0)).tolist(),
#                     'mode':"markers"
#                 }
#                 for i in range(int((p0.shape[0]-2)/3)):
#                     print("\tPeak: A={}+-{}\t\tmu={}+-{}\t\tsigma={}+-{}".format(p0[2+3*i], perr[2+3*i],p0[2+3*i+1], perr[2+3*i+1],p0[2+3*i+2], perr[2+3*i+2]))
#     eel.update_selected_fit(res)
eel.start('index.html')
