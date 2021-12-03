from abc import ABC
from networkx import Graph, shortest_path


class GenerationProtocol(ABC):
    """Class representing protocol to generate entanglement links.

    Attributes:
        node (Node): node hosting the protocol instance.
        prob_dist (Dict[int, float]): probability distribution to select direct neighbors to generate entanglement.
    """

    def __init__(self, node):
        """Constructor of entanglement generation protocol instance.

        Args:
            node (Node): node hosting the protocol instance.
        """
        self.node = node
        self.prob_dist = {}

    def update_dist(self, links_available, links_used):
        pass

    def choose_link(self):
        """Method to choose a link to attempt entanglement.

        Returns:
            int: label of node chosen for entanglement
        """

        choices = list(self.prob_dist.keys())
        probs = list(self.prob_dist.values())
        return self.node.rng.choice(choices, p=probs)


class UniformGenerationProtocol(GenerationProtocol):
    """Class representing protocol to generate entanglement links.

    This protocol has probabilities following a uniform distribution.
    """

    def __init__(self, node):
        """Constructor of entanglement generation protocol instance.

        Args:
            node (Node): host node.
        """

        super().__init__(node)
        prob = 1 / len(node.other_nodes)
        self.prob_dist = {n.label: prob for n in node.other_nodes}


class ExponentialGenerationProtocol(GenerationProtocol):
    """Class representing protocol to generate entanglement links.

    This protocol has probabilities following an exponential distribution, with closer nodes more likely.
    """

    def __init__(self, node, network):
        """Constructor of entanglement generation protocol instance.

        Args:
            node (Node): host node.
            network (np.ndarray): adjacency array for the network.
        """

        super().__init__(node)
        G = Graph(network)
        self.prob_dist = {n.label: 1 / len(shortest_path(G, node.label, n.label)) for n in node.other_nodes}
        total = sum(self.prob_dist.values())
        for label in self.prob_dist:
            self.prob_dist[label] /= total


class AdaptiveGenerationProtocol(GenerationProtocol):
    """Class representing protocol to generate entanglement links.

    This protocol will update the probabilities adaptively based on network traffic.
    """

    def __init__(self, node, adapt_param, neighbors):
        """Constructor of entanglement generation protocol instance.

        Args:
            node (Node): node hosting the protocol instance.
            adapt_param (float): sets alpha parameter for adaptive update of probabilities.
            neighbors (List[int]): list of labels for neighboring nodes.
        """

        super().__init__(node)
        self.alpha = adapt_param
        self.neighbors = neighbors

        init_prob = 1/len(neighbors)
        self.prob_dist = {neighbor: init_prob for neighbor in neighbors}

    def update_dist(self, links_available, links_used):
        """Method to update the probability distribution adaptively.

        Called when a request is sent to the network.

        Args:
            links_available (List[int]): entanglement links available before the request is submitted.
            links_used (List[int]): entanglement links used to complete the request.
        """

        avail = set(links_available) & set(self.neighbors)
        used = set(links_used) & set(self.neighbors)

        S = avail & used
        T = used - avail
        not_used = set(self.neighbors) - used

        # increase probability for links in T
        if len(T) > 0:
            sum_st = sum([self.prob_dist[i] for i in (S | T)])
            new_prob_increase = (self.alpha/len(T)) * (1 - sum_st)
            for t in T:
                self.prob_dist[t] += new_prob_increase

        # decrease probability for links not in T or S
        if len(not_used) > 0:
            sum_st_new = sum([self.prob_dist[i] for i in used])
            new_prob = (1 - sum_st_new) / len(not_used)
            for i in not_used:
                self.prob_dist[i] = new_prob


class Request:
    """Class representing single requests for generating entanglement between two nodes.

    Attributes:
        submit_time (int): time to submit the request
        start_time (int): time when the network starts to serve the request
        pair (Tuple[int, int]): keeps track of labels of origin and destination nodes of the request
        route (List[int]): route of nodes for entanglement connection to complete the request
    """

    def __init__(self, submit_time, pair):
        """Constructor of a request instance.

        Args:
            submit_time (int): time to submit the request
            pair (Tuple[int, int]): keeps track of labels of origin and destination nodes of the request
        """

        self.submit_time = submit_time
        self.start_time = submit_time # start time is no earlier than submit time
        self.pair = pair
        self.route = None

    def get_path(self, network, nodes):
        """Get optimal path to service request.

        Uses local best effort algorithm based on number of existing entanglement links.

        Args:
            network (numpy.ndarray): Adjacency matrix for the network.
            nodes (List[Node]): List of node objects for the network, contains current entanglement info.

        Returns:
            List[int]: Optimal path as list of node labels.
        """

        G = Graph(network)
        end = self.pair[1]
        u_curr = self.pair[0]
        path = [u_curr]

        while u_curr != end:
            node = nodes[u_curr]
            virtual_neighbors = [n for n, count in node.entanglement_link_nums.items() if count > 1]
            if len(virtual_neighbors) == 0:
                u = shortest_path(G, u_curr, end)[1]
            else:
                distances = [len(shortest_path(G, v, end)) - 1 for v in virtual_neighbors]
                minimum_distance = min(distances)

                u = virtual_neighbors[distances.index(minimum_distance)]
                if len(shortest_path(G, u_curr, end)) <= len(shortest_path(G, u, end)):
                    u = shortest_path(G, u_curr, end)[1]

            path.append(u)
            u_curr = u

        return path
