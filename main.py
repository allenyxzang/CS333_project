from time import time

import numpy as np
from matplotlib import pyplot as plt
import networkx as nx

from simulation_core import *
from hardware import *
from protocols import *

# Network parameters
CONFIG = "network_customized.json"
GENERATE_NEW_NET = False
TRAFFIC_MATRIX = "traffic_matrix.json"
GENERATE_NEW_TRAFFIC = False
RANDOM_REQUESTS = True
NET_SIZE = 8
NET_TYPE = "as_net"
CONTINUOUS_SCHEME = "adaptive"

# Node parameters
MEMO_SIZE = 5  # default memory number per node
MEMO_LIFETIME = 1000  # in units of simulation time step
ENTANGLEMENT_GEN_PROB = 0.01
ENTANGLEMENT_SWAP_PROB = 1
ADAPT_WEIGHT = 0.05

# Simulation parameters
SIM_SEED = 0
END_TIME = 40000
NUM_TRIALS = 10
QUEUE_LEN = 200
QUEUE_INT = 200
QUEUE_START = QUEUE_INT


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
                        # avoid repetitive counting
                        if other_label not in left_neighbors_to_connect:
                            links = [(label, other_label)] * count
                            entanglement_available.extend(links)
                # get links used for request
                if i > 0:
                    links_used.append(new_route[i-1])
                if i < (len(new_route) - 1):
                    links_used.append(new_route[i+1])
                node.generation_protocol.update_dist(links_available, links_used)

            # record entanglement links available (stemming from nodes in route) and reset entanglement_available
            entanglement_usage_pattern["available"].append(entanglement_available)
            entanglement_available = []

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
                    latency = int(time - current_request.submit_time)
                    serve_time = int(time - current_request.start_time)
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
    default_memos = [MEMO_SIZE] * NET_SIZE
    if GENERATE_NEW_NET:
        graph_arr = gen_network_json(CONFIG, NET_SIZE, NET_TYPE, SIM_SEED)
        memo_sizes = default_memos
    else:
        fh = open(CONFIG)
        topo = json.load(fh)
        graph_arr = np.array(topo["array"])
        memo_sizes = np.array(topo.get("memo_sizes", default_memos))
        assert graph_arr.shape == (NET_SIZE, NET_SIZE)
        assert len(memo_sizes) == NET_SIZE
    G = nx.Graph(graph_arr)
    pos = nx.spring_layout(G)
    nx.draw_networkx(G, pos)
    plt.show()

    # Generate traffic matrix
    if GENERATE_NEW_TRAFFIC:
        traffic_mtx = gen_traffic_mtx(NET_SIZE, rng)
    else:
        tm = open(TRAFFIC_MATRIX)
        tm_json = json.load(tm)
        traffic_mtx = np.array(tm_json["matrix"])

    latencies_list = []
    serve_times_list = []
    usage_pattern_list = []

    tick = time()
    for trial in range(NUM_TRIALS):
        # set nodes
        seed_start = NET_SIZE * trial
        nodes = [Node(i, memo_size, MEMO_LIFETIME, ENTANGLEMENT_GEN_PROB, ENTANGLEMENT_SWAP_PROB, graph_arr,
                      seed=seed_start+i)
                 for i, memo_size in enumerate(memo_sizes)]
        for node in nodes:
            other_nodes = nodes[:]
            other_nodes.remove(node)
            node.set_other_nodes(other_nodes)
            node.set_generation_protocol(CONTINUOUS_SCHEME, ADAPT_WEIGHT)

        # Generate request node pair queue
        if RANDOM_REQUESTS:
            pair_queue = gen_pair_queue(traffic_mtx, NET_SIZE, QUEUE_LEN, rng, rng)
        else:
            pair_queue = [(9, 6) for i in range(QUEUE_LEN)]  # a queue of identical requests
        # Generate request submission time list with constant interval
        time_list = gen_request_time_list(QUEUE_START, QUEUE_LEN, interval=QUEUE_INT)
        # Generate request stack
        request_stack = [Request(time, pair) for time, pair in zip(time_list, pair_queue)]

        # Run simulation
        latencies, serve_times, congestion, request_complete_times, entanglement_usage_pattern =\
            run_simulation(graph_arr, nodes, request_stack, END_TIME)
        latencies_list.append(latencies)
        serve_times_list.append(serve_times)
        usage_pattern_list.append(entanglement_usage_pattern)
        print("Finished trial {} of {}".format(trial + 1, NUM_TRIALS))
    
    sim_time = time() - tick
    print("Total simulation time: ", sim_time)
    print("Average time per trial: ", sim_time / NUM_TRIALS)

    num_latencies = min([len(latencies_list[i]) for i in range(NUM_TRIALS)])
    num_serve_times = min([len(serve_times_list[i]) for i in range(NUM_TRIALS)])
    num_requests = min(num_latencies, num_serve_times)  # num_latencies and num_serve_times should be equal in principle
    latencies_avg = np.zeros(num_requests)
    serve_times_avg = np.zeros(num_requests)

    for i in range(NUM_TRIALS):
        latencies_avg += np.array(latencies_list[i][:num_requests])

    for i in range(NUM_TRIALS):
        serve_times_avg += np.array(serve_times_list[i][:num_requests])

    latencies_avg = latencies_avg / NUM_TRIALS
    serve_times_avg = serve_times_avg / NUM_TRIALS

    # construct error
    low_percentile = np.zeros(num_latencies)
    high_percentile = np.zeros(num_latencies)
    low_percentile_serve = np.zeros(num_latencies)
    high_percentile_serve = np.zeros(num_latencies)
    for i in range(num_latencies):
        low_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 5)
        high_percentile[i] = np.percentile([ll[i] for ll in latencies_list], 95)
        low_percentile_serve[i] = np.percentile([ll[i] for ll in serve_times_list], 5)
        high_percentile_serve[i] = np.percentile([ll[i] for ll in serve_times_list], 95)

    # entanglement usage pattern information
    available_patterns = [usage_pattern_list[i]["available"] for i in range(NUM_TRIALS)]
    ondemand_patterns = [usage_pattern_list[i]["ondemand"] for i in range(NUM_TRIALS)]
    available_accum = [[] for i in range(num_requests)]
    ondemand_accum = [[] for i in range(num_requests)]
    for i in range(num_requests):
        for pattern in available_patterns:
            available_accum[i] += pattern[i]
        for pattern in ondemand_patterns:
            ondemand_accum[i] += pattern[i]

    # choose the first, the last and the middle requests' patterns for visualization
    vis_available_patterns = [available_accum[0], available_accum[round(num_requests/2)], available_accum[-1]]
    vis_ondemand_patterns = [ondemand_accum[0], ondemand_accum[round(num_requests/2)], ondemand_accum[-1]]
    vis_available_graphs = []
    vis_ondemand_graphs = []
    for pattern in vis_available_patterns:
        G_vis = nx.Graph(graph_arr)
        nx.set_edge_attributes(G_vis, 0, "available")
        # nx.set_edge_attributes(G_vis, 0, "ondemand")
        for pair in pattern:
            if (pair[0], pair[1]) not in G_vis.edges():
                G_vis.add_edge(pair[0], pair[1], available=1)
            else:
                G_vis[pair[0]][pair[1]]["available"] += 1
        vis_available_graphs.append(G_vis)
        
    for pattern in vis_ondemand_patterns:
        G_vis = nx.Graph(graph_arr)
        # nx.set_edge_attributes(G_vis, 0, "available")
        nx.set_edge_attributes(G_vis, 0, "ondemand")
        for pair in pattern:
            if (pair[0], pair[1]) not in G_vis.edges():
                G_vis.add_edge(pair[0], pair[1], ondemand=1)
            else:
                G_vis[pair[0]][pair[1]]["ondemand"] += 1
        vis_ondemand_graphs.append(G_vis)

    # save data
    filename = "data_" + CONTINUOUS_SCHEME + ".json"
    data = {"latencies": latencies_list,
            "service_times": serve_times_list,
            "average_latencies": latencies_avg.tolist(),
            "average_service_times": serve_times_avg.tolist(),
            "accumulated_available_patterns": available_accum,
            "accumulated_ondemand_patterns": ondemand_accum}
    fh = open(filename, 'w')
    json.dump(data, fh)
            
    # statistics visualization
    requests_latencies = np.arange(num_latencies)
    requests_serve_times = np.arange(num_serve_times)

    fig = plt.figure(figsize=(7, 7))

    ax1 = plt.subplot(211)
    ax1.plot(requests_latencies, latencies_avg)
    ax1.set_title("average request latencies")
    ax1.fill_between(requests_latencies, high_percentile, low_percentile, alpha=0.4)
    
    ax2 = plt.subplot(212)
    ax2.plot(requests_serve_times, serve_times_avg)
    ax2.set_title("average times to serve requests")
    ax2.fill_between(requests_serve_times, high_percentile_serve, low_percentile_serve, alpha=0.4)

    plt.xlabel("request number")
    plt.tight_layout()
    plt.show()

    # patterns visualization on graphs
    for Graph in vis_available_graphs:
        edges = Graph.edges()
        avails = [Graph[u][v]["available"] for u,v in edges]
        nx.draw_networkx_nodes(Graph, pos)
        nx.draw_networkx_labels(Graph, pos)
        edges_drawn = nx.draw_networkx_edges(Graph, pos, edge_color=avails, width=2, edge_cmap=plt.cm.Greens, edge_vmin=0)
        plt.colorbar(edges_drawn)
        plt.axis('off')
        plt.show()
    
    for Graph in vis_ondemand_graphs:
        edges = Graph.edges()
        ondemands = [Graph[u][v]["ondemand"] for u,v in edges]
        nx.draw_networkx_nodes(Graph, pos)
        nx.draw_networkx_labels(Graph, pos)
        edges_drawn = nx.draw_networkx_edges(Graph, pos, edge_color=ondemands, width=2, edge_cmap=plt.cm.Reds, edge_vmin=0)
        plt.colorbar(edges_drawn)
        plt.axis('off')
        plt.show()
