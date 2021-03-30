import os

import networkx as nx
from matplotlib import pyplot as plt


def getG(inp, f0, f1):
    """
    Get the output G in the ARI block which is determined by the init[16] and init[17]
    Input:
    - inp: INIT[16:17]
    - f0: Output when A = 0
    - f1: Output when A = 1
    Output:
    - returns G
    """
    if inp == "00":
        return 0
    elif inp == "01":
        return f0
    elif inp == "10":
        return 1
    elif inp == "11":
        return f1


def getP(inp, y):
    """
    Get the output P in the ARI block which is determined by the init[18] and init[19]
    Input:
    - inp: INIT[18:19]
    - y: output Y of the ARI block
    Output:
    - returns P
    """
    if inp == "00":
        return 0
    elif inp == "01":
        return y
    else:
        return 1


class Graph:
    """
    A class for the graph generation and simulation

    Attributes: 
    - filePath: Path of the input .vm file
    - graph: MultiDiGraph from the networkx module which supports multiple edges between two nodes 
        and it is a directed graph
    - dataType: The input, output and wire instances
    - modules: The INBUF, OUTBUF, TRIBUFF, CFG1, CFG2, CFG3, CFG4 modules with inputs and outputs
    - defparams: The defparams data
    - ari1: The ARI1 modules with inputs and outputs

    Functions:
    - Private:
        - __init__
        - __parse
        - __findNode
        - __drawGraph
    - Public:
        - construct
        - simulate
        - TMRApproach
    """

    def __init__(self):
        self.filePath = input(
            '\x1b[0;36;49m' + "Enter the path for the .vm file: " + '\x1b[0m')
        self.graph = nx.MultiDiGraph()
        # Parse the given file and get the data
        self.dataTypes, self.modules, self.defparam, self.ari1 = self.__parse()

    def __parse(self):
        """
        A function to parse the input vm file
        Output:
        - dataType: The input, output and wire instances
        - modules: The INBUF, OUTBUF, TRIBUFF, CFG1, CFG2, CFG3, CFG4 modules with inputs and outputs
        - defparams: The defparams data
        - ari1: The ARI1 modules with inputs and outputs
        """
        with open(self.filePath, "r") as fp:
            fileData = fp.readlines()
        flag = 0
        name = ""
        mod = ""
        flags = {
            "INBUF": 0,
            "OUTBUF": 0,
            "CFG1": 0,
            "CFG2": 0,
            "CFG3": 0,
            "CFG4": 0,
            "TRIBUFF": 0,
            "": 0
        }
        ariFlag = 0
        ari1 = {}
        defparam = {}
        dataTypes = {
            "input": [],
            "output": [],
            "wire": []
        }
        modules = {}
        # Loop through each line of the file
        for line in fileData:
            # Split the lines to words
            words = line.split()
            # Edge cases
            if len(words) == 0:
                continue
            if words[0] == "//" or words[0] == "`timescale" or words[0] == "endmodule":
                continue
            if words[0] == "module":
                flag = 1
                continue
            if flag == 1:
                if words[0] == ";":
                    flag = 0
                continue
            # If the first word is a datatype i.e., input/output/wire
            if words[0] in list(dataTypes.keys()):
                dataTypes[words[0]].append(words[1])
            # If it is CFG1 / CG2 / CFG3 / CFG4 / INBUF / OUTBUF / TRIBUFF module
            if words[0] in flags.keys():
                # Copy the instantiation name and set the corresponding flag to 1
                mod = words[0]
                name = words[1]
                modules[name] = []
                flags[mod] = 1
                continue
            # If the flag is 1
            if flags[mod] == 1:
                # End of the module
                if words[0] == ");":
                    flags[mod] = 0
                    continue
                # Ports to the module
                else:
                    # Append the data within the paranthesis, if it is an input
                    # Insert it at index 0, if it is an output
                    x = words[0].find("(")
                    y = words[0].find(")")
                    if words[0][1] == "Y":
                        modules[name].insert(0, words[0][x + 1:y])
                    else:
                        modules[name].append(words[0][x+1:y])
            # If it is an ARI1 module
            if words[0] == "ARI1":
                # Copy the instantiation name and set the flag to 1
                name = words[1]
                ari1[name] = []
                ariFlag = 1
                continue
            if ariFlag == 1:
                # End of the module
                if words[0] == ");":
                    ariFlag = 0
                    continue
                else:
                    # Append the data within the paranthesis, if it is an input
                    # Insert it at index 0, if it is an output
                    x = words[0].find("(")
                    y = words[0].find(")")
                    ari1[name].append(words[0][x+1:y])
            # If it is a defparam
            if words[0] == "defparam":
                try:
                    words[1] = words[1] + words[2]
                except:
                    pass
                # Split the word to get the hexadecimal value
                x = words[1].replace("=", "= ")
                x = x.replace(";", " ;").split()
                defparam[name] = x[1]
        # Return the data
        return dataTypes, modules, defparam, ari1

    def __findNode(self, current):
        """
        A function that finds the node where the output is generated
        Input:
        - current: The input port of some module
        Output:
        - i: The module where current is an output
        - color: The color to differentiate the output wires of ARI1 block
            Color Map
            Red   |  Y
            Blue  |  D
            Green |  FCO 
        """
        # Looping through the CFG1 / CG2 / CFG3 / CFG4 / INBUF / OUTBUF / TRIBUFF modules
        # Output for these modules is at index 0
        for i, j in self.modules.items():
            # Compare it to the current name
            if current == j[0]:
                return i, 'black'
        # Looping through the ARI1 modules
        # Output for the module is at index 0, 1, 2
        for i, j in self.ari1.items():
            # Compare it to the current name
            # Red: Y, Blue: S, Green: FCO
            if current == j[0]:
                return i, 'red'
            elif current == j[1]:
                return i, 'blue'
            elif current == j[2]:
                return i, 'green'

    def __drawGraph(self, fileName):
        """
        A function to draw the graph on the canvas
        Input
        - fileName: Output file name
        """
        # Get the attributes of the graph and plot it
        pos = nx.get_node_attributes(self.graph, 'pos')
        color = list(nx.get_node_attributes(self.graph, 'color').values())
        size = list(nx.get_node_attributes(self.graph, 'size').values())
        graphDict = nx.to_dict_of_lists(self.graph)

        print('\x1b[0;31;49m' + "\nConstructing the graph...\n" + '\x1b[0m')

        nx.draw(self.graph, pos, node_color=color,
                with_labels=True, font_size=24, node_size=size)
        outputPath = 'Output/' + fileName + '.png'
        plt.savefig(outputPath)
        print('\x1b[1;32;49m' + "The graph as a adjacency list:" + '\x1b[0m')
        for x, y in graphDict.items():
            print('\x1b[0;34;49m' + x + '\x1b[0m', end=": ")
            print(y)
        print('\x1b[0;33;49m' +
              f"\nThe graph is stored as an image at {outputPath}." + '\x1b[0m')

    def construct(self):
        """
        A function that constructs and draws the graph from the parsed vm file
        """
        plt.figure(figsize=(100, 200))
        moduleKeys = list(self.modules.keys())
        ibuf, obuf, cfg = 0, 0, 0
        # Add the input data types to the graph
        for i in range(len(self.dataTypes["input"])):
            self.graph.add_node(
                self.dataTypes["input"][i], pos=(0, -10*i), color='blue', size=5000)
        # Add the output data types to the graph
        for i in range(len(self.dataTypes["output"])):
            self.graph.add_node(
                self.dataTypes["output"][i], pos=(50, -10*i), color='green', size=5000)
        for i in range(len(moduleKeys)):
            # Add the INBUF modules to the graph
            if moduleKeys[i].endswith("ibuf"):
                self.graph.add_node(moduleKeys[i], pos=(
                    10, -10*ibuf), color='red', size=20000)
                ibuf += 1
            # Add the OUTBUF modules to the graph
            elif moduleKeys[i].endswith("obuf"):
                self.graph.add_node(moduleKeys[i], pos=(
                    40, -10*obuf), color='yellow', size=20000)
                obuf += 1
            # Add the TRIBUFF / CFG1 / CFG2 / CFG3 / CFG4 modules to the graph
            else:
                self.graph.add_node(moduleKeys[i], pos=(
                    30, -10*cfg), color='orange', size=60000)
                cfg += 1
        # Add the ARI1 modules to the graph
        x = 0
        for i in self.ari1.keys():
            self.graph.add_node(i, pos=(20, -10*x), color='orange', size=60000)
            x += 1
        # Add VCC and GND to the graph
        self.graph.add_node("GND", pos=(10, 20), color='grey', size=5000)
        self.graph.add_node("VCC", pos=(30, 20), color='grey', size=5000)
        # For each INBUF, add an edge
        for i in self.dataTypes["input"]:
            if i+"_ibuf" in moduleKeys:
                self.graph.add_edge(i, i+"_ibuf", color='black')
        # For each OUTBUF, add an edge
        for i in self.dataTypes["output"]:
            if i+"_obuf" in moduleKeys:
                self.graph.add_edge(i+"_obuf", i, color='black')
        for x, y in self.modules.items():
            # For TRIBUFF module
            if x.endswith("obuft"):
                if y[0] in self.dataTypes["output"]:
                    self.graph.add_edge(x, y[0], color='black')
                self.graph.add_edge("GND", x, color='black')
                self.graph.add_edge("GND", x, color='black')
            # For OUTBUF / CFG1 / CFG2 / CFG3 / CFG4 modules
            elif not x.endswith("ibuf"):
                for j in range(1, len(y), 1):
                    if y[j] == "GND" or y[j] == "VCC":
                        self.graph.add_edge(y[j], x, color='black')
                    else:
                        node, color = self.__findNode(y[j])
                        self.graph.add_edge(node, x, color=color)
        # For ARI1 modules
        for x, y in self.ari1.items():
            for j in range(3, len(y), 1):
                if y[j] == "GND" or y[j] == "VCC":
                    self.graph.add_edge(y[j], x)
                else:
                    node, color = self.__findNode(y[j])
                    self.graph.add_edge(node, x, color=color)
        # Draw the graph on the plt canvas
        self.__drawGraph(os.path.splitext(os.path.basename(self.filePath))[0])

    def simulate(self):
        """
        A function that simulates the vm file for the given input 
        """
        # Get the longest path in the graph
        maxRange = nx.algorithms.dag.dag_longest_path_length(self.graph)
        inputValue = {}
        print('\x1b[1;32;49m' +
              "\nInput values for simulation of the circuit:" + '\x1b[0m')
        for i in self.dataTypes["input"]:
            inputValue[i] = input(
                '\x1b[0;36;49m' + f"Enter the value for input {i}: " + '\x1b[0m')
        print()
        # For each edge to the successor of GND, add weight as 0
        for i in self.graph.successors("GND"):
            self.graph["GND"][i][0]["weight"] = "0"
        # For each edge to the successor of GND, add weight as 1
        for i in self.graph.successors("VCC"):
            self.graph["VCC"][i][0]["weight"] = "1"
        # For each edge to the INBUF module and its successors, add corresponding weight
        for i in self.dataTypes["input"]:
            try:
                self.graph[i][i+"_ibuf"][0]["weight"] = inputValue[i]
                for j in self.graph.successors(i+"_ibuf"):
                    self.graph[i+"_ibuf"][j][0]["weight"] = inputValue[i]
            except:
                pass
        # Loop through the range of longest path
        # As there are weight dependencies among the modules
        for a in range(maxRange):
            # Loop through the defparams
            for i, j in self.defparam.items():
                # Split the hexadecimal value where
                # 0: Length of the number
                # 2: The hexadecimal number
                y = j.replace("'", " '")
                y = y.replace("h", "h ").split()
                # If it is CFG1 / CG2 / CFG3 / CFG4 / INBUF / OUTBUF / TRIBUFF module
                if i in self.modules.keys():
                    # Convert the hexadecimal number to binary
                    bNum1 = bin(int(y[2], 16))[2:].zfill(int(y[0]))[::-1]
                    x = ""
                    # Get the index for retriving the output
                    try:
                        for src, dest, data in self.graph.in_edges(i, data=True):
                            x += str(data['weight'])
                    except:
                        continue
                    # Revert the index
                    x = x[::-1]
                    # Add the weight to the edges leading to its successors
                    for k in self.graph.successors(i):
                        self.graph[i][k][0]["weight"] = bNum1[int(x, 2)]
                # If it is ARI1 module
                elif i in self.ari1.keys():
                    # bNum1: init[0:15]
                    # bNum2: init[17:16]
                    # bNum3: init[19:18]
                    bNum = bin(int(y[2], 16))[2:].zfill(y[0])
                    bNum1 = bNum[4:][::-1]
                    bNum2 = bNum[2:4]
                    bNum3 = bNum[:2]
                    x = ""
                    # Get the index for retriving the output
                    try:
                        for src, dest, data in self.graph.in_edges(i, data=True):
                            x += str(data['weight'])
                    except:
                        continue
                    x = x[::-1]
                    # Get the adcb, fc1, dcb
                    adcb = x[:4]
                    fci = x[4]
                    dcb = x[:3]
                    # Calculate f0, f1 with keeping a = 0 and a = 1 respectively
                    y = bNum1[int(adcb, 2)]
                    f0 = bNum1[int('0'+dcb, 2)]
                    f1 = bNum1[int('1'+dcb, 2)]
                    # Generate s from the truth table
                    if y+fci == "00" or y+fci == "11":
                        s = 0
                    elif y+fci == "01" or y+fci == "10":
                        s = 1
                    # Get p and g values for the given input
                    g = getG(bNum2, f0, f1)
                    p = getP(bNum3, y)
                    # Generate the fco from the truth table
                    if p == '0':
                        fco = g
                    else:
                        fco = fci
                    # For each out edges of i
                    # Check the color of the edge and add corresponding weight
                    for src, dest, data in self.graph.out_edges(i, data=True):
                        if data["color"] == "green":
                            data['weight'] = fco
                        if data["color"] == "blue":
                            data['weight'] = s
                        if data["color"] == "red":
                            data['weight'] = y

        out = {}
        # For each edge from OUTBUF, add corresponding weights
        for i in self.dataTypes["output"]:
            try:
                for j in self.graph.predecessors(i):
                    for k in self.graph.predecessors(j):
                        weight = self.graph[k][j][0]["weight"]
                        self.graph[j][i][0]["weight"] = weight
                        out[i] = weight
            except:
                pass
        print('\x1b[1;32;49m' + "Simulation output:" + '\x1b[0m')
        for i, j in out.items():
            print('\x1b[0;35;49m' + i + '\x1b[0m', end=": ")
            print(j)
        print()

    def TMRApproach(self):
        """
        A function that simulates the triple mode redundancy (TMR) approach
        """
        plt.clf()
        inputNodes = list(input(
            '\x1b[0;36;49m' + "Enter the nodes to be duplicated(seperated by a space): " + '\x1b[0m').strip().split())
        pos = nx.get_node_attributes(self.graph, 'pos')
        orIdx = 0
        andIdx = 0
        # For each input module
        for node in inputNodes:
            # If the input is not a module, raise an exception
            if node not in list(self.modules.keys()) + list(self.ari1.keys()):
                raise ValueError("Module not in the file.")
            # If the input is a module
            else:
                # Retrive the in edges and out edges on the node
                inEdges = self.graph.in_edges(node, data=True)
                inData = []
                for src, dest, data in inEdges:
                    inData.append((src, dest, data))
                outEdges = self.graph.out_edges(node, data=True)
                outData = []
                for src, dest, data in outEdges:
                    outData.append((src, dest, data))
                currPos = pos[node]
                andGate1 = "and"+str(andIdx)
                andGate2 = "and"+str(andIdx+1)
                andGate3 = "and"+str(andIdx+2)
                orGate = "or"+str(orIdx)
                # Update the positions of the modules
                for mod, position in pos.items():
                    if currPos[0] == position[0] and currPos[1] > position[1]:
                        pos[mod] = (position[0], position[1]-20)
                nx.set_node_attributes(self.graph, pos, 'pos')
                # Remove the current node
                self.graph.remove_node(node)
                # Add the new three nodes of the module
                self.graph.add_node(
                    node+"_0", pos=(currPos[0], currPos[1]), color='magenta', size=60000)
                self.graph.add_node(
                    node+"_1", pos=(currPos[0], currPos[1]-10), color='magenta', size=60000)
                self.graph.add_node(
                    node+"_2", pos=(currPos[0], currPos[1]-20), color='magenta', size=60000)
                # Add the AND and OR gates
                self.graph.add_node(
                    andGate1, pos=(currPos[0]+5, currPos[1]), color='beige', size=30000)
                self.graph.add_node(
                    andGate2, pos=(currPos[0]+5, currPos[1]-10), color='beige', size=30000)
                self.graph.add_node(
                    andGate3, pos=(currPos[0]+5, currPos[1]-20), color='beige', size=30000)
                self.graph.add_node(
                    orGate, pos=(currPos[0]+8, currPos[1]-10), color='cyan', size=30000)
                # For each in edge
                for src, dest, data in inData:
                    # Duplicates the edges to all the three nodes
                    self.graph.add_edge(
                        src, node+"_0", weight=data["weight"], color=data["color"])
                    self.graph.add_edge(
                        src, node+"_1", weight=data["weight"], color=data["color"])
                    self.graph.add_edge(
                        src, node+"_2", weight=data["weight"], color=data["color"])
                # For each out edge
                for src, dest, data in outData:
                    # Pass the node outputs to the AND gates
                    self.graph.add_edge(
                        node+"_0", andGate1, weight=data["weight"], color=data["color"])
                    self.graph.add_edge(
                        node+"_1", andGate1, weight=data["weight"], color=data["color"])
                    self.graph.add_edge(
                        node+"_1", andGate2, weight=data["weight"], color=data["color"])
                    self.graph.add_edge(
                        node+"_2", andGate2, weight=data["weight"], color=data["color"])
                    self.graph.add_edge(
                        node+"_2", andGate3, weight=data["weight"], color=data["color"])
                    self.graph.add_edge(
                        node+"_0", andGate3, weight=data["weight"], color=data["color"])
                    # Pass the AND gate outputs to the OR gate
                    self.graph.add_edge(
                        andGate1, orGate, weight=data["weight"], color=data["color"])
                    self.graph.add_edge(
                        andGate2, orGate, weight=data["weight"], color=data["color"])
                    self.graph.add_edge(
                        andGate3, orGate, weight=data["weight"], color=data["color"])
                    # Pass the OR gate output to the destination
                    self.graph.add_edge(
                        orGate, dest, weight=data["weight"], color=data["color"])
                orIdx += 1
                andIdx += 3
        # Draw the graph on the plt canvas
        self.__drawGraph(os.path.splitext(
            os.path.basename(self.filePath))[0]+"_TMR")
