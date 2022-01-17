import json
import numpy as np


def get_data(filename):
    fh = open(filename)
    data = json.load(fh)
    latencies = data["average_latencies"]
    latencies_list = data["latencies"]

    num_latencies = len(latencies)
    high_percentile = np.zeros(num_latencies)
    for i in range(num_latencies):
        high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 95)

    return latencies, high_percentile


def get_moving_average(data, w):
    return np.convolve(data, np.ones(w), 'valid') / w
