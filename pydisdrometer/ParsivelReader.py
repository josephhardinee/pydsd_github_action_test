# -*- coding: utf-8 -*-
import numpy as np
import numpy.ma as ma
import pytmatrix
import DSDProcessor
from pytmatrix.tmatrix import Scatterer
from pytmatrix.psd import PSDIntegrator
from pytmatrix import orientation, radar, tmatrix_aux, refractive
import csv
import expfit
from DropSizeDistribution import DropSizeDistribution


def read_parsivel(filename):
    '''
    Takes a filename pointing to a parsivel raw file and returns
    a drop size distribution object.
    '''

    reader = ParsivelReader(filename)
    dsd = DropSizeDistribution(reader.time, reader.Nd, reader.spread,
                               reader.rain_rate)
    dsd.raw_matrix = reader.raw
    dsd.Z = reader.Z
    return dsd


class ParsivelReader(object):

    '''
    ParsivelReader class takes takes a filename as it's only argument(for now).
    This should be a parsivel raw datafile(output from the parsivel).

    '''

    rain_rate = []
    Z = []
    num_particles = []

    Nd = []
    vd = []
    raw = []
    code = []
    time = []

    ndt = []

    def __init__(self, filename):
        self.filename = filename

        pcm_matrix_file = open('./parsivel_conditional_matrix.txt')
        self.pcm_matrix = np.reshape(
            map(int, pcm_matrix_file.read().rstrip('\n').split(',')), (32, 32))

        self._read_file()
        self._prep_data()

        self.bins = np.hstack((0, self.diameter + np.array(self.spread) / 2))

    def _read_file(self):
        with open(self.filename) as f:
            for line in f:
                code = line.split(':')[0]
                if(code == '01'):
                    self.rain_rate.append(
                        float(line.rstrip('\n\r').split(':')[1]))
                elif(code == '07'):
                    self.Z.append(float(line.rstrip('\n\r').split(':')[1]))
                elif(code == '11'):
                    self.num_particles.append(
                        int(line.rstrip('\n\r').split(':')[1]))
                elif(code == '20'):
                    self.time.append(
                        self.get_sec(line.rstrip('\n\r').split(':')[1:4]))
                elif(code == '90'):
                    self.Nd.append(
                        map(float, line.rstrip('\n\r;').split(':')[1].split(';')))
                elif(code == '91'):
                    self.vd.append(
                        map(float, line.rstrip('\n').split(':')[1].rstrip(';\r').split(';')))
                elif(code == '93'):
                    self.raw.append(
                        map(int, line.split(':')[1].strip('\r\n;').split(';')))
                    #self.ndt.append(np.sum((np.reshape(map(int,
                    #    line.split(':')[1].strip(';\n').split(';')), (32, 32))), axis=0))

    def _apply_pcm_matrix(self):
        pass

    def _prep_data(self):
        self.rain_rate = np.array(self.rain_rate)
        self.Z = ma.masked_equal(self.Z, -9.999)
        self.Nd[self.Nd == -9.999] = 0
        self.num_particles = np.array(self.num_particles)
        self.time = np.array(self.time)
        self.velocity = np.ndarray(self.vd)
        self.raw = np.ndarray(self.raw)

    def get_sec(self, s):
        return int(s[0]) * 3600 + int(s[1]) * 60 + int(s[2])

    def _setup_scattering(self):
        self.scatterer = Scatterer(wavelength=tmatrix_aux.wl_X,
                                   m=refractive.m_w_10C[tmatrix_aux.wl_X])
        self.scatterer.psd_integrator = PSDIntegrator()
        self.scatterer.psd_integrator.axis_ratio_func = lambda D: 1.0 / \
            self.bc(D)
        self.scatterer.psd_integrator.D_max = 10.0
        self.scatterer.psd_integrator.geometries = (
            tmatrix_aux.geom_horiz_back, tmatrix_aux.geom_horiz_forw)
        self.scatterer.or_pdf = orientation.gaussian_pdf(20.0)
        self.scatterer.orient = orientation.orient_averaged_fixed
        self.scatterer.psd_integrator.init_scatter_table(self.scatterer)

    def radar_from_dsd(self, Nd):
        for t in range(0, nt - 6):
            BinnedDSD = pytmatrix.psd.BinnedPSD(
                self.bins,  np.sum(Nd[t:t + 1], axis=0))
            self.scatterer.psd = BinnedDSD
            self.scatterer.set_geometry(tmatrix_aux.geom_horiz_back)
            Zdr[t] = 10 * np.log10(radar.Zdr(self.scatterer))
            Zh[t] = 10 * np.log10(radar.refl(self.scatterer))
            self.scatterer.set_geometry(tmatrix_aux.geom_horiz_forw)
            Kdp[t] = radar.Kdp(self.scatterer)
            Ai[t] = radar.Ai(self.scatterer)


    diameter = [
        0.06, 0.19, 0.32, 0.45, 0.58, 0.71, 0.84, 0.96, 1.09, 1.22, 1.42, 1.67,
        1.93, 2.19, 2.45, 2.83, 3.35, 3.86, 4.38, 4.89, 5.66,
        6.7, 7.72, 8.76, 9.78, 11.33, 13.39, 15.45, 17.51, 19.57, 22.15, 25.24]

    spread = [
        0.129, 0.129, 0.129, 0.129, 0.129, 0.129, 0.129, 0.129, 0.129, 0.129, 0.257,
        0.257, 0.257, 0.257, 0.257, 0.515, 0.515, 0.515, 0.515, 0.515, 1.030, 1.030,
        1.030, 1.030, 1.030, 2.060, 2.060, 2.060, 2.060, 2.060, 3.090, 3.090]

    v = [
        0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.1, 1.3, 1.5, 1.7, 1.9,
        2.2, 2.6, 3, 3.4, 3.8, 4.4, 5.2, 6.0, 6.8, 7.6, 8.8, 10.4, 12.0, 13.6, 15.2,
        17.6, 20.8
    ]

    v_spread = [.1, .1, .1, .1, .1, .1, .1, .1, .1, .1, .2, .2, .2, .2, .2, .4,
                .4, .4, .4, .4, .8, .8, .8, .8, .8, 1.6, 1.6, 1.6, 1.6, 1.6, 3.2, 3.2]

    def bc(D_eq):
        return 1.0048 + 5.7 * 10 ** (-4) - 2.628 * 10 ** (-2) * D_eq * D_eq ** 2 +\
            3.682 * 10 ** (-3) * D_eq ** 3 - 1.677 * 10 ** -4 * D_eq ** 4

#Nd = np.power(10, np.array(Nd))
#ndt = np.array(ndt)

#Nd[Nd < 0] = 0
#ndt[ndt < 0] = 0
#k = 92


# At this point we have Nd, need to do the scattering calculations


#nt = Nd.shape[0]

#Kdp = np.zeros(nt)
#Zh = np.zeros(nt)
#Zdr = np.zeros(nt)
#Ai = np.zeros(nt)

#rain_rate = np.array(rain_intensity)

#if __name__ == '__main__':
#    filename = '/net/makalu/radar/tmp/jhardin/parsiveldata/20110910.mis'
#    par_reader = ParsivelReader(filename)
