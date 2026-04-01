import json
import matplotlib.pyplot as plt
import networkx as nx
from fa2 import ForceAtlas2
import numpy as np


def load_data(map_file_name, edges_file_name):
    with open(f"{map_file_name}.json") as f:
        map_f = json.load(f)
    with open(f"{edges_file_name}.json") as f:
        e = json.load(f)
    return map_f, e


def build_graph(paper_map_obj, edges_obj):
    G = nx.DiGraph()

    for paper_id, paper in paper_map_obj.items():
        G.add_node(paper_id,
                   title=paper.get("title", "Unknown"),
                   citations=paper.get("citationCount", 0))

    for source, target in edges_obj:
        G.add_edge(source, target)

    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    print(f"Removed {len(isolated)} isolated nodes, {G.number_of_nodes()} remain")

    forceatlas2 = ForceAtlas2(
        outboundAttractionDistribution=True,
        edgeWeightInfluence=1.0,
        jitterTolerance=0.25,
        barnesHutOptimize=False,
        barnesHutTheta=1.2,
        scalingRatio=0.5,
        seed=42,
        gravity=2.5,
        linLogMode=True,
        adjustSizes=True
    )

    G_undirected = G.to_undirected()
    pos = forceatlas2.forceatlas2_networkx_layout(G_undirected, iterations=5000)

    # balanced sizing
    deg_dict = dict(G.in_degree())

    deg = np.array([deg_dict[n] for n in G.nodes()])
    node_sizes = (np.sqrt(deg) * 500) + 80

    # colors
    color_vals = deg

    fig, ax = plt.subplots(figsize=(18, 14))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    nx.draw_networkx_edges(G, pos, ax=ax,
                           edge_color="#2d4a7a",
                           arrows=True,
                           arrowsize=12,
                           arrowstyle='->',
                           width=0.6,
                           alpha=0.5,
                           connectionstyle="arc3,rad=0.1")

    cmap = plt.cm.plasma
    nodes = nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_size=node_sizes,
        node_color=color_vals,
        cmap=cmap,
        alpha=0.95
    )

    nodes.set_edgecolor("white")
    nodes.set_linewidth(0.3)

    # colorbar legend
    sm = plt.cm.ScalarMappable(
        cmap=cmap,
        norm=plt.Normalize(vmin=deg.min(), vmax=deg.max())
    )

    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.3, pad=0.01, aspect=20)
    cbar.set_label("In-Degree Centrality", color="white", fontsize=9)
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white", fontsize=7)
    cbar.outline.set_edgecolor("#444444")

    # label top nodes by degree
    top_nodes = sorted(deg_dict.items(), key=lambda x: x[1], reverse=True)[:25]

    labels = {}
    for n, c in top_nodes:
        t = G.nodes[n]["title"]
        words = t.split()
        line, lines = "", []
        for w in words:
            if len(line + w) > 28:
                lines.append(line.strip())
                line = w + " "
            else:
                line += w + " "
        lines.append(line.strip())
        labels[n] = "\n".join(lines[:3])

    nx.draw_networkx_labels(G, pos, labels, ax=ax,
                            font_size=5.5,
                            font_color="white",
                            font_family="monospace")

    ax.set_title("Avian Same-Sex Behavior\nCitation Network",
                 color="white", fontsize=18, fontweight="bold",
                 pad=15, loc="left", x=0.02)

    ax.text(0.98, 0.02,
            f"{G.number_of_nodes()} papers · {G.number_of_edges()} citations\n"
            f"node size & color = degree\n\n"
            "degree: the number of connections a node has\n\n"
            "In this citation network, it represents how many times a\n"
            "paper is cited (incoming links)",
            transform=ax.transAxes, color="#888888",
            fontsize=7, ha="left", va="bottom", fontfamily="monospace")

    ax.axis("off")
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig("network.png", dpi=200, bbox_inches="tight", facecolor="#0d1117")
    plt.show()
    print("Saved to network.png")


if __name__ == '__main__':
    paper_map, edges = load_data("group_a_map", "group_a_edges")
    build_graph(paper_map, edges)