import json
import networkx as nx
import numpy as np
from numpy.random import default_rng


# TODO: network topology in JSON
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

    fh = open(filename)
    topo = {"array": arr}
    json.dump(topo, fh)
    return arr


# generator of traffic matrix 
def gen_traffic_mtx(node_num, rng):
    mtx = rng.random.rand(node_num, node_num)
    for i in range(node_num):
        mtx[i, i] = 0  # no self-to-self traffic

    return mtx


# generator of request queue
def gen_request_queue(traffic_mtx, node_num, queue_len, rng_mtx, rng_judge):
    queue = []
    idx = 0
    while idx < queue_len:
        # random selection of traffic matrix element for judgement
        rand_row = rng_mtx.random.randint(node_num)
        rand_col = rng_mtx.random.randint(node_num)

        if rng_judge.random() < traffic_mtx[rand_row, rand_col]:
            # request in form of two-element tuple
            # first element is the label of the origin node, and second element is the label of the destination
            queue.append((rand_row, rand_col))
            idx += 1
    
    return queue


class Node:
    """Class of network nodes.

    Hold quantum memories, information of total network topology (global variable) and nearest neighbor entanglement.
    Carry continuous entanglement generation, adaptive update, and path finding protocols.

    Attributes:
        label (int): integer to label the node, corresponding to the indices of traffic matrix and requests
        neighbors (List[Node]): list of neighboring nodes
        memo_size (int): number of quantum memories in the node, assuming memories are of the same type
        lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store entanglement
        entanglement_link_nums (Dict[int, int]): keeps track of numbers of entanglement links with direct neighbors (for path finding alg.)
    """

    def __init__(self, label, neighbors, memo_size, lifetime,
                 gen_success_prob, swap_success_prob, adapt_param, seed=0):
        self.label = label
        self.neighbors = neighbors
        self.memo_size = memo_size
        self.memories = []
        self.entanglement_link_nums = {n.label: 0 for n in neighbors}

        # create memories
        for i in range(memo_size):
            memory = Memory("Node" + str(self.label) + "[%d]" % i, lifetime)
            self.memories.append(memory)

        # create protocol
        self.generation_protocol = GenerationProtocol(self, adapt_param)

        # create rng and store params
        self.rng = default_rng(seed)
        self.gen_success_prob = gen_success_prob
        self.swap_success_prob = swap_success_prob

    def memo_reserve(self):
        """Method for entanglement generation and swapping protocol to invoke to reserve quantum memories.

        Returns:
            bool: if there was an available memory to reserve.
        """
        
        idx = 0
        while idx < len(self.memories):
            if self.memories[idx].reserved:
                idx += 1
            else:
                self.memories[idx].reserve()
                return True

        if idx == len(self.memories):
            return False

    def create_random_link(self):
        neighbor_label = self.generation_protocol.choose_link()
        neighbor = next((n for n in self.neighbors if n.label == neighbor_label), None)
        self.create_link(neighbor)

    def create_link(self, other_node):
        if self.rng.random() < self.gen_success_prob:
            raise NotImplementedError

    @staticmethod
    def swap(memory1, memory2):
        """Method to do entanglement swapping. 
        
        Will reset the two involved memories' entanglement state. 
        Will modify entanglement state of original entangled parties of memory1 and memory2.
        Does not modify start_time, and expiration of entanglement is determined by the first memory expiration
        """

        memo1 = memory1.entangled_memory["memo"].entangled_memory["memo"]
        memo2 = memory2.entangled_memory["memo"].entangled_memory["memo"]
        node1 = memory1.entangled_memory["memo"].entangled_memory["node"]
        node2 = memory2.entangled_memory["memo"].entangled_memory["node"]

        # entanglement connection
        memory1.entangled_memory["memo"].entangled_memory["node"] = node2
        memory2.entangled_memory["memo"].entangled_memory["node"] = node1
        memory1.entangled_memory["memo"].entangled_memory["memo"] = memo2
        memory2.entangled_memory["memo"].entangled_memory["memo"] = memo1

        # entanglement reset
        memory1.expire()
        memory2.expire()


