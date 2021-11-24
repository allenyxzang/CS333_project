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
