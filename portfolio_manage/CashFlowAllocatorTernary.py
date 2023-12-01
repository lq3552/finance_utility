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

	def __call__(self, cashFlow) -> tuple[np.float64, np.float64, np.float64]:
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
	'''
	Here is an example of application:
	(1) We have a total cashFlow
	(2) We split it into cashFlowPrimary and cashFlowSecondary
	(3) For we plan to invest cashFlowPrimary into EMU stock and 
	    EMU intermediate bond, the ratio is 2:3
	(4) But we don't actually invest the cash cash flow into EMU Stock,
	    instead, this amount will be added to cashFlowSecondary
	(5) Then we invest cashFlowSecondary into EMU ultra-short bond and
	    short bond, the ratio is 1:1
	'''
	cashFlowPrimary   = 300.0
	cashFlowSecondary = 200.0

	emuStock = (100 + 50 / 40) * 41
	emuBond  = 6543
	cashAllocator = CashFlowAllocatorTernary(emuStock, emuBond, asset3 = 0, ratio12 = 2. / 3.)
	allocationPrimary = cashAllocator(cashFlowPrimary)

	emuUltrashortBond = 2345
	emuShortBond = 2435
	cashAllocator = CashFlowAllocatorTernary(emuUltrashortBond, emuShortBond, asset3 = 0, ratio12 = 1)
	allocationSecondary = cashAllocator(cashFlowSecondary + allocationPrimary[0])

	allocation = (allocationPrimary[1], allocationSecondary[0], allocationSecondary[1])
	print("(EMU Intermediate Bond, EMU Ultrashort Bond, EMU Short Bond) = ", allocation)
	print("(EMU Stock Equivalent) = ", allocationPrimary[0])
