import numpy as np
import statsmodels.api as sm
import scipy.stats as stats

class EMUEconomyCycle(object):
	def __init__(self, file_pmi, file_cpi):
		dat_pmi = np.loadtxt(file_pmi)
		dat_cpi = np.loadtxt(file_cpi)
		self.t = dat_pmi[:,0]
		self.t = self.t // 100 + (self.t % 100 - 1) / 12
		self.pmi_2nd  = dat_pmi[:,1]
#		self.pmi_else = dat_pmi[:,3]
		second_total_ratio = 1.0
		self.pmi = second_total_ratio * self.pmi_2nd# + (1 - second_total_ratio) * self.pmi_else
		self.pmi = (self.pmi - 50.0)
		self.cpi = dat_cpi[:,1] 

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

if __name__ == "__main__":
	import matplotlib.pyplot as plt
	from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

	eec = EMUEconomyCycle("economy_data/EMU_Manu_PMI.txt",
			"economy_data/EMU_CPI.txt")
	pmi_cycle, pmi_trend, cpi_cycle, cpi_trend = eec.HP_filter(lamb = 100)
	dpmi_trend = pmi_trend[:-1] - pmi_trend[1:]
	dcpi_trend = cpi_trend[:-1] - cpi_trend[1:]

	fig, ax = plt.subplots(nrows = 2, ncols = 2, sharex = True)
	ax[0,0].plot(eec.t, pmi_trend, ls = "-", color = "C0", label = "Manufacture PMI - Pressure")
	ax[0,0].plot(eec.t, cpi_trend, ls = "-", color = "C1", label = "CPI - Resistance")
	ax[0,0].plot(eec.t, eec.pmi, ls = "--", marker = "", color = "C0")
	ax[0,0].plot(eec.t, eec.cpi, ls = "--", marker = "", color = "C1")
	ax[0,0].xaxis.set_minor_locator(MultipleLocator(0.25))
	ax[0,0].xaxis.set_major_locator(MultipleLocator(1))
	ax[0,0].legend()

	ax[0,1].plot(eec.t[1:], dpmi_trend, ls = "-", color = "C0")
	ax[0,1].plot(eec.t[1:], dcpi_trend, ls = "-", color = "C1")
	ax[0,1].xaxis.set_minor_locator(MultipleLocator(0.25))
	ax[0,1].xaxis.set_major_locator(MultipleLocator(1))

	ax[1,1].plot(eec.t[1:], np.sign(dpmi_trend), ls = "", marker = "o", color = "C0")
	ax[1,1].plot(eec.t[1:], np.sign(dcpi_trend), ls = "", marker = "o", color = "C1")
	ax[1,1].xaxis.set_minor_locator(MultipleLocator(0.25))
	ax[1,1].xaxis.set_major_locator(MultipleLocator(1))


	stage = np.zeros_like(dpmi_trend)
	for i in range(len(stage)):
		if dpmi_trend[i] >= 0 and dcpi_trend[i] < 0: stage[i] = 0 # recovery
		elif dpmi_trend[i] >= 0 and dcpi_trend[i] >= 0: stage[i] = 1 # expansion
		elif dpmi_trend[i] < 0 and dcpi_trend[i] >= 0: stage[i] = 2 # stagflation
		else: stage[i] = 3 # recession
	ax[1,0].plot(eec.t[1:], stage, ls = "-", marker = "o", color = "C2")
	ax[1,0].xaxis.set_minor_locator(MultipleLocator(0.25))
	ax[1,0].xaxis.set_major_locator(MultipleLocator(1))
	plt.show()
