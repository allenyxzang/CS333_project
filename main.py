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

    # metrics
    latencies = []  # keep track of latencies for each request to get completed
    congestion = []  # keep track of number of incompleted requests at the end of each time step
    request_complete_times = []  # keep track of when each request is completed
    entanglement_available = []  # keep track of entanglement links stemming from route nodes when a request is submitted
    entanglement_ondemand = []  # keep track of entanglement links generated on demand to complete a request
    entanglement_usage_pattern = {"available":[], "ondemand":[]}  # keep track of entanglement usage pattern for every request

    # get first request
    request = request_stack.pop(0)
    requests_to_serve = []  # keep track of incompleted requests, in case new request comes in before previous request is completed

    while time < end_time:
        # determine if a new request is submitted to the network
        if time == request.start_time:
            # submit request
            requests_to_serve.append(request)
            
            # find path and assign to route attribute
            route = request.get_path(graph_arr, nodes)
            request.route = route

            # two neighbors to maintain entanglement as local information on each node in route
            for i in range(len(route)):
                idx = route[i]
                if i == 0:
                    left = -1  # left == -1 means leftmost node in route
                    right = route[i+1]
                    
                elif i == len(route)-1:
                    left = route[i-1]
                    right = -2  # right == -2 means rightmost node in route

                else:
                    left = route[i-1]
                    right = route[i+1]

                two_neighbors = (left, right)
                nodes[idx].neighbors_to_connect.append(two_neighbors)

            # adaptively update probability distribution when a request is submitted to the network
            for node in nodes:
                if node.label not in route:
                    continue

                links_available = []
                links_used = []

                for idx in node.entanglement_link_nums.keys():
                    # determine if entanglement links are available
                    if node.entanglement_link_nums[idx] > 0:
                        links_available.append(idx)
                        # entanglement links available for nodes in the route for this request
                        links = [(node.label, idx)] * node.entanglement_link_nums[idx]
                        entanglement_available.extend(links)
                        # determine if the available entanglement links are in the route of the request (a used link)
                        if idx in node.neighbors_to_connect[-1]:
                            links_used.append(idx)

                # record entanglement links available (stemming from nodes in route) and reset entanglement_available
                entanglement_usage_pattern["available"].append(entanglement_available)
                entanglement_available = []

                node.generation_protocol.update_dist(links_available, links_used)
        
        # serve only the first request in queue at a time
        if len(requests_to_serve) > 0:
            route = requests_to_serve[0].route
            origin_node = nodes[route[0]]
            destination_node = nodes[route[-1]]
        else:
            route = []

        # call function to run node (entanglement generation) protocol
        for node in nodes:
            if node.label in route:
                left = node.neighbors_to_connect[0][0]
                left_node = nodes[left]
                right = node.neighbors_to_connect[0][1]
                right_node = nodes[right]

                # determine if the node is the origin node of the route
                if node == origin_node:
                    # if there is no entanglement link between it and its right neighbor, create it on demand
                    if node.entanglement_link_nums[right] == 0:
                        node.create_link(time, right_node)
                        entanglement_ondemand.append((node.label, right))

                # determine if the node is the destination node of the route
                elif node == destination_node:
                    # if there is no entanglement link between it and its left neighbor, create it on demand
                    if node.entanglement_link_nums[left] == 0:
                        node.create_link(time, left_node)
                        entanglement_ondemand.append((left, node.label))

                # otherwise the node is in the middle of the route
                else:
                    # if there is no entanglement link between it and its left neighbor, create it on demand
                    if node.entanglement_link_nums[left] == 0:
                        node.create_link(time, left_node)
                        entanglement_ondemand.append((left, node.label))
                    
                    # if there is no entanglement link between it and its right neighbor, create it on demand
                    elif node.entanglement_link_nums[right] == 0:
                        node.create_link(time, right_node)
                        entanglement_ondemand.append((node.label, right))

                    # if both sides have entanglement links, try swapping
                    else:
                        # there can be multiple links and choose only one at a time
                        for memory in node.memories:
                            if memory.entangled_memory["node"] == left_node:
                                left_memory = memory
                                break
                        for memory in node.memories:
                            if memory.entangled_memory["node"] == right_node:
                                right_memory = memory
                                break
                        
                        node.swap(left_memory, right_memory)

            else:
                node.create_random_link(time)

        # determine if the desired entanglement is established
        if len(requests_to_serve) > 0:
            for memory in origin_node.memories:
                # check if have memory entangled with destination
                if memory.entangled_memory["node"] == destination_node:
                    # record latency and completion time
                    completed_request = requests_to_serve.pop(0)
                    latency = time - completed_request.start_time
                    latencies.append(latency)
                    request_complete_times.append(time)

                    # clean neighbors_to_connect information for nodes in current route
                    for i in range(len(route)-1):
                        idx = route[i]
                        nodes[idx].neighbors_to_connect.pop(0)

                    # record entanglement links generated on demand and reset entanglement_ondemand
                    entanglement_usage_pattern["ondemand"].append(entanglement_ondemand)
                    entanglement_ondemand = []

                    break

        congestion.append(len(requests_to_serve))

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
        time_list = gen_request_time_list(10, 30, interval=15)
        # Generate request stack
        request_stack = [Request(time, pair) for time, pair in zip(time_list, pair_queue)]

        # Run simulation
        res = run_simulation(graph_arr, nodes, request_stack, END_TIME)

# TODO: request methods

# TODO: network topology, etc.
