import numpy as np
import statsmodels.api as sm
import scipy.stats as stats

class EMUEconomyCycle(object):
    def __init__(self, file_pmi = "economy_data/EMU_Composite_PMI_SPGlobal.txt", file_pmi_manu = "economy_data/EMU_Manu_PMI.txt", file_cpi = "economy_data/EMU_CPI.txt"):
        dat_pmi = np.loadtxt(file_pmi)
        dat_pmi_manu = np.loadtxt(file_pmi_manu)
        dat_cpi = np.loadtxt(file_cpi)
        self.t = dat_pmi[:,0]
        self.pmi = dat_pmi[:,1]
        self.pmi = (self.pmi - 50.0) * 1
        self.cpi = dat_cpi[:,1]
        self.pmi_manu = dat_pmi_manu[:, 1]
        self.pmi_manu_hungary = dat_pmi_manu[:, 3]
        size =  min(self.pmi.shape[0], self.cpi.shape[0])
        self.t = self.__resize(self.t, size)
        self.t = self.t // 100 + (self.t % 100 - 1) / 12
        self.pmi = self.__resize(self.pmi, size)
        self.cpi = self.__resize(self.cpi, size)

    def HP_filter(self, lamb):
        '''
        lamb: lambda, The Hodrick-Prescott smoothing parameter. A value of 1600 is suggested for quarterly data. 
        Ravn and Uhlig suggest using a value of 6.25 (1600/4**4) for annual data and 129600 (1600*3**4) for monthly data.
        In practie, 100 and 14400 are commonly used respectively.
        '''
        x = self.t
        y = self.pmi
        pmi_cycle, pmi_trend = sm.tsa.filters.hpfilter(y, lamb = lamb)
        y = self.cpi
        cpi_cycle, cpi_trend = sm.tsa.filters.hpfilter(y, lamb = lamb)
        return pmi_cycle, pmi_trend, cpi_cycle, cpi_trend

    def __resize(self, array, size):
        array = array[array.shape[0] - size:]
        return array

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

    eec = EMUEconomyCycle("economy_data/EMU_Composite_PMI_SPGlobal.txt",
            "economy_data/EMU_Manu_PMI.txt",
            "economy_data/EMU_CPI.txt")
    pmi_cycle, pmi_trend, cpi_cycle, cpi_trend = eec.HP_filter(lamb = 14400)
    dpmi_trend = pmi_trend[:-1] - pmi_trend[1:]
    dcpi_trend = cpi_trend[:-1] - cpi_trend[1:]

    fig, ax = plt.subplots(nrows = 2, ncols = 2, sharex = True)
    ax[0,0].plot(eec.t, pmi_trend, ls = "-", color = "C0", label = "Composite PMI - Pressure")
    ax[0,0].plot(eec.t, cpi_trend, ls = "-", color = "C1", label = "CPI - Resistance")
    ax[0,0].plot(eec.t, eec.pmi, ls = "--", marker = "", color = "C0")
    ax[0,0].plot(eec.t, eec.cpi, ls = "--", marker = "", color = "C1")
    ax[0,0].xaxis.set_minor_locator(MultipleLocator(0.25))
    ax[0,0].xaxis.set_major_locator(MultipleLocator(1))
    ax[0,0].set_ylabel("Index")
    ax[0,0].legend()

    ax[0,1].plot(eec.t[1:], dpmi_trend, ls = "-", color = "C0")
    ax[0,1].plot(eec.t[1:], dcpi_trend, ls = "-", color = "C1")
    ax[0,1].plot(eec.t[1:], np.zeros_like(eec.t[1:]), ls = "--", color = "k")
    ax[0,1].xaxis.set_minor_locator(MultipleLocator(0.25))
    ax[0,1].xaxis.set_major_locator(MultipleLocator(1))
    ax[0,1].set_ylabel("Index Change")

    ax[1,1].plot(eec.t[1:], np.sign(dpmi_trend), ls = "", marker = "o", color = "C0")
    ax[1,1].plot(eec.t[1:], np.sign(dcpi_trend), ls = "", marker = "o", color = "C1")
    ax[1,1].xaxis.set_minor_locator(MultipleLocator(0.25))
    ax[1,1].xaxis.set_major_locator(MultipleLocator(1))
    ax[1,1].yaxis.set_major_locator(MultipleLocator(1))
    ax[1,1].set_ylabel("Index Change Sign")

    stage = np.zeros_like(dpmi_trend)
    for i in range(len(stage)):
        if dpmi_trend[i] >= 0 and dcpi_trend[i] < 0: stage[i] = 0 # recovery
        elif dpmi_trend[i] >= 0 and dcpi_trend[i] >= 0: stage[i] = 1 # expansion
        elif dpmi_trend[i] < 0 and dcpi_trend[i] >= 0: stage[i] = 2 # stagflation
        else: stage[i] = 3 # recession
    ax[1,0].plot(eec.t[1:], stage, ls = "-", marker = "o", color = "C2")
    ax[1,0].xaxis.set_minor_locator(MultipleLocator(0.25))
    ax[1,0].xaxis.set_major_locator(MultipleLocator(1))
    ax[1,0].yaxis.set_major_locator(MultipleLocator(1))
    ax[1,0].set_ylabel("Stage")
    plt.show()


    fig, ax = plt.subplots(nrows = 2, ncols = 1)
    ax[0].plot(eec.t, eec.pmi_manu, color = "C0", label = "EMU")
    ax[0].plot(eec.t, eec.pmi_manu_hungary, color = "C1", label = "Hungary")
    ax[0].set_ylabel("Manufacturing PMI")
    ax[0].legend()

    ax[1].scatter(eec.pmi_manu, eec.pmi_manu_hungary)
    ax[1].set_xlabel("Manufacturing PMI EMU")
    ax[1].set_ylabel("Manufacturing PMI Hungary")

    plt.show()
