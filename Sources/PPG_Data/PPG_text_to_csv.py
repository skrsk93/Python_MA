import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

#plt.style.use('ggplot')

data = np.genfromtxt(r'/Users/stephankrauskopf/Documents/Python_MA/Dataset/Data File/0_subject/2_1.txt')
time = np.arange(0,2.1,0.001)

plt.xlabel('Time')
plt.plot(time,data)
plt.show()
print(data)

#read_file = pd.read_csv (r'/Users/stephankrauskopf/Documents/Python_MA/Dataset/Data File/0_subject/2_1.txt')
#read_file.to_csv (r'/Users/stephankrauskopf/Documents/Python_MA/PPG Data/', index=None)