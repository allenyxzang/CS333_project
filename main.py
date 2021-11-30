from numpy.random import default_rng
from simulation_core import *
from hardware import *
from protocols import *

# Network parameters
CONFIG = "network.json"
GENERATE_NEW = True
NET_SIZE = 10
NET_TYPE = "as_net"
SEED = 0

# Node parameters
MEMO_SIZE = 100
MEMO_LIFETIME = 100  # in units of simulation time step
ENTANGLEMENT_GEN_PROB = 0.01
ENTANGLEMENT_SWAP_PROB = 1
ADAPT_WEIGHT = 0.5

# Simulation parameters
SIM_SEED = 0
END_TIME = 10000
NUM_TRIALS = 1
QUEUE_LEN = 100
QUEUE_START = 10
QUEUE_INT = 15


def run_simulation(graph_arr, nodes, request_stack, end_time):
    time = 0

    # metrics
    latencies = []  # keep track of latencies for each request to get completed
    congestion = []  # keep track of number of incomplete requests at the end of each time step
    request_complete_times = []  # keep track of when each request is completed
    entanglement_usage_pattern = {"available": [], "ondemand": []}  # keep track of entanglement usage pattern for every request

    requests_to_serve = []  # keep track of incomplete requests, in case new request comes in before previous request is completed
    entanglement_available = []  # keep track of entanglement links from route nodes when a request is submitted
    entanglement_ondemand = []  # keep track of entanglement links generated on demand to complete a request
    # get first request
    request = request_stack.pop(0)

    while time < end_time:
        # check if memories expired
        for node in nodes:
            for memory in node.memories:
                expire_time = memory.entangled_memory["expire_time"]
                if expire_time is not None and expire_time <= time:
                    node.memo_expire(memory)

        # determine if a new request is submitted to the network
        if time == request.start_time:
            # submit request
            requests_to_serve.append(request)
            
            # find path and assign to route attribute
            route = request.get_path(graph_arr, nodes)
            request.route = route

            # get new request
            if len(request_stack) > 0:
                request = request_stack.pop(0)

            # two neighbors to maintain entanglement as local information on each node in route
            for i in range(len(route)):
                idx = route[i]
                if i == 0:
                    left_neighbors_to_connect = []
                    right_neighbors_to_connect = [route[i+k+1] for k in range(len(route)-i-1)]
                    
                elif i == len(route)-1:
                    left_neighbors_to_connect = [route[k] for k in range(i)]
                    right_neighbors_to_connect = []

                else:
                    left_neighbors_to_connect = [route[k] for k in range(i)]
                    right_neighbors_to_connect = [route[i+k+1] for k in range(len(route)-i-1)]

                nodes[idx].left_neighbors_to_connect.append(left_neighbors_to_connect)
                nodes[idx].right_neighbors_to_connect.append(right_neighbors_to_connect)

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
                        if node.label == route[0]:
                            right_idx = node.right_neighbors_to_connect[-1][0]
                            links_used.append(right_idx)
                        elif node.label == route[-1]:
                            left_idx = node.left_neighbors_to_connect[-1][-1]
                            links_used.append(left_idx)
                        else:
                            left_idx = node.left_neighbors_to_connect[-1][-1]
                            right_idx = node.right_neighbors_to_connect[-1][0]
                            links_used.append(left_idx)
                            links_used.append(right_idx)

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
            origin_node = None
            destination_node = None
            route = []

        # call function to run node (entanglement generation) protocol
        for node in nodes:
            n = node.label

            if n in route:
                # get neighbor information in the path
                direct_right = None
                direct_right_node = None
                direct_left = None
                direct_left_node = None
                left_neighbors = node.left_neighbors_to_connect[0]
                if len(left_neighbors) > 0:
                    direct_left = left_neighbors[-1]
                    direct_left_node = nodes[direct_left]
                right_neighbors = node.right_neighbors_to_connect[0]
                if len(right_neighbors) > 0:
                    direct_right = right_neighbors[0]
                    direct_right_node = nodes[direct_right]

                # determine if the node is the origin node of the route
                if node is origin_node:
                    # if there is no entanglement link between it and its right neighbors, create link with direct right neighbor on demand
                    right_entanglement_link_nums = [node.entanglement_link_nums[i] for i in right_neighbors]
                    if not any(right_entanglement_link_nums):
                        node.create_link(time, direct_right_node)
                        entanglement_ondemand.append((node.label, direct_right))

                # determine if the node is the destination node of the route
                elif node is destination_node:
                    # if there is no entanglement link between it and its left neighbors, create link with direct left neighbor on demand
                    left_entanglement_link_nums = [node.entanglement_link_nums[i] for i in left_neighbors]
                    if not any(left_entanglement_link_nums):
                        node.create_link(time, direct_left_node)
                        entanglement_ondemand.append((direct_left, node.label))

                # otherwise the node is in the middle of the route
                else:
                    left_entanglement_link_nums = [node.entanglement_link_nums[i] for i in left_neighbors]
                    right_entanglement_link_nums = [node.entanglement_link_nums[i] for i in right_neighbors]

                    # if there is no entanglement link between it and its left neighbors, create link with direct left neighbor on demand
                    if not any(left_entanglement_link_nums):
                        node.create_link(time, direct_left_node)
                        entanglement_ondemand.append((direct_left, node.label))
                    
                    # if there is no entanglement link between it and its right neighbors, create link with direct right neighbor on demand
                    elif not any(right_entanglement_link_nums):
                        node.create_link(time, direct_right_node)
                        entanglement_ondemand.append((node.label, direct_right))

                    # if both sides have entanglement links, try swapping
                    else:
                        # choose memories with rightmost and leftmost entanglement
                        # find leftmost and rightmost entangled nodes
                        leftmost = n
                        rightmost = n
                        right_reversed = list(reversed(right_neighbors))
                        right_nums_reversed = list(reversed(right_entanglement_link_nums))
                        for i, label in enumerate(left_neighbors):
                            if left_entanglement_link_nums[i] > 0:
                                leftmost = label
                                break
                        for i, label in enumerate(right_reversed):
                            if right_nums_reversed[i] > 0:
                                rightmost = label
                                break
                        assert leftmost != n
                        assert rightmost != n

                        leftmost_node = nodes[leftmost]
                        rightmost_node = nodes[rightmost]

                        left_memory = None
                        right_memory = None
                        for memory in node.memories:
                            if memory.entangled_memory["node"] == leftmost_node:
                                left_memory = memory
                                break
                        for memory in node.memories:
                            if memory.entangled_memory["node"] == rightmost_node:
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

                    # clean left and right neighbors_to_connect information for nodes in current route
                    for node_label in route:
                        nodes[node_label].left_neighbors_to_connect.pop(0)
                        nodes[node_label].right_neighbors_to_connect.pop(0)

                    # record entanglement links generated on demand and reset entanglement_ondemand
                    entanglement_usage_pattern["ondemand"].append(entanglement_ondemand)
                    entanglement_ondemand = []

                    # expire memories
                    origin_node.memo_expire(memory)

                    break

        congestion.append(len(requests_to_serve))

        # check if no more requests
        if len(request_stack) == 0 and len(requests_to_serve) == 0:
            break

        time += 1

    # average latencies (over time) and return
    return [latencies, congestion, request_complete_times, entanglement_usage_pattern]


