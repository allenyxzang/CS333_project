from abc import ABC
from networkx import Graph, dijkstra_path


class GenerationProtocol(ABC):
    """Class representing protocol to generate entanglement links.

    Attributes:
        node (Node): node hosting the protocol instance.
        alpha (float): parameter used for certain protocols.
        prob_dist (Dict[int, float]): probability distribution to select direct neighbors to generate entanglement.
    """

    def __init__(self, node, adapt_param):
        """Constructor of entanglement generation protocol instance.

        Args:
            node (Node): node hosting the protocol instance.
            adapt_param (float): sets alpha parameter.
        """
        self.node = node
        self.alpha = adapt_param
        self.prob_dist = {}


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

        super().__init__(node, adapt_param)
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

        avail = set(links_available)
        used = set(links_used)

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

    def choose_link(self):
        """Method to choose a link to attempt entanglement.

        Returns:
            int: label of node chosen for entanglement
        """

        choices = list(self.prob_dist.keys())
        probs = list(self.prob_dist.values())
        return self.node.rng.choice(choices, p=probs)


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

        Uses greedy algorithm based on number of existing entanglement links.

        Args:
            network (numpy.ndarray): Adjacency matrix for the network.
            nodes (List[Node]): List of node objects for the network, contains current entanglement info.

        Returns:
            List[int]: Optimal path as list of node labels.
        """

        graph = Graph(network)
        path = dijkstra_path(graph, self.pair[0], self.pair[1])
        return path
