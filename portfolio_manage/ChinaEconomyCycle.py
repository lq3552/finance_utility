import numpy as np
import statsmodels.api as sm
import scipy.stats as stats

class ChinaEconomyCycle(object):
	def __init__(self, file_pmi, file_ppi):
		dat_pmi = np.loadtxt(file_pmi)
		dat_ppi = np.loadtxt(file_ppi)
		self.t = dat_pmi[:,0]
		self.t = self.t // 100 + (self.t % 100 - 1) / 12
		self.pmi_2nd  = dat_pmi[:,1]
		self.pmi_else = dat_pmi[:,3]
		second_total_ratio = 1.0
		self.pmi = second_total_ratio * self.pmi_2nd + (1 - second_total_ratio) * self.pmi_else
		self.pmi = (self.pmi - 50.0) * 2
		self.ppi = dat_ppi[:,2]

	def HP_filter(self, lamb):
		'''
		lamb: lambda, The Hodrick-Prescott smoothing parameter. A value of 1600 is suggested for quarterly data. 
		Ravn and Uhlig suggest using a value of 6.25 (1600/4**4) for annual data and 129600 (1600*3**4) for monthly data.
		In practie, 100 and 14400 are commonly used respectively.
		'''
		x = self.t
		y = self.pmi
		pmi_cycle, pmi_trend = sm.tsa.filters.hpfilter(y, lamb = lamb)
		y = self.ppi
		ppi_cycle, ppi_trend = sm.tsa.filters.hpfilter(y, lamb = lamb)
		return pmi_cycle, pmi_trend, ppi_cycle, ppi_trend

	def correlate_pmi_2nd_and_else(self):
		print("(Person r, p-value) = ", stats.pearsonr(self.pmi_2nd, self.pmi_else))

if __name__ == "__main__":
	import matplotlib.pyplot as plt
	from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

	cec = ChinaEconomyCycle("economy_data/China_PMI.txt",
			"economy_data/China_PPI.txt")
	cec.correlate_pmi_2nd_and_else()
	pmi_cycle, pmi_trend, ppi_cycle, ppi_trend = cec.HP_filter(lamb = 100)
	dpmi_trend = pmi_trend[:-1] - pmi_trend[1:]
	dppi_trend = ppi_trend[:-1] - ppi_trend[1:]

	fig, ax = plt.subplots(nrows = 2, ncols = 2, sharex = True)
	ax[0,0].plot(cec.t, pmi_trend, ls = "-", color = "C0", label = "Manufacture PMI - Pressure")
	ax[0,0].plot(cec.t, ppi_trend, ls = "-", color = "C1", label = "PPI - Resistance")
	ax[0,0].plot(cec.t, cec.pmi, ls = "--", marker = "", color = "C0")
	ax[0,0].plot(cec.t, cec.ppi, ls = "--", marker = "", color = "C1")
	ax[0,0].xaxis.set_minor_locator(MultipleLocator(0.25))
	ax[0,0].xaxis.set_major_locator(MultipleLocator(1))
	ax[0,0].legend()

	ax[0,1].plot(cec.t[1:], dpmi_trend, ls = "-", color = "C0")
	ax[0,1].plot(cec.t[1:], dppi_trend, ls = "-", color = "C1")
	ax[0,1].xaxis.set_minor_locator(MultipleLocator(0.25))
	ax[0,1].xaxis.set_major_locator(MultipleLocator(1))

	ax[1,1].plot(cec.t[1:], np.sign(dpmi_trend), ls = "", marker = "o", color = "C0")
	ax[1,1].plot(cec.t[1:], np.sign(dppi_trend), ls = "", marker = "o", color = "C1")
	ax[1,1].xaxis.set_minor_locator(MultipleLocator(0.25))
	ax[1,1].xaxis.set_major_locator(MultipleLocator(1))


	stage = np.zeros_like(dpmi_trend)
	for i in range(len(stage)):
		if dpmi_trend[i] >= 0 and dppi_trend[i] < 0: stage[i] = 0 # recovery
		elif dpmi_trend[i] >= 0 and dppi_trend[i] >= 0: stage[i] = 1 # expansion
		elif dpmi_trend[i] < 0 and dppi_trend[i] >= 0: stage[i] = 2 # stagflation
		else: stage[i] = 3 # recession
	ax[1,0].plot(cec.t[1:], stage, ls = "-", marker = "o", color = "C2")
	ax[1,0].xaxis.set_minor_locator(MultipleLocator(0.25))
	ax[1,0].xaxis.set_major_locator(MultipleLocator(1))
	plt.show()
