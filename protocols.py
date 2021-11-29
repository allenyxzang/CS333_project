from networkx import Graph, dijkstra_path


class GenerationProtocol:
    """Class representing protocol to generate entanglement links.

    Attributes:
        node (Node):
        alpha (float):
        prob_dist (Dict[int, float]): probability distribution to select direct neighbors to generate entanglement.
    """

    def __init__(self, node, adapt_param):
        """Constructor of entanglement generation protocol instance.

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


class Request:
    """Class representing single requests for generating entanglement between two nodes.

    Attributes:
        start_time (int): time to submit the request
        pair (Tuple[int, int]): keeps track of labels of origin and destination nodes of the request
        route (List[int]): route of nodes for entanglement connection to complete the request
    """

    def __init__(self, start_time, pair):
        """Constructor of a request instance.

        Args:
            start_time (int): time to submit the request
            pair (Tuple[int, int]): keeps track of labels of origin and destination nodes of the request
        """

        self.start_time = start_time
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
