import json
import numpy as np
import matplotlib
from matplotlib import pyplot as plt

cmap = matplotlib.cm.get_cmap('viridis')

adaptive_parameters = [0, 0.05, 0.1, 0.15, 0.2]
legend = [r'\alpha={}'.format(a) for a in adaptive_parameters]
avg_latencies = []
max_latencies = []

for alpha in adaptive_parameters:
    filename = "data_adaptive_{}.json".format(alpha)
    fh = open(filename)
    data = json.load(fh)
    latencies = data["average_latencies"]
    latencies_list = data["latencies"]

    num_latencies = len(latencies)
    high_percentile = np.zeros(num_latencies)
    for i in range(num_latencies):
        high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 95)

    avg_latencies.append(latencies)
    max_latencies.append(high_percentile)

fig, ax = plt.subplots(2, 1, figsize=(7, 7))

for alpha, al, ml in zip(adaptive_parameters, avg_latencies, max_latencies):
    color = cmap(alpha/(max(adaptive_parameters)*1.1))  # exclude bright yellow
    ax[0].plot(np.arange(len(al)), al, color=color)
    ax[1].plot(np.arange(len(ml)), ml, color=color)
ax[0].set_title("Average Latencies")
ax[0].set_xlabel("Request Number")
ax[0].set_ylabel("Latency")
ax[0].legend(legend, loc='upper left')
ax[1].set_title("Max Latencies")
ax[1].set_xlabel("Request Number")
ax[1].set_ylabel("Latency")

fig.tight_layout()
fig.savefig("graph_multi.png")
fig.show()
