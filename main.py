from numpy.random import default_rng
from simulation_core import *
from hardware import *
from protocols import *

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


def run_simulation(graph_arr, nodes, request_stack, end_time):
    time = 0
    request_time = 0  # TODO: request class
    request_completed = False  # TODO: request class
    requests_toserve = [] # keep track of incompleted requests, in case new request comes in before previous request is completed
    congestion = [] # keep track of number of incompleted requests at the end of each time step

    while time < end_time:
        # call function to run node protocol
        for node in nodes:
            node.create_random_link(time)

        if time == request_time:
            # submit request and update next request time
            request_tuple = request_stack.pop()
            request_time, request_pair, request = request_tuple[0]
            requests_toserve.append(request)
            # TODO: how the first request to serve determine what operation to perform
            
        if request_completed:
            # record latency
            pass

        congestion.append(len(requests_toserve))

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
        # Generate request node pair queue
        pair_queue = gen_pair_queue(traffic_mtx, NET_SIZE, 30, rng, rng)
        # Generate request submssion time list with constant interval
        time_list = gen_request_time_list(10, 30, interval = 15)
        # Generate request stack instance
        request_stack = RequestStack(time_list, pair_queue)

        # Run simulation
        res = run_simulation(graph_arr, nodes, request_stack, END_TIME)

# TODO: request methods

# TODO: network topology, etc.