class Memory:
    """Simplified class of quantum memories to be stored in a node.

    Omitting details of memory efficiency, quantum state fidelity, photon wavelength, memory maximal frequency of reuse, etc.

    Attributes:
        name (str): name of a memory array instance
        lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store quantum entanglement
    """

    def __init__(self, name, lifetime):
        """Constructor of memory instance.

        Args:
            name: name of memory instance
            lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store quantum entanglement
        """

        self.name = name
        self.owner = None
        self.lifetime = lifetime
        self.reserved = False  # Boolean representing if the memory has been reserved for use
        self.entangled_memory = {"node": None, "memo": None, "start_time": None}

    def entangle(self, memory, time):
        self.entangled_memory = {"node": memory.owner, "memo": memory, "start_time": time}

    def set_owner(self, node):
        self.owner = node

    def reserve(self):
        if not self.reserved:
            self.reserved = True
        else:
            raise Exception("This memory has already been reserved")

    def expire(self):
        self.entangled_memory = {"node": None, "memo": None, "start_time": None}


class GenerationProtocol:
    """Class representing protocol to generate entanglement links.

    Attributes:
        node (Node):
        alpha (float):
        prob_dist (Dict[int, float]): probability distribution to select direct neighbors to generate entanglement.
    """

    def __init__(self, node, adapt_param):
        """

        Args:
            node (Node):
            adapt_param (float):
        """
        self.node = node
        self.alpha = adapt_param

        init_prob = 1/len(node.neighbors)
        self.prob_dist = {}
        for neighbor in node.neighbors:
            self.prob_dist[neighbor.label] = init_prob

    def update_dist(self, links_available, links_used):
        """Method to update the probability distribution adaptively.

        Called when a request is sent to the network.

        Args:
            links_available (List[int]): entanglement links available before the request is submitted.
            links_used (List[int]): entanglement links used to complete the request request.
        """

        avail = set(links_available)
        used = set(links_used)

        S = avail & used
        T = used - avail
        not_used = set([n.label for n in self.node.neighbors]) - used

        # increase probability for links in T
        sum_st = sum([self.prob_dist[i] for i in (S | T)])
        new_prob_increase = (self.alpha/len(T)) * (1 - sum_st)
        for t in T:
            self.prob_dist[t] += new_prob_increase

        # decrease probability for links not in T or S
        sum_st_new = sum([self.prob_dist[i] for i in used])
        new_prob = (1 - sum_st_new) / len(not_used)
        for i in not_used:
            self.prob_dist[i] = new_prob

    def choose_link(self):
        """Method to choose a link to attempt entanglement.

        Returns:
            int: label of node chosen for entanglement
        """

        return self.node.rng.choice(self.prob_dist.keys(), self.prob_dist.values())


class RequestStack:
    """Class of the request stack to be served.

    The sequence of feeding requests into the network is determined by the request time list.

    Attributes:
        time_list (List[int]): list of times to submit individual requests
        request_queue (List[Tuple[int,int]]): queue of requests for generating entanglement between two nodes
        requests (List[Request]): list of request instances in order of start time
    """

    def __init__(self, time_list, request_queue):
        """Constructor of request stack instance.

        Args:
            time_list (List[int]): list of times to submit individual requests
            request_queue (List[Tuple[int,int]]): queue of requests for generating entanglement between two nodes
        """
        
        assert len(time_list) == len(request_queue), "Time list and request queue shapes incompatible."
        self.time_list = time_list
        self.request_queue = request_queue
        self.requests = []

        for i in range(len(time_list)):
            start_time = self.time_list[i]
            pair = self.request_queue[i]
            request = Request(start_time, pair)
            self.requests.append(request)

    def pop(self):
        """Method to remove the submitted request from the stack.
        
        Return most updated request and its request time.
        """

        request_time = self.time_list.pop(0)
        pair = self.request_queue.pop(0)
        request = self.requests.pop(0)

        return request_time, pair, request


class Request:
    """Class representing single requests for generating entanglement between two nodes.

    Attributes:
        start_time (int): time to submit the request
        pair (Tuple[int, int]): keeps track of labels of origin and destination nodes of the request
        completed (Bool): Boolean to keep track if the request has been completed
    """

    def __init__(self, start_time, pair):
        """Constructor of a request instance.

        Args:
            start_time (int): time to submit the request
            pair (Tuple[int, int]): keeps track of labels of origin and destination nodes of the request
        """

        self.start_time = start_time
        self.pair = pair
        self.completed = False

    def get_path(self, network, nodes):
        """Get optimal path to service request.

        Uses greedy algorithm based on number of existing entanglement links.

        Args:
            network (numpy.ndarray): Adjacency matrix for the network.
            nodes (List[Node]): List of node objects for the network, contains current entanglement info.

        Returns:
            List[int]: Optimal path as list of node labels.
        """

        raise NotImplementedError

# TODO: request methods

# TODO: network topology, etc.
