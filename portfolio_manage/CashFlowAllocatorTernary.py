import numpy as np

class CashFlowAllocatorTernary(object):
	'''
		Purpose: allocate new cash flows to three types of assets, based on the target proportion
		Variables:
			asset1: capitalization of Asset 1 already owned
			asset2
			asset3
			ratio12: ratio of capitalizations of Asset 1 to that of Asset 2
			ratio13: if this ratio = np.inf then asset3 is ignored
	'''
	def __init__(self, asset1 : np.float64 = 0.0, asset2 : np.float64 = 0.0, asset3 : np.float64 = 0.0, ratio12 : np.float64 = 1.0, ratio13 : np.float64 = np.inf):
		self.ratio12 = ratio12
		self.ratio13 = ratio13
		self.asset1 = asset1
		self.asset2 = asset2
		self.asset3 = asset3

	def allocate(self, cashFlow) -> tuple[np.float64, np.float64, np.float64]:
		try: # for now, ratio12 must not be Inf, ratio13 can be Inf
			sumNew = self.asset1 + self.asset2 + self.asset3 + cashFlow
			assetNew2 = sumNew / (self.ratio12 + 1.0 + self.ratio12 / self.ratio13) 
			cashFlow2 = assetNew2 - self.asset2
			assetNew3 = self.ratio12 * assetNew2 / self.ratio13
			cashFlow3 = assetNew3 - self.asset3
			assetNew1 = sumNew - assetNew2 - assetNew3
			cashFlow1 = cashFlow - cashFlow2 - cashFlow3
		except:
			cashFlow1 = CashFlow
			cashFlow2 = 0.0
			cashFlow3 = 0.0
		finally:
			return (round(cashFlow1, 2), round(cashFlow2, 2), round(cashFlow3, 2))


if __name__ == "__main__":
	asset1 = 0.0
	asset2 = 1.5
	asset3 = 1.0
	cashAllocator = CashFlowAllocatorTernary(asset1, asset2, asset3, ratio12 = 2. / 3., ratio13 = 2.0)
	allocation = cashAllocator.allocate(6.5)
	print("CF = ", allocation)
	print("Asset = ", (asset1 + allocation[0], asset2 + allocation[1], asset3 + allocation[2]))

