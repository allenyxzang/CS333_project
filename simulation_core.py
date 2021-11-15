import numpy as np
from numpy.random import Generator
import math

# global simulation parameters
MEMO_SIZE = 1
MEMO_LIFETIME = 100 # in unit of simulation time step
ENTANGLEMENT_GEN_PROB = 0.01
ENTANGLEMENT_SWAP_PROB = 1

# network topology in JSON

# generator of traffic matrix 
def gen_traffic_mtx(node_num, rng):
    mtx = rng.random.rand(node_num,node_num)
    for i in range(node_num):
        for j in range(node_num):
            if i == j:
                mtx[i, j] = 0 # no self-to-self traffic

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
            queue.append({rand_row: rand_col}) # request in form of dict, key is the number of origin and value is the number of destination
            idx += 1
    
    return queue


class Node():
    """Class of network nodes.

    Hold quantum memories, information of total network topology (global variable) and nearest neighbor entanglement.
    Carry continuous entanglement generation, adaptive update, and path finding protocols.

    Attributes:
        label (int): integer to label the node, corresponding to the indices of traffic matrix and requests
        memo_size (int): number of quantum memories in the node, assuming memories are of the same type
        lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store quantum entanglement
        prob_dist (Dict[int, float]): probability distribution to select direct neighbors to generate entanglement
        entanglement_links (List): collection of established entanglement links with direct neighbors
    """

    def __init__(self, label, memo_size, lifetime):
        self.label = label
        self.memo_size = memo_size
        self.memories = []
        self.prob_dist = {}
        self.entanglement_links = []

        for i in range(memo_size):
            memory = Memory("Node" + str(self.label) + "[%d]" % i, lifetime)
            self.memories.append(memory)
        
    def prob_dist_update(self, new_prob_dist):
        """Method for adaptive protocol to update probabilistic distribution."""

        self.prob_dist = new_prob_dist

    def memo_reserve(self):
        """Method for entanglement generation and swapping protocol to invoke to reserve quantum memories
        
        Args:
            num (int): number of memories to be reserved
        """
        
        idx = 0
        while idx < len(self.memories):
            if self.memories[idx].reserved == True:
                idx +=1
            else:
                self.memories[idx].reserve()
                break
            

class Memory():
    """Simplified class of quantum memories to be stored in a node.

    Omitting details of memory efficiency, quantum state fidelity, photon wavelength, memory maximal frequency of reuse, etc.

    Attributes:
        name (str): name of a memory array instance
        lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store quantum entanglement
    """

    def __init__(self, name, lifetime):
        """Constructor of memoryinstance.

        Args:
            name: name of memory instance
            lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store quantum entanglement
        """

        self.name = name
        self.owner = None
        self.lifetime = lifetime
        self.reserved = False # Boolean representing if the memory has been reserved for use
        self.entanglement = None

    def entangle(self, memory):
        self.entanglement = memory # assuming only bipartite entanglement

    def set_owner(self, node):
        self.owner = node

    def reserve(self):
        if self.reserved == False:
            self.reserved = True
        else:
            raise Exception("This memory has already been reserved")
    
# TODO: protocol interface, network topology, etc.