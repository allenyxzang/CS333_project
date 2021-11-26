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
    # request_completed = False  # TODO: request class
    requests_toserve = [] # keep track of incompleted requests, in case new request comes in before previous request is completed
    latencies = [] # keep track of latencies for each request to get completed
    congestion = [] # keep track of number of incompleted requests at the end of each time step
    request_complete_times = [] # keep track of when each request is completed

    while time < end_time:
        # determine if a new request is submitted to the network
        if time == request_time:
            # submit request and update next request time
            request_tuple = request_stack.pop(0)
            request_time, request_pair, request = request_tuple[0]
            
            # find path and assign to route attribute
            route = request.get_path(graph_arr, nodes)
            request.route = route

            requests_toserve.append(request)

            # two neighbors to maintain entanglement as local information on each node in route
            for i in range(len(route)):
                idx = route[i]
                if i == 0:
                    left = -1 # left == -1 means leftmost node in route
                    right = route[i+1]
                    
                elif i == len(route)-1:
                    left = route[i-1]
                    right = -2 # right == -2 means rightmost node in route

                else:
                    left = route[i-1]
                    right = route[i+1]

                two_neighbors = (left, right)
                nodes[idx].neighbors_to_connect.append(two_neighbors)

            # TODO: adaptively update probability distribution when a request is submitted to the network
            # TODO: record available links, to be used links, to be generated links for visualization
        
        route = requests_toserve[0].route
        origin_node = nodes[route[0]]
        destination_node = nodes[route[-1]]

        # call function to run node (entanglement generation) protocol
        for node in nodes:
            if node.label in route:
                left = node.neighbors_to_connect[0][0]
                right = node.neighbors_to_connect[0][1]

                # determine if the node is the origin node of the route
                if node == origin_node:
                    # if there is no entanglement link between it and its right neighbor, create it on demand
                    if node.entanglement_link_nums[right.label] == 0:
                        node.create_link(time, right)

                # determine if the node is the destination node of the route
                elif node == destination_node:
                    # if there is no entanglement link between it and its left neighbor, create it on demand
                    if node.entanglement_link_nums[left.label] == 0:
                        node.create_link(time, left)

                # otherwise the node is in the middle of the route
                else:
                    # if there is no entanglement link between it and its left neighbor, create it on demand
                    if node.entanglement_link_nums[left.label] == 0:
                        node.create_link(time, left)
                    
                    # if there is no entanglement link between it and its right neighbor, create it on demand
                    elif node.entanglement_link_nums[right.label] == 0:
                        node.create_link(time, right)

                    # if both sides have entanglement links, try swapping
                    else:
                        # there can be multiple links and choose only one at a time
                        for memory in node.memories:
                            if memory.entangled_memory["node"] == left:
                                left_memory = memory
                                return
                        for memory in node.memories:
                            if memory.entangled_memory["node"] == right:
                                right_memory = memory
                                return
                        
                        node.swap(left_memory, right_memory)

            else:
                node.create_random_link(time)

        # determine if the desired entanglement is established
        for memory in origin_node.memories:
            if memory.entangled_memory["node"] == destination_node:
                requests_toserve[0].is_completed = True

        if requests_toserve[0].is_completed:
            # record latency and completion time
            completed_request = requests_toserve.pop(0)
            latency = time - completed_request.start_time
            latencies.append(latency)
            request_complete_times.append(time)

            # clean neighbors_to_connect information for nodes in current route
            for i in range(len(route)-1):
                idx = route[i]
                nodes[idx].neighbors_to_connect.pop(0)

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
