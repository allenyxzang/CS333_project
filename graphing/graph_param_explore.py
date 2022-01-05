import os
import json
import numpy as np
from matplotlib.cm import get_cmap
from matplotlib import pyplot as plt

# network params
lifetime = 100
probability = "large"
memories = "multi"

# data storage locations
data_dir = "data"
network_dir_template = "bottleneck_{}_memo"
filename_template = "data_{}_life_{}_prob.json"
filename_adapt_template = "data_adaptive_{}_life_{}_prob.json"
path = os.path.join(os.getcwd(), data_dir, network_dir_template.format(memories))

# plotting
cmap = get_cmap('viridis')
fig, ax = plt.subplots(2, 1, figsize=(7, 7))


# get data for non-adaptive
filename = os.path.join(path, filename_template.format(lifetime, probability))
fh = open(filename)
data = json.load(fh)
latencies = data["average_latencies"]
latencies_list = data["latencies"]

num_latencies = len(latencies)
high_percentile = np.zeros(num_latencies)
for i in range(num_latencies):
    high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 95)

color = cmap(0)
ax[0].plot(latencies, color=color)
ax[1].plot(high_percentile, color=color)

# get data for adaptive
filename = os.path.join(path, filename_adapt_template.format(lifetime, probability))
fh = open(filename)
data = json.load(fh)
latencies = data["average_latencies"]
latencies_list = data["latencies"]

num_latencies = len(latencies)
high_percentile = np.zeros(num_latencies)
for i in range(num_latencies):
    high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 95)

color = cmap(10/11)
ax[0].plot(latencies, color=color)
ax[1].plot(high_percentile, color=color)


legend = [r'$\alpha$={}'.format(a) for a in [0, 0.05]]
ax[0].set_title("Average Latencies")
ax[0].set_ylabel("Latency")
ax[0].legend(legend, loc='upper left')
ax[1].set_title("Max Latencies")
ax[1].set_xlabel("Request Number")
ax[1].set_ylabel("Latency")

fig.tight_layout()
fig.savefig("graph_{}_life_{}_prob.png".format(lifetime, probability))
fig.show()
