import json
import numpy as np
from matplotlib import pyplot as plt

ADAPTIVE = True
UNIFORM = False
POWER_LAW = False

filename_adaptive = "data_adaptive.json"
filename_uniform = "data_uniform.json"
filename_powerlaw = "/data_powerlaw.json"

if ADAPTIVE:
    fh_adaptive = open(filename_adaptive)
    adaptive_data = json.load(fh_adaptive)
    adaptive_latencies = adaptive_data["average_latencies"]
    latencies_list = adaptive_data["latencies"]

    num_latencies = len(adaptive_latencies)
    low_percentile = np.zeros(num_latencies)
    high_percentile = np.zeros(num_latencies)
    for i in range(num_latencies):
        low_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 5)
        high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 95)

    plt.plot(np.arange(num_latencies), adaptive_latencies)
    plt.fill_between(num_latencies, low_percentile, high_percentile)

if UNIFORM:
    fh_uniform = open(filename_uniform)
    uniform_data = json.load(fh_uniform)
    uniform_latencies = uniform_data["average_latencies"]
    plt.plot(np.arange(len(uniform_latencies)), uniform_latencies)

if POWER_LAW:
    fh_powerlaw = open(filename_powerlaw)
    powerlaw_data = json.load(fh_powerlaw)
    powerlaw_latencies = powerlaw_data["average_latencies"]
    plt.plot(np.arange(len(powerlaw_latencies)), powerlaw_latencies)

plt.show()
