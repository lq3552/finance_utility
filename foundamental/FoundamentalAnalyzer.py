import scipy.stats as stats 
import numpy as np

class FoundamentalAnalyzer(object):
	def __init__(self, data_file = None):
		if data_file == None:
			print("WARNING: no data are provided")
			return
		self.file = data_file
		self.data = np.loadtxt(data_file)
		self.data.sort(axis = 0)
		self.date = self.data[:,0]
		self.price = self.data[:,1]
		self.eps = self.data[:,2]
		self.pe = self.eps / self.price

	def correlate_price_earning(self):
		tau,p_value =  stats.kendalltau(self.eps, self.price)
		return (tau, p_value)


	def compute_moving_average(self, window = 4):
		moving_averages = np.convolve(self.price, np.ones(window)/window, mode='valid')
		return moving_averages

if __name__ == "__main__":
	import matplotlib.pyplot as plt
	print("Correlation between price and earnings per share:")
	WLK_foundamental = FoundamentalAnalyzer("WLK.txt")
	kendall = WLK_foundamental.correlate_price_earning()
	print("WLK:", kendall)
	PFE_foundamental = FoundamentalAnalyzer("PFE.txt")
	kendall = PFE_foundamental.correlate_price_earning()
	print("PFE:", kendall)
	TSN_foundamental = FoundamentalAnalyzer("TSN.txt")
	ma_q4 = TSN_foundamental.compute_moving_average(4)
	kendall = TSN_foundamental.correlate_price_earning()
	print("TSN:", kendall)
	plt.plot(TSN_foundamental.date[:-3], ma_q4,label = "MA 4Q")
	plt.plot(TSN_foundamental.date, TSN_foundamental.price, label = "MA 1Q")
	plt.legend()
	plt.show()
