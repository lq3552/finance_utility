import numpy as np
import statsmodels.api as sm
import scipy.stats as stats

class ChinaEconomyCycle(object):
    def __init__(self, file_pmi = "economy_data/China_Composite_PMI.txt", file_ppi = "economy_data/China_PPI.txt", file_cpi = "economy_data/China_CPI.txt", file_pmi_sec = "economy_data/China_Sector_PMI.txt"):
        '''
        parameters: path(s) to economic data files
            file_pmi, file_ppi, file_cpi, file_pmi_sec
        '''
        dat_pmi = np.loadtxt(file_pmi)
        dat_ppi = np.loadtxt(file_ppi)
        dat_cpi = np.loadtxt(file_cpi)
        dat_pmi_sec = np.loadtxt(file_pmi_sec)
        self.t = dat_pmi[: ,0]
        self.pmi_2nd  = dat_pmi_sec[:,1]
        self.pmi_else = dat_pmi_sec[:,3]
        self.pmi = dat_pmi[:,1]
        self.pmi = (self.pmi - 50.0) * 2
        self.ppi = dat_ppi[:,2]
        self.cpi = dat_cpi[:,2]
        size = min(self.pmi.shape[0], self.ppi.shape[0], self.cpi.shape[0])
        self.t = self.__resize(self.t, size)
        self.t = self.t // 100 + (self.t % 100 - 1) / 12
        self.pmi = self.__resize(self.pmi, size)
        self.ppi = self.__resize(self.ppi, size)
        self.cpi = self.__resize(self.cpi, size)
        self.pmi_2nd = self.__resize(self.pmi_2nd, size)
        self.pmi_else = self.__resize(self.pmi_else, size)

    def HP_filter(self, lamb):
        '''
        lamb: lambda, The Hodrick-Prescott smoothing parameter. A value of 1600 is suggested for quarterly data. 
        Ravn and Uhlig suggest using a value of 6.25 (1600/4**4) for annual data and 129600 (1600*3**4) for monthly data.
        In practie, 100 and 14400 are commonly used respectively.
        '''
        y = self.pmi
        pmi_cycle, pmi_trend = sm.tsa.filters.hpfilter(y, lamb = lamb)
        y = self.ppi
        ppi_cycle, ppi_trend = sm.tsa.filters.hpfilter(y, lamb = lamb)
        y = self.cpi
        cpi_cycle, cpi_trend = sm.tsa.filters.hpfilter(y, lamb = lamb)
        return pmi_cycle, pmi_trend, ppi_cycle, ppi_trend, cpi_cycle, cpi_trend

    def correlate_pmi_2nd_and_else(self):
        print("(Kendall tau, p-value) = ", stats.kendalltau(self.pmi_2nd, self.pmi_else))

    def __resize(self, array, size):
        array = array[array.shape[0] - size:]
        return array

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

    cec = ChinaEconomyCycle()
    cec.correlate_pmi_2nd_and_else()
    pmi_cycle, pmi_trend, ppi_cycle, ppi_trend, cpi_cycle, cpi_trend = cec.HP_filter(lamb = 1600)
    dpmi_trend = pmi_trend[:-1] - pmi_trend[1:]
    dppi_trend = ppi_trend[:-1] - ppi_trend[1:]
    dcpi_trend = cpi_trend[:-1] - cpi_trend[1:]

    fig, ax = plt.subplots(nrows = 3, ncols = 2, sharex = True)

    for i in range(ax.shape[0]):
        for j in range(ax.shape[1]):
            ax[i, j].xaxis.set_minor_locator(MultipleLocator(0.25))
            ax[i, j].xaxis.set_major_locator(MultipleLocator(1))
    
    ax[0,0].plot(cec.t, pmi_trend, ls = "-", color = "C0", label = "Composite PMI - Pressure")
    ax[0,0].plot(cec.t, ppi_trend, ls = "-", color = "C1", label = "PPI - Resistance")
    ax[0,0].plot(cec.t, cec.pmi, ls = "--", marker = "", color = "C0")
    ax[0,0].plot(cec.t, cec.ppi, ls = "--", marker = "", color = "C1")
    ax[0,0].set_ylabel("Index")
    ax[0,0].legend()

    ax[0,1].plot(cec.t[1:], dpmi_trend, ls = "-", color = "C0")
    ax[0,1].plot(cec.t[1:], dppi_trend, ls = "-", color = "C1")
    ax[0,1].set_ylabel("Index Change")

    ax[1,1].plot(cec.t[1:], np.sign(dpmi_trend), ls = "", marker = "o", color = "C0")
    ax[1,1].plot(cec.t[1:], np.sign(dppi_trend), ls = "", marker = "o", color = "C1")
    ax[1,1].yaxis.set_major_locator(MultipleLocator(1))
    ax[1,1].set_ylabel("Index Change Sign")

    ax[2,0].plot(cec.t, ppi_trend, ls = "-", color = "C0", label = "PPI")
    ax[2,0].plot(cec.t, cpi_trend, ls = "-", color = "C1", label = "CPI")
    ax[2,0].plot(cec.t, cec.ppi, ls = "--", marker = "", color = "C0")
    ax[2,0].plot(cec.t, cec.cpi, ls = "--", marker = "", color = "C1")
    ax[2,0].set_ylabel("Index")
    ax[2,0].legend()

    ax[2,1].plot(cec.t[1:], dppi_trend, ls = "-", color = "C0")
    ax[2,1].plot(cec.t[1:], dcpi_trend, ls = "-", color = "C1")
    ax[2,1].set_ylabel("Index Change")


    stage = np.zeros_like(dpmi_trend)
    for i in range(len(stage)):
        if dpmi_trend[i] >= 0 and dppi_trend[i] < 0: stage[i] = 0 # recovery
        elif dpmi_trend[i] >= 0 and dppi_trend[i] >= 0: stage[i] = 1 # expansion
        elif dpmi_trend[i] < 0 and dppi_trend[i] >= 0: stage[i] = 2 # stagflation
        else: stage[i] = 3 # recession
    ax[1,0].plot(cec.t[1:], stage, ls = "-", marker = "o", color = "C2")
    ax[1,0].yaxis.set_major_locator(MultipleLocator(1))
    ax[1,0].set_ylabel("Stage")
    plt.show()
