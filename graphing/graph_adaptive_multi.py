import os
from matplotlib.cm import get_cmap
from matplotlib import pyplot as plt

from graph_utils import *

# network params
adaptive_parameters = [0, 0.05, 0.1, 0.4]

# data storage locations
data_dir = "data/adaptive_large_network_random"
filename_template = "data_adaptive_{}.json"
path = os.path.join(os.getcwd(), data_dir)

# plotting
cmap = get_cmap('viridis')
fig, ax = plt.subplots(2, 1, figsize=(7, 5))

for alpha in adaptive_parameters:
    filename = os.path.join(path, filename_template.format(alpha))
    latencies, high_percentile = get_data(filename)

    color = cmap(adaptive_parameters.index(alpha)/((len(adaptive_parameters)-1)*1.1))  # exclude bright yellow
    ax[0].plot(latencies, color=color)
    ax[1].plot(high_percentile, color=color)

legend = [r'$\alpha$={}'.format(a) for a in adaptive_parameters]
ax[0].set_title("Average Latencies")
ax[0].set_ylabel("Latency")
ax[1].set_title("Max Latencies")
ax[1].set_xlabel("Request Number")
ax[1].set_ylabel("Latency")

fig.legend(legend, loc='center left', bbox_to_anchor=(1, 0.5))

fig.tight_layout()
fig.savefig("graph_multi.png", bbox_inches='tight')
