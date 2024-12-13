import numpy as np

class BondFixedRatePresentValueCalculator(object):
    '''
        Purpose: calculate present value of a fixed-rate bond
        Variables:
            parValue: par value of the bond
            couponRate: coupon rate
            y: yield to maturity
            t: term to maturity
        callable return: 
            pv: present value
    '''
    def __init__(self, parValue : np.float64 = 100.0, couponRate : np.float64 = 0.0, y : np.float64 = 0.0, t : int = 1):
        self.parValue = parValue
        self.couponRate = couponRate
        self.y = y
        self.t = t

    def __call__(self) -> np.float64:
        coupon = self.parValue * self.couponRate
        pv = 0.0
        yt = 1.0 + self.y
        for i in range(0, self.t):
            pv += coupon / yt ** (i + 1)
        pv += self.parValue / yt ** self.t
        return pv
            

if __name__ == "__main__":
    calculator = BondFixedRatePresentValueCalculator(100.0, 0.01, 0.0315, 5)
    pv1 = calculator()
    calculator = BondFixedRatePresentValueCalculator(100.0, 0.01, 0.01, 5)
    pv2 = calculator()
    print("PV_3.15 = ", pv1)
    print("PV_1.00 = ", pv2)
    print("change = ", pv2 / pv1 - 1.0)
