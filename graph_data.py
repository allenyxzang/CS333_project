import json
import numpy as np
from matplotlib import pyplot as plt

filename_adaptive = "data_all_nodes/data_adaptive.json"
filename_uniform = "data_all_nodes/data_uniform.json"
filename_powerlaw = "data_all_nodes/data_powerlaw.json"

fh_adaptive = open(filename_adaptive)
adaptive_data = json.load(fh_adaptive)
adaptive_latencies = adaptive_data["average_latencies"]
fh_uniform = open(filename_uniform)
uniform_data = json.load(fh_uniform)
uniform_latencies = uniform_data["average_latencies"]
fh_powerlaw = open(filename_powerlaw)
powerlaw_data = json.load(fh_powerlaw)
powerlaw_latencies = powerlaw_data["average_latencies"]

num_latencies = min([len(adaptive_latencies), len(uniform_latencies), len(powerlaw_latencies)])
requests_latencies = np.arange(num_latencies)
plt.plot(requests_latencies, adaptive_latencies)
plt.plot(requests_latencies, uniform_latencies)
plt.plot(requests_latencies, powerlaw_latencies)
plt.show()
