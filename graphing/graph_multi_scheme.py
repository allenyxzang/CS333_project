import os
from matplotlib import pyplot as plt

from graph_utils import *

ADAPTIVE = True
UNIFORM = True
POWER_LAW = True

data_dir = "data/compare_schemes"
filename_adaptive = "data_adaptive.json"
filename_uniform = "data_uniform.json"
filename_powerlaw = "data_powerlaw.json"
path = os.path.join(os.getcwd(), data_dir)

avg_latencies = []
max_latencies = []
legend = []

if ADAPTIVE:
    filename = os.path.join(path, filename_adaptive)
    latencies, high_percentile = get_data(filename)
    avg_latencies.append(latencies)
    max_latencies.append(high_percentile)
    legend.append("Adaptive")

if UNIFORM:
    filename = os.path.join(path, filename_uniform)
    latencies, high_percentile = get_data(filename)
    avg_latencies.append(latencies)
    max_latencies.append(high_percentile)
    legend.append("Uniform")

if POWER_LAW:
    filename = os.path.join(path, filename_powerlaw)
    latencies, high_percentile = get_data(filename)
    avg_latencies.append(latencies)
    max_latencies.append(high_percentile)
    legend.append("Power Law")

fig, ax = plt.subplots(2, 1, figsize=(7, 5))

for al in avg_latencies:
    ax[0].plot(np.arange(len(al)), al)
ax[0].set_title("Average Latencies")
ax[0].set_ylabel("Latency")

for ml in max_latencies:
    ax[1].plot(np.arange(len(ml)), ml)
ax[1].set_title("Max Latencies")
ax[1].set_xlabel("Request Number")
ax[1].set_ylabel("Latency")

fig.legend(legend, loc='center left', bbox_to_anchor=(1, 0.5))

fig.tight_layout()
fig.savefig("graph.png",  bbox_inches='tight')
