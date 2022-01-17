import os
from matplotlib import pyplot as plt

from graph_utils import *

# network params
lifetimes = [1000, 1000, 100]
probabilities = ["small", "large", "small"]
prob_values = {"small": 0.01, "large": 0.1}
memories = [5, 30]
QUEUE_INT = 200
window_size = 3

# data storage locations
data_dir = "data"
network_dir_template = "bottleneck_{}_memo"
filename_template = "data_{}_life_{}_prob.json"
filename_adapt_template = "data_adaptive_{}_life_{}_prob.json"
data_path = os.path.join(os.getcwd(), data_dir)

# plotting
styles = ["-", "--"]
fig, ax = plt.subplots(3, 1, figsize=(7, 6))
legend = []
for mem_count in memories:
    legend.append("Adaptive, {} memories".format(mem_count))
    legend.append("Non-adaptive, {} memories".format(mem_count))

for i, (lifetime, probability) in enumerate(zip(lifetimes, probabilities)):
    for mem_count, style in zip(memories, styles):
        path = os.path.join(data_path, network_dir_template.format(mem_count))

        # get data for adaptive
        filename = os.path.join(path, filename_adapt_template.format(lifetime, probability))
        latencies, _ = get_data(filename)
        avg_latencies = get_moving_average(latencies, window_size)
        time = np.arange(len(avg_latencies)) * QUEUE_INT
        ax[i].plot(time, avg_latencies, color='tab:blue', ls=style)

        # get data for non-adaptive
        filename = os.path.join(path, filename_template.format(lifetime, probability))
        latencies, _ = get_data(filename)
        avg_latencies = get_moving_average(latencies, window_size)
        time = np.arange(len(avg_latencies)) * QUEUE_INT
        ax[i].plot(time, avg_latencies, color='tab:orange', ls=style)

    ax[i].set_title(r'Average Latencies ($\tau_m$ = {}, $p_e$ = {})'.format(
        lifetime, prob_values[probability]))
    ax[i].set_ylabel("Latency")

    if i != len(lifetimes) - 1:
        ax[i].tick_params(bottom=False, labelbottom=False)

ax[-1].set_xlabel("Simulation Time")
ax[-1].legend(legend, loc='upper center', bbox_to_anchor=(0, -0.5, 1, 0), ncol=2)

fig.tight_layout()
fig.savefig("graph_bottleneck_multi.png", bbox_inches='tight')
