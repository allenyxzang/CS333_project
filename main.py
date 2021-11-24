from numpy.random import default_rng
from simulation_core import *
from hardware import Node

# Network parameters
CONFIG = "network.json"
GENERATE_NEW = True
NET_SIZE = 100
NET_TYPE = "as_net"
SEED = 0

# Node parameters
MEMO_SIZE = 1
MEMO_LIFETIME = 100  # in units of simulation time step
ENTANGLEMENT_GEN_PROB = 0.01
ENTANGLEMENT_SWAP_PROB = 1
ADAPT_WEIGHT = 0.5

# Simulation parameters
SIM_SEED = 0
END_TIME = 100
NUM_TRIALS = 100
QUEUE_LEN = 100


def run_simulation(graph_arr, nodes, queue, end_time):
    time = 0
    request_time = 0  # TODO: request class
    request_completed = False  # TODO: request class

    while time < end_time:
        # call function to run node protocol
        for node in nodes:
            node.create_random_link(time)

        if time == request_time:
            # submit request and update next request time
            pass
        if request_completed:
            # record latency
            pass

        time += 1

    # average latencies (over time) and return

    raise NotImplementedError


if __name__ == "__main__":
    # Setup rng
    rng = default_rng(SIM_SEED)

    # Generate network
    if GENERATE_NEW:
        graph_arr = gen_network_json(CONFIG, NET_SIZE, NET_TYPE, SIM_SEED)
    else:
        fh = open(CONFIG)
        topo = json.load(fh)
        graph_arr = topo["array"]
        assert graph_arr.shape == (NET_SIZE, NET_SIZE)
    nodes = []
    for i in range(NET_SIZE):
        neighbors = [j for j, element in enumerate(graph_arr[i]) if element != 0]
        node = Node(i, neighbors, MEMO_SIZE, MEMO_LIFETIME,
                    ENTANGLEMENT_GEN_PROB, ENTANGLEMENT_SWAP_PROB, ADAPT_WEIGHT, i)
        nodes.append(node)

    # Generate traffic matrix
    traffic_mtx = gen_traffic_mtx(NET_SIZE, rng)

    for trial in range(NUM_TRIALS):
        # Generate queue
        queue = gen_request_queue(traffic_mtx, NET_SIZE, QUEUE_LEN, rng, rng)

        # Run simulation
        res = run_simulation(graph_arr, nodes, queue, END_TIME)

# TODO: request methods

# TODO: network topology, etc.
