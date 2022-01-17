import json
import numpy as np

import networkx as nx
from matplotlib import pyplot as plt

network_file = "network.json"
draw_kwargs = {"node_size": 1000,
               "font_color": "white",
               "font_size": 20}

fh = open(network_file)
topo = json.load(fh)
graph_arr = np.array(topo["array"])

G = nx.Graph(graph_arr)
pos = nx.spring_layout(G)

plt.figure(figsize=(5, 4), tight_layout=True)
nx.draw_networkx(G, pos, **draw_kwargs)
plt.axis('off')
plt.savefig("network.png")
plt.show()
