from time import time

import numpy as np
from matplotlib import pyplot as plt
import networkx as nx

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
MEMO_SIZE = 5
MEMO_LIFETIME = 1000  # in units of simulation time step
ENTANGLEMENT_GEN_PROB = 0.01
ENTANGLEMENT_SWAP_PROB = 1
ADAPT_WEIGHT = 0.05

# Simulation parameters
SIM_SEED = 0
END_TIME = 20000
NUM_TRIALS = 50
QUEUE_LEN = 40
QUEUE_START = 10
QUEUE_INT = 500


def run_simulation(graph_arr, nodes, request_stack, end_time):
    time = 0

    # metrics
    latencies = []  # keep track of latencies for each request to get completed
    serve_times = []  # keep track of times to serve each request
    congestion = []  # keep track of number of incomplete requests at the end of each time step
    request_complete_times = []  # keep track of when each request is completed
    entanglement_usage_pattern = {"available": [], "ondemand": []}  # keep track of entanglement usage pattern for every request

    requests_to_serve = []  # keep track of incomplete requests, in case new request comes in before previous request is completed
    entanglement_available = []  # keep track of entanglement links from route nodes when a request is submitted
    entanglement_ondemand = []  # keep track of entanglement links generated on demand to complete a request

    # track current request and related info
    next_request_to_submit = request_stack.pop(0)
    current_request = None
    origin_node = None
    destination_node = None
    route = []

    while time < end_time:
        # check if memories expired
        for node in nodes:
            for memory in node.memories:
                expire_time = memory.entangled_memory["expire_time"]
                if expire_time is not None and expire_time <= time:
                    node.memo_expire(memory)

        # determine if a new request is submitted to the network
        if time == next_request_to_submit.submit_time:
            # submit request
            requests_to_serve.append(next_request_to_submit)

            # find path and assign to route attribute
            new_route = next_request_to_submit.get_path(graph_arr, nodes)
            next_request_to_submit.route = new_route

            # assign as current request if there is none
            if current_request is None:
                current_request = next_request_to_submit
                route = new_route
                origin_node = nodes[route[0]]
                destination_node = nodes[route[-1]]

            # get new request
            if len(request_stack) > 0:
                next_request_to_submit = request_stack.pop(0)

            # update node information on other nodes in path
            # adaptively update probability distribution when a request is submitted to the network
            for i, label in enumerate(new_route):
                node = nodes[label]

                left_neighbors_to_connect = new_route[:i]
                right_neighbors_to_connect = new_route[i+1:]
                nodes[label].left_neighbors_to_connect.append(left_neighbors_to_connect)
                nodes[label].right_neighbors_to_connect.append(right_neighbors_to_connect)

                links_available = []
                links_used = []

                # get current links
                for other_label, count in node.entanglement_link_nums.items():
                    # determine if entanglement links are available
                    if count > 0:
                        links_available.append(other_label)
                        # entanglement links available for nodes in the route for this request
                        links = [(label, other_label)] * count
                        entanglement_available.extend(links)
                # get links used for request
                if i > 0:
                    links_used.append(new_route[i-1])
                if i < (len(new_route) - 1):
                    links_used.append(new_route[i+1])

                # record entanglement links available (stemming from nodes in route) and reset entanglement_available
                entanglement_usage_pattern["available"].append(entanglement_available)
                entanglement_available = []

                node.generation_protocol.update_dist(links_available, links_used)

        # call function to run node (entanglement generation) protocol
        for node in nodes:
            n = node.label

            if n not in route:
                node.create_random_link(time)

            else:
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
                    right_entanglement_link_nums = [node.entanglement_link_nums[i] for i in right_neighbors]
                    # if no entanglement link with right neighbors, create link with direct right neighbor on demand
                    if not any(right_entanglement_link_nums):
                        node.create_link_with_priority(time, direct_right_node)
                        entanglement_ondemand.append((node.label, direct_right))

                # determine if the node is the destination node of the route
                elif node is destination_node:
                    left_entanglement_link_nums = [node.entanglement_link_nums[i] for i in left_neighbors]
                    # if no entanglement link with left neighbors, create link with direct left neighbor on demand
                    if not any(left_entanglement_link_nums):
                        node.create_link_with_priority(time, direct_left_node)
                        entanglement_ondemand.append((direct_left, node.label))

                # otherwise the node is in the middle of the route
                else:
                    left_entanglement_link_nums = [node.entanglement_link_nums[i] for i in left_neighbors]
                    right_entanglement_link_nums = [node.entanglement_link_nums[i] for i in right_neighbors]

                    # if no entanglement link with left neighbors, create link with direct left neighbor on demand
                    if not any(left_entanglement_link_nums):
                        node.create_link_with_priority(time, direct_left_node)
                        entanglement_ondemand.append((direct_left, node.label))

                    # if no entanglement link with right neighbors, create link with direct right neighbor on demand
                    elif not any(right_entanglement_link_nums):
                        node.create_link_with_priority(time, direct_right_node)
                        entanglement_ondemand.append((node.label, direct_right))

                    # if both sides have entanglement links, try swapping
                    else:
                        # choose memories with rightmost and leftmost entanglement
                        # find leftmost and rightmost entangled nodes
                        right_reversed = list(reversed(right_neighbors))
                        right_nums_reversed = list(reversed(right_entanglement_link_nums))
                        leftmost = next((label for num, label in zip(left_entanglement_link_nums, left_neighbors)
                                         if num > 0), n)
                        rightmost = next((label for num, label in zip(right_nums_reversed, right_reversed)
                                          if num > 0), n)
                        assert leftmost != n
                        assert rightmost != n

                        leftmost_node = nodes[leftmost]
                        rightmost_node = nodes[rightmost]

                        left_memory = next((mem for mem in node.memories
                                            if mem.entangled_memory["node"] == leftmost_node), None)
                        right_memory = next((mem for mem in node.memories
                                             if mem.entangled_memory["node"] == rightmost_node), None)

                        node.swap(left_memory, right_memory)

        # determine if the desired entanglement is established
        if current_request is not None:
            for memory in origin_node.memories:
                # check if we have memory entangled with destination
                if memory.entangled_memory["node"] == destination_node:
                    # record latency and completion time
                    latency = time - current_request.submit_time
                    serve_time = time - current_request.start_time
                    latencies.append(latency)
                    serve_times.append(serve_time)
                    request_complete_times.append(time)
                    # record entanglement links generated on demand and reset entanglement_ondemand
                    entanglement_usage_pattern["ondemand"].append(entanglement_ondemand)
                    entanglement_ondemand = []

                    # clean left and right neighbors_to_connect information for nodes in current route
                    for node_label in route:
                        nodes[node_label].left_neighbors_to_connect.pop(0)
                        nodes[node_label].right_neighbors_to_connect.pop(0)
                    # expire memories
                    origin_node.memo_expire(memory)

                    requests_to_serve.pop(0)
                    # if waiting on any requests to serve, they will start at next time step
                    if len(requests_to_serve) > 0:
                        current_request = requests_to_serve[0]
                        current_request.start_time = time + 1
                        route = current_request.route
                        origin_node = nodes[route[0]]
                        destination_node = nodes[route[-1]]
                    else:
                        current_request = None
                        route = []
                        origin_node = None
                        destination_node = None

                    break

        congestion.append(len(requests_to_serve))

        # check if no more requests
        if len(request_stack) == 0 and len(requests_to_serve) == 0:
            break

        time += 1

    # average latencies (over time) and return
    return [latencies, serve_times, congestion, request_complete_times, entanglement_usage_pattern]


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
    G = nx.Graph(graph_arr)
    nx.draw_networkx(G)
    plt.show()

    # Generate nodes
    nodes = [Node(i, MEMO_SIZE, MEMO_LIFETIME, ENTANGLEMENT_GEN_PROB, ENTANGLEMENT_SWAP_PROB, seed=i)
             for i in range(NET_SIZE)]
    for node in nodes:
        other_nodes = nodes[:]
        other_nodes.remove(node)
        node.set_other_nodes(other_nodes)
        node.set_generation_protocol("adaptive", ADAPT_WEIGHT, graph_arr)

    # Generate traffic matrix
    traffic_mtx = gen_traffic_mtx(NET_SIZE, rng)

    latencies_list = []
    serve_times_list = []

    tick = time()
    for trial in range(NUM_TRIALS):
        # Generate request node pair queue
        # pair_queue = gen_pair_queue(traffic_mtx, NET_SIZE, QUEUE_LEN, rng, rng)
        pair_queue = [(9, 6) for i in range(QUEUE_LEN)]  # a queue of identical requests
        # Generate request submission time list with constant interval
        time_list = gen_request_time_list(QUEUE_START, QUEUE_LEN, interval=QUEUE_INT)
        # Generate request stack
        request_stack = [Request(time, pair) for time, pair in zip(time_list, pair_queue)]

        # Run simulation
        latencies, serve_times, congestion, request_complete_times, entanglement_usage_pattern =\
            run_simulation(graph_arr, nodes, request_stack, END_TIME)
        # print(latencies)
        latencies_list.append(latencies)
        serve_times_list.append(serve_times)
    sim_time = time() - tick
    print("Total simulation time: ", sim_time)
    print("Average time per trial: ", sim_time / NUM_TRIALS)

    num_latencies = min([len(latencies_list[i]) for i in range(NUM_TRIALS)])
    num_serve_times = min([len(serve_times_list[i]) for i in range(NUM_TRIALS)])
    latencies_avg = np.zeros(num_latencies)
    serve_times_avg = np.zeros(num_serve_times)

    for i in range(NUM_TRIALS):
        latencies_avg += np.array(latencies_list[i][:num_latencies])

    for i in range(NUM_TRIALS):
        serve_times_avg += np.array(serve_times_list[i][:num_latencies])

    # construct error
    low_percentile = np.zeros(num_latencies)
    high_percentile = np.zeros(num_latencies)
    low_percentile_serve = np.zeros(num_latencies)
    high_percentile_serve = np.zeros(num_latencies)
    for i in range(num_latencies):
        low_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 0.05)
        high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 0.95)
        low_percentile_serve[i] = np.percentile([ll[i] for ll in serve_times_list], 0.05)
        high_percentile_serve[i] = np.percentile([ll[i] for ll in serve_times_list], 0.95)

    latencies_avg = latencies_avg / NUM_TRIALS
    serve_times_avg = serve_times_avg / NUM_TRIALS
            
    # visualization
    requests_latencies = np.arange(num_latencies)
    requests_serve_times = np.arange(num_serve_times)
        
    ax1 = plt.subplot(121)
    ax1.plot(requests_latencies, latencies_avg)
    ax1.set_title("average request latencies")
    ax1.fill_between(requests_latencies, high_percentile, low_percentile, alpha=0.4)
    
    ax2 = plt.subplot(122)
    ax2.plot(requests_serve_times, serve_times_avg)
    ax2.set_title("average times to serve requests")
    ax2.fill_between(requests_serve_times, high_percentile_serve, low_percentile_serve, alpha=0.4)

    plt.show()
