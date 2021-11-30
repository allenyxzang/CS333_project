from numpy.random import default_rng
from protocols import GenerationProtocol


class Node:
    """Class of network nodes.

    Hold quantum memories, information of total network topology (global variable) and nearest neighbor entanglement.
    Carry continuous entanglement generation, adaptive update, and path finding protocols.

    Attributes:
        label (int): integer to label the node, corresponding to the indices of traffic matrix and requests
        neighbors (List[Node]): list of neighboring nodes
        memo_size (int): number of quantum memories in the node, assuming memories are of the same type
        memories (List[Memory]): local memory objects.
        lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store entanglement
        entanglement_link_nums (Dict[int, int]): keeps track of numbers of entanglement links with direct neighbors (for path finding alg.)
        reserved_memories (int): number of memories reserved on the node.
        _next_avail_memory (int): index (in self.memories) of next memory that may be reserved.
        left_neighbors_to_connect (List[List]): list of left neighbors' indices in route for entanglement connection
        right_neighbors_to_connect (List[List]): list of right neighbors' indices in route for entanglement connection
        generation_protocol (GenerationProtocol): entanglement generation protocol attached to the node
    """

    def __init__(self, label, memo_size, lifetime,
                 gen_success_prob, swap_success_prob, adapt_param, seed=0):
        """Constructor of a node instance.

        Args:
            label (int): integer to label the node, corresponding to the indices of traffic matrix and requests
            memo_size (int): number of quantum memories in the node, assuming memories are of the same type
            lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store entanglement
            gen_success_prob (float): success probability of entanglement generation between 0 and 1
            swap_success_prob (float): success probability of entanglement swapping between 0 and 1
            adapt_param (float): parameter for adaptive protocol
            seed: seed for random number generators (default 0)
        """

        self.label = label
        self.neighbors = []
        self.memo_size = memo_size
        self.memories = []
        self.entanglement_link_nums = {}
        self.left_neighbors_to_connect = []
        self.right_neighbors_to_connect = []
        self.adapt_param = adapt_param
        self.generation_protocol = None

        self.reserved_memories = 0
        self._next_avail_memory = 0

        # create memories
        for i in range(memo_size):
            memory = Memory("Node" + str(self.label) + "[%d]" % i, lifetime)
            memory.set_owner(self)
            self.memories.append(memory)

        # create rng and store params
        self.rng = default_rng(seed)
        self.gen_success_prob = gen_success_prob
        self.swap_success_prob = swap_success_prob

    def set_neighbors(self, neighbors):
        self.neighbors = neighbors
        # create protocol
        self.generation_protocol = GenerationProtocol(self, self.adapt_param)

    def memo_reserve(self):
        """Method for entanglement generation and swapping protocol to invoke to reserve quantum memories.

        Returns:
            Memory: memory object reserved (None if there are no free memories).
        """

        if self._next_avail_memory >= self.memo_size:
            return None
        memory = self.memories[self._next_avail_memory]
        memory.reserved = True

        self._next_avail_memory += 1
        while self._next_avail_memory < self.memo_size:
            if not self.memories[self._next_avail_memory].reserved:
                break
            self._next_avail_memory += 1

        return memory

    def memo_free(self, memory):
        """Method to free an occupied memory.

        Args:
            memory (Memory): memory object to free.
        """

        idx = self.memories.index(memory)
        memory.free()
        if idx < self._next_avail_memory:
            self._next_avail_memory = idx

    def memo_expire(self, memory):
        # avoid infinite loop
        if memory is None:
            return 
        if not memory.reserved:
            return

        other_node = memory.entangled_memory["node"]
        self.entanglement_link_nums[other_node.label] -= 1
        memory.expire()
        self.memo_free(memory)

        other_memory = memory.entangled_memory["memo"]
        other_node.memo_expire(other_memory)

    def create_random_link(self, time):
        neighbor_label = self.generation_protocol.choose_link()
        neighbor = next((n for n in self.neighbors if n.label == neighbor_label), None)
        self.create_link(time, neighbor)

    def create_link(self, time, other_node):
        # check if entanglement succeeds
        if self.rng.random() > self.gen_success_prob:
            return

        # reserve a local memory and a memory on the other node to entangle
        # Note: it is possible that when generating entanglement on demand, no memory is available for reservation
        local_memo = self.memo_reserve()
        if local_memo is None:
            return
        other_memo = other_node.memo_reserve()
        if other_memo is None:
            self.memo_free(local_memo)
            return

        # entangle the two nodes
        local_memo.entangle(other_memo, time)

        # record entanglement
        self.entanglement_link_nums[other_node.label] += 1
        # the other node should also update its entanglement link information
        other_node.entanglement_link_nums[self.label] += 1

    def swap(self, memory1, memory2):
        """Method to do entanglement swapping.

        Will reset the two involved memories' entanglement state.
        Will modify entanglement state of original entangled parties of memory1 and memory2.
        Does not modify start_time, and expiration of entanglement is determined by the first memory expiration

        Return the result of swapping (successful or not).
        """

        if not memory1.reserved or not memory2.reserved:
            return

        memo1 = memory1.entangled_memory["memo"]
        memo2 = memory2.entangled_memory["memo"]
        node1 = memory1.entangled_memory["node"]
        node2 = memory2.entangled_memory["node"]

        if self.rng.random() < self.swap_success_prob:
            # entanglement connection
            memo1.entangled_memory["node"] = node2
            memo2.entangled_memory["node"] = node1
            memo1.entangled_memory["memo"] = memo2
            memo2.entangled_memory["memo"] = memo1

            # entanglement reset
            self.memo_expire(memory1)
            self.memo_expire(memory2)

            return True

        else:
            # if unsuccessful, all involved memories entanglement reset
            self.memo_expire(memory1)
            self.memo_expire(memory2)
            node1.memo_expire(memo1)
            node2.memo_expire(memo2)

            return False


class Memory:
    """Simplified class of quantum memories to be stored in a node.

    Omitting details of memory efficiency, quantum state fidelity, photon wavelength, memory maximal frequency of reuse, etc.

    Attributes:
        name (str): name of a memory array instance
        owner (Node): node object which holds this memory.
        lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store quantum entanglement
        reserved (bool): indicates if the memory has been reserved by the owning node.
        entangled_memory (Dict[str, any]): records information on another memory sharing entanglement (if it exists).
    """

    def __init__(self, name, lifetime):
        """Constructor of memory instance.

        Args:
            name (str): name of memory instance
            lifetime (int): quantum memory lifetime in unit of simulation time step, represents time to store quantum entanglement
        """

        self.name = name
        self.owner = None
        self.lifetime = lifetime
        self.reserved = False  # Boolean representing if the memory has been reserved for use

        self.entangled_memory = {"node": None, "memo": None, "expire_time": None}

    def entangle(self, memory, time):
        self.entangled_memory = {"node": memory.owner, "memo": memory, "expire_time": time + self.lifetime}
        # the other memory should also update its entanglement information
        memory.entangled_memory = {"node": self.owner, "memo": self, "expire_time": time + memory.lifetime}

    def set_owner(self, node):
        self.owner = node

    def reserve(self):
        if not self.reserved:
            self.reserved = True
        else:
            raise Exception("This memory has already been reserved")

    def free(self):
        if self.reserved:
            self.reserved = False
        else:
            raise Exception("This memory is not reserved")

    def expire(self):
        self.entangled_memory = {"node": None, "memo": None, "expire_time": None}
