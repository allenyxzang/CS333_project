from numpy.random import default_rng
from simulation_core import *

# Network parameters
CONFIG = "network.json"
GENERATE_NEW = True
NET_SIZE = 100
NET_TYPE = "as_net"
SEED = 0

# Node parameters
MEMO_SIZE = 1
MEMO_LIFETIME = 100  # in unitS of simulation time step
ENTANGLEMENT_GEN_PROB = 0.01
ENTANGLEMENT_SWAP_PROB = 1

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
            node.create_links()

        if time == request_time:
            # submit request and update next request time
            pass
        if request_completed:
            # record latency
            pass

        time += 1

    # average latencies (over time) and return

    raise NotImplementedError


def gen_request_time_list(start_time, num_request, interval=10):
    """Function to generate a list of times at each of which a request starts to get served, in order to mimic a central request controller.
    Time interval between adjacent request is constant."""

    request_time_list = [start_time]
    for i in range(num_request - 1):
        request_time_list.append(request_time_list[-1] + interval)

    return request_time_list
    
    
def gen_request_time_list_rand(start_time, num_request, rng, lower_bound=1, upper_bound=10):
    """Function to generate a list of times at each of which a request starts to get served, in order to mimic a central request controller.
    Time interval between adjacent requests is a random integer. Can modify this function to change the distribution."""

    request_time_list = [start_time]
    for i in range(num_request - 1):
        request_time_list.append(request_time_list[-1] + rng.random.random_integers(lower_bound, high=upper_bound))

    return request_time_list


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
    nodes = [Node(i, MEMO_SIZE, MEMO_LIFETIME) for i in range(NET_SIZE)]

    # Generate traffic matrix
    traffic_mtx = gen_traffic_mtx(NET_SIZE, rng)

    for trial in range(NUM_TRIALS):
        # Generate queue
        queue = gen_request_queue(traffic_mtx, NET_SIZE, QUEUE_LEN, rng, rng)

        # Run simulation
        res = run_simulation(graph_arr, nodes, queue, END_TIME)
