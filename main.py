from Graph import Graph


# Main driver function for the NetList Viewer and Simulator
if __name__ == "__main__":
    # Initialize the graph
    graph = Graph()
    # Construct the graph
    graph.construct()
    # Simulate the graph
    graph.simulate()
    # Simulate the TMR approach
    graph.TMRApproach()
