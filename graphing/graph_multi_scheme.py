from matplotlib import pyplot as plt

from graph_utils import *

ADAPTIVE = True
UNIFORM = True
POWER_LAW = True

filename_adaptive = "data_adaptive.json"
filename_uniform = "data_uniform.json"
filename_powerlaw = "data_powerlaw.json"

avg_latencies = []
max_latencies = []
legend = []

if ADAPTIVE:
    latencies, high_percentile = get_data(filename_adaptive)
    avg_latencies.append(latencies)
    max_latencies.append(high_percentile)
    legend.append("Adaptive")

if UNIFORM:
    latencies, high_percentile = get_data(filename_uniform)
    avg_latencies.append(latencies)
    max_latencies.append(high_percentile)
    legend.append("Uniform")

if POWER_LAW:
    latencies, high_percentile = get_data(filename_powerlaw)
    avg_latencies.append(latencies)
    max_latencies.append(high_percentile)
    legend.append("Power Law")

fig, ax = plt.subplots(2, 1, figsize=(7, 7))

for al in avg_latencies:
    ax[0].plot(np.arange(len(al)), al)
ax[0].set_title("Average Latencies")
ax[0].set_ylabel("Latency")
ax[0].legend(legend)

for ml in max_latencies:
    ax[1].plot(np.arange(len(ml)), ml)
ax[1].set_title("Max Latencies")
ax[1].set_xlabel("Request Number")
ax[1].set_ylabel("Latency")

fig.tight_layout()
fig.savefig("graph.png")
fig.show()
