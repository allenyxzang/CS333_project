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
            # request in form of dict, key is the number of origin and value is the number of destination
            queue.append({rand_row: rand_col})
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
        entanglement_links (List[int]): collection of established entanglement links with direct neighbors
    """

    def __init__(self, label, neighbors, memo_size, lifetime,
                 gen_success_prob, swap_success_prob, adapt_param, seed=0):
        self.label = label
        self.neighbors = neighbors
        self.memo_size = memo_size
        self.memories = []
        self.entanglement_links = []

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
        self.create_link(neighbor_label)

    def create_link(self, other_label):
        if self.rng.random() < self.gen_success_prob and self.memo_reserve():
            self.entanglement_links.append(other_label)


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
        self.entanglement = None

    def entangle(self, memory):
        self.entanglement = memory  # assuming only bipartite entanglement

    def set_owner(self, node):
        self.owner = node

    def reserve(self):
        if not self.reserved:
            self.reserved = True
        else:
            raise Exception("This memory has already been reserved")


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

        # increase probability for links in T
        sum_st = sum([self.prob_dist[i] for i in (S | T)])
        for t in T:
            self.prob_dist[t] += (self.alpha/len(T)) * (1 - sum_st)

        # decrease probability for links not in T or S
        sum_st_new = sum([self.prob_dist[i] for i in (S | T)])
        for neighbor in self.node.neighbors:
            self.prob_dist[neighbor.label] = 1/(len(self.node.neighbors) - len(S | T)) * (1 - sum_st_new)

    def choose_link(self):
        """Method to choose a link to attempt entanglement.

        Returns:
            int: label of node chosen for entanglement
        """

        return self.node.rng.random_choice(self.prob_dist.keys(), self.prob_dist.values())


# TODO: network topology, etc.
