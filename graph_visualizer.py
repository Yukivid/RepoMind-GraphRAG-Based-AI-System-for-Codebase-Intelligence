from pyvis.network import Network
import tempfile
import os


def visualize_graph(graph):
    """
    Full Knowledge Graph visualization with:
    - ALL nodes & edges
    - Large spacing
    - Clear edges
    - Static (no physics)
    """

    net = Network(
        height="1200px",        # MUCH taller
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#000000"
    )

    # -----------------------------
    # Disable physics (no movement)
    # -----------------------------
    net.toggle_physics(False)

    # -----------------------------
    # Configure LARGE SPACING
    # -----------------------------
    net.set_options("""
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "levelSeparation": 350,
          "nodeSpacing": 300,
          "treeSpacing": 350,
          "sortMethod": "directed"
        }
      },
      "nodes": {
        "shape": "box",
        "font": {
          "size": 16
        },
        "margin": 18,
        "widthConstraint": {
          "maximum": 320
        }
      },
      "edges": {
        "smooth": false,
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.7
          }
        },
        "color": {
          "color": "#666666"
        },
        "font": {
          "size": 12
        }
      },
      "interaction": {
        "dragNodes": false,
        "dragView": true,
        "zoomView": true
      },
      "physics": {
        "enabled": false
      }
    }
    """)

    # -----------------------------
    # Add ALL nodes
    # -----------------------------
    for node_id, attrs in graph.nodes(data=True):
        label = attrs.get("name", node_id)
        kind = attrs.get("type", "symbol")

        color = {
            "function": "#E3F2FD",
            "class": "#E8F5E9",
            "call": "#FFFDE7"
        }.get(kind, "#F5F5F5")

        net.add_node(
            node_id,
            label=label,
            title=node_id,
            color=color
        )

    # -----------------------------
    # Add ALL edges
    # -----------------------------
    for src, tgt, attrs in graph.edges(data=True):
        net.add_edge(
            src,
            tgt,
            label=attrs.get("relation", ""),
            arrows="to"
        )

    # -----------------------------
    # Save HTML
    # -----------------------------
    path = os.path.join(
        tempfile.gettempdir(),
        "knowledge_graph_spaced.html"
    )
    net.save_graph(path)

    return path
