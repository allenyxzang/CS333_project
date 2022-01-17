import os
from matplotlib import pyplot as plt

from graph_utils import *

QUEUE_INT = 500
window_size = 3

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

    avg_latency = get_moving_average(latencies, window_size)
    avg_high = get_moving_average(high_percentile, window_size)

    avg_latencies.append(avg_latency)
    max_latencies.append(avg_high)
    legend.append("Adaptive")

if UNIFORM:
    filename = os.path.join(path, filename_uniform)
    latencies, high_percentile = get_data(filename)

    avg_latency = get_moving_average(latencies, window_size)
    avg_high = get_moving_average(high_percentile, window_size)

    avg_latencies.append(avg_latency)
    max_latencies.append(avg_high)
    legend.append("Uniform")

if POWER_LAW:
    filename = os.path.join(path, filename_powerlaw)
    latencies, high_percentile = get_data(filename)

    avg_latency = get_moving_average(latencies, window_size)
    avg_high = get_moving_average(high_percentile, window_size)

    avg_latencies.append(avg_latency)
    max_latencies.append(avg_high)
    legend.append("Power Law")

fig, ax = plt.subplots(2, 1, figsize=(7, 4))

for al in avg_latencies:
    time = np.arange(len(al)) * QUEUE_INT
    ax[0].plot(time, al)
ax[0].set_title("Average Latencies")
ax[0].set_ylabel("Latency")
ax[0].tick_params(bottom=False, labelbottom=False)

for ml in max_latencies:
    time = np.arange(len(ml)) * QUEUE_INT
    ax[1].plot(time, ml)
ax[1].set_title("Max Latencies")
ax[1].set_xlabel("Simulation Time")
ax[1].set_ylabel("Latency")

fig.legend(legend, loc='center left', bbox_to_anchor=(1, 0.5))

fig.tight_layout()
fig.savefig("graph.png",  bbox_inches='tight')
