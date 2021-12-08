import json
import numpy as np
from matplotlib import pyplot as plt

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
    fh_adaptive = open(filename_adaptive)
    adaptive_data = json.load(fh_adaptive)
    adaptive_latencies = adaptive_data["average_latencies"]
    latencies_list = adaptive_data["latencies"]

    num_latencies = len(adaptive_latencies)
    high_percentile = np.zeros(num_latencies)
    for i in range(num_latencies):
        high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 95)

    avg_latencies.append(adaptive_latencies)
    max_latencies.append(high_percentile)
    legend.append("Adaptive")

if UNIFORM:
    fh_uniform = open(filename_uniform)
    uniform_data = json.load(fh_uniform)
    uniform_latencies = uniform_data["average_latencies"]
    latencies_list = uniform_data["latencies"]

    num_latencies = len(uniform_latencies)
    high_percentile = np.zeros(num_latencies)
    for i in range(num_latencies):
        high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 95)

    avg_latencies.append(uniform_latencies)
    max_latencies.append(high_percentile)
    legend.append("Uniform")

if POWER_LAW:
    fh_powerlaw = open(filename_powerlaw)
    powerlaw_data = json.load(fh_powerlaw)
    powerlaw_latencies = powerlaw_data["average_latencies"]
    latencies_list = powerlaw_data["latencies"]

    num_latencies = len(powerlaw_latencies)
    high_percentile = np.zeros(num_latencies)
    for i in range(num_latencies):
        high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 95)

    avg_latencies.append(powerlaw_latencies)
    max_latencies.append(high_percentile)
    legend.append("Power Law")

fig, ax = plt.subplots(2, 1, figsize=(7, 7))

for al in avg_latencies:
    ax[0].plot(np.arange(len(al)), al)
ax[0].set_title("Average Latencies")
ax[0].set_xlabel("Request Number")
ax[0].set_ylabel("Latency")
ax[0].legend(legend)

for ml in max_latencies:
    ax[1].plot(np.arange(len(ml)), ml)
ax[1].set_title("Max Latencies")
ax[1].set_xlabel("Request Number")
ax[1].set_ylabel("Latency")
ax[1].legend(legend)

fig.tight_layout()
fig.savefig("graph.png")
fig.show()