if __name__ == "__main__":
    # Setup rng
    rng = default_rng(SIM_SEED)

    # Generate network
    if GENERATE_NEW:
        graph_arr = gen_network_json(CONFIG, NET_SIZE, NET_TYPE, SIM_SEED)
    else:
        fh = open(CONFIG)
        topo = json.load(fh)
        graph_arr = np.ndarray(topo["array"])
        assert graph_arr.shape == (NET_SIZE, NET_SIZE)
    nodes = []
    for i in range(NET_SIZE):
        node = Node(i, MEMO_SIZE, MEMO_LIFETIME,
                    ENTANGLEMENT_GEN_PROB, ENTANGLEMENT_SWAP_PROB, ADAPT_WEIGHT, i)
        nodes.append(node)
    for i in range(NET_SIZE):
        node = nodes[i]
        neighbors = [nodes[j] for j, element in enumerate(graph_arr[i]) if element != 0]
        node.set_neighbors(neighbors)
        node.entanglement_link_nums = {n: 0 for n in range(NET_SIZE)}

    # Generate traffic matrix
    traffic_mtx = gen_traffic_mtx(NET_SIZE, rng)

    for trial in range(NUM_TRIALS):
        # Generate request node pair queue
        pair_queue = gen_pair_queue(traffic_mtx, NET_SIZE, QUEUE_LEN, rng, rng)
        # Generate request submission time list with constant interval
        time_list = gen_request_time_list(QUEUE_START, QUEUE_LEN, interval=QUEUE_INT)
        # Generate request stack
        request_stack = [Request(time, pair) for time, pair in zip(time_list, pair_queue)]

        # Run simulation
        latencies, congestion, request_complete_times, entanglement_usage_pattern =\
            run_simulation(graph_arr, nodes, request_stack, END_TIME)
        print(latencies)

