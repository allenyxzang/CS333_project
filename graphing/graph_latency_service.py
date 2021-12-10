import json
import numpy as np
from matplotlib import pyplot as plt

filename = "data_adaptive.json"
fh = open(filename)
data = json.load(fh)
latencies = data["average_latencies"]
service_times = data["average_service_times"]
latencies_list = data["latencies"]
service_times_list = data["service_times"]

num_latencies = len(latencies)
high_percentile_latencies = np.zeros(num_latencies)
high_percentile_service = np.zeros(num_latencies)
for i in range(num_latencies):
    high_percentile_latencies[i] = np.percentile([ll[i] for ll in latencies_list], 95)
    high_percentile_service[i] = np.percentile([sl[i] for sl in service_times_list], 95)

fig, ax = plt.subplots(2, 1, figsize=(7, 7))

ax[0].plot(np.arange(num_latencies), latencies)
ax[0].plot(np.arange(num_latencies), service_times)
ax[0].set_title("Average Value")
ax[0].set_ylabel("Time")
ax[0].legend(["Latency", "Service Time"])

ax[1].plot(np.arange(num_latencies), high_percentile_latencies)
ax[1].plot(np.arange(num_latencies), high_percentile_service)
ax[1].set_title("Max Value")
ax[1].set_xlabel("Request Number")
ax[1].set_ylabel("Time")

fig.tight_layout()
fig.savefig("graph_latency_service.png")
fig.show()
