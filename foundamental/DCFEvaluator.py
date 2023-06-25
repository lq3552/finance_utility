import numpy as np

class DCFEvaluator(object):
	def __init__(self, market_cap0, market_cap, period, equity, debt,
			tax_rate, margin_tax_rate,
			r0, default_interest_rate_spread,
			EBIT, interest, depreciation, capital_expenditure, working_capital0, working_capital,
			beta = 1.0, term = 10):
		self.E = equity
		self.D = debt
		self.V = self.E + self.D
		anualized_capital_return = (market_cap / market_cap0)**(1.0 / period) - 1.0
		ERP = anualized_capital_return - r0
		self.Re = r0 + beta * ERP
		self.Rd = (r0 + default_interest_rate_spread) * (1.0 - margin_tax_rate)
		self.Tc = tax_rate
		self.WACC = 0.0586191807254955#self.E / self.V * self.Re + self.D / self.V * self.Rd * (1 - self.Tc)
		print(self.WACC)
		self.EBIT = EBIT
		delta_working_capital = working_capital - working_capital0
		self.FCFF = 660e8#EBIT * (1 - tax_rate) + interest + depreciation - capital_expenditure - delta_working_capital
		self.term = term
		self.growth_rate = np.zeros(term)
		self.growth_rate = np.array([1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.4, 1.3, 1.2, 1.1]) / 100.0
		self.growth_rate_perpetual = 1.0 / 100.0
		self.PV = 0.0
		print(self.FCFF)

	def evaluate_PV(self):
		self.PV = 0.0
		FCFF = self.FCFF
		for i in range(self.term):
			FCFF *= 1 + self.growth_rate[i]
			self.PV += FCFF / (1.0 + self.WACC)**(i + 1)
		FCFF *= (1 + self.growth_rate_perpetual) / (self.WACC - self.growth_rate_perpetual)
		self.PV += FCFF / (1.0 + self.WACC)**self.term
		print(self.PV/8015e8 - 1)


if __name__ == "__main__":
	evaluator = DCFEvaluator(100, 3050.12, 30, 1253.0, 317.0,
			25 / 100.0, 35 / 100.0,
			3.27 / 100.0, 0.75 / 100.0,
			355.85 / (1 - 25 / 100.0), 1.36, 1.68, 16.07, -49.74, -57.42)
	evaluator.evaluate_PV()
