import numpy as np
import matplotlib.pyplot as plt

dat = np.loadtxt("CPI.txt")
t = []
dcpi = []
for i in range(109):
	t.append(dat[3 * i])
	dcpi.append(dat[3 * i + 2])

plt.plot(t,dcpi)
plt.show()
