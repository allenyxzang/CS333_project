import json
import networkx as nx
import numpy as np


def gen_network_json(filename, size, net_type, seed=0):
    if net_type == "ring":
        arr = np.ndarray((size, size), int)
        for i in range(size):
            arr[i, (i+1) % size] = 1
            arr[(i+1) % size, i] = 1

    elif net_type == "as_net":
        G = nx.random_internet_as_graph(size, seed)
        arr = nx.convert_matrix.to_numpy_array(G)

    else:
        raise ValueError("Unknown graph type " + net_type)

    fh = open(filename, 'w')
    topo = {"array": arr.tolist()}
    json.dump(topo, fh)
    return arr


# generator of traffic matrix 
def gen_traffic_mtx(node_num, rng):
    mtx = rng.normal(size=(node_num, node_num))
    for i in range(node_num):
        mtx[i, i] = 0  # no self-to-self traffic

    return mtx


# generator of request node pair queue
def gen_pair_queue(traffic_mtx, node_num, queue_len, rng_mtx, rng_judge):
    queue = []
    idx = 0
    while idx < queue_len:
        # random selection of traffic matrix element for judgement
        rand_row = rng_mtx.integers(node_num)
        rand_col = rng_mtx.integers(node_num)

        if rng_judge.random() < traffic_mtx[rand_row, rand_col]:
            # request node pair in form of two-element tuple
            # first element is the label of the origin node, and second element is the label of the destination
            queue.append((rand_row, rand_col))
            idx += 1
    
    return queue


def gen_request_time_list(start_time, num_request, interval=10):
    """Function to generate a list of times when a request starts to get served.
    This mimics a central request controller.
    The time interval between adjacent request is constant.
    """

    request_time_list = np.arange(start_time, num_request*interval + start_time, step=interval)
    return request_time_list


def gen_request_time_list_rand(start_time, num_request, rng, lower_bound=1, upper_bound=10):
    """Function to generate a list of times when a request starts to get served.
    This mimics a central request controller.
    The time interval between adjacent requests is a random integer.
    This function may be modified to change the distribution.
    """

    request_time_list = [start_time]
    for i in range(num_request - 1):
        request_time_list.append(request_time_list[-1] + rng.random.random_integers(lower_bound, high=upper_bound))

    return request_time_list
