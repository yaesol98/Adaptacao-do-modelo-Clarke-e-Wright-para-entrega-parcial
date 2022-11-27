import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import collections
import itertools
from sklearn.preprocessing import MinMaxScaler

import node
import edge
import vehicle
import product
import baggage

def euclidean(inode,jnode):
    """
    The euclidean distance between two nodes.

    :param inode: First Node
    :param jnode: Second Node
    """
    return math.sqrt((inode.loc_x - jnode.loc_x)**2 +(inode.loc_y - jnode.loc_y)**2)

def normalization_dists (edges, dists, depot, source, n_nodes):

    temp_dists = np.zeros((n_nodes, n_nodes))

    for edge in edges:
        cost, inode, jnode = edge.cost, edge.inode, edge.jnode
        temp_dists[inode.id,jnode.id] = dists[inode.id, depot.id] + dists[source[0].id, jnode.id] - cost
    
    max_dist_norm = np.max(temp_dists)
    min_dist_norm = np.min(temp_dists)
   
    #O mínimo está sendo considerado como 0, pois a partida e chegada no mesmo node é 0
    dists_norm = (temp_dists - min_dist_norm)/(max_dist_norm - min_dist_norm)
    
    return dists_norm

def normalization_edges_revenues(edges):
    revenues = []

    for edge in edges:
        revenues.append(edge.revenue)
    
    max_revenue = np.max(revenues)
    min_revenue = np.min(revenues)

    for edge in edges:
        edge.revenue_norm = (edge.revenue - min_revenue)/ (max_revenue - min_revenue)

    return edges



class Problem:
    """
    An instance of this class represent single depot Orienteering Problem
    """

    def __init__(self, name, sources, nodes, depot, type_products, vehicles_avaliable):
        """
        Initialise

        :param name: The name of the problem
        :param nodes: The nodes to visit
        :param depot: The depot
        :param type_products: The caract. of produts
        :param vehicles_avaliable: The vehicles available in depot to departure
        :param sources: The source nodes.


        :attr n_nodes: The number of nodes + depot
        
        :attr vehicles: The vehicles delivering / Path
        :attr dists: The matrix of distances between nodes
        :attr dists_norm: The matriz of distances normalized between nodes
        :attr position: A dictionary of nodes positions
        :attr edges: The edges connecting the nodes
        """

        self.name = name
        self.nodes = nodes
        self.depot = depot
        self.type_products = type_products
        self.vehicles_avaliable = vehicles_avaliable
        self.sources = sources

        self.vehicles = []

        self.n_nodes = len(nodes) + 1 #Acresentar 1 devido ao depot - DEVE SER ACRESCENTADO CASO SOURCE FOR DIFERENTE DO DEPOT  

        #Usado para corte
        self.cap_weight = 0
        self.cap_volumn = 0

        # Initialise edges list and nodes positions
        edges = collections.deque()
        dists = np.zeros((self.n_nodes, self.n_nodes)) #google maps - importar matrix


        # Calculate the matrix of distances and instantiate the edges
        #and define nodes colors and positions - VERIFICAR
        for node1, node2 in itertools.permutations(itertools.chain(nodes,(depot,)),2):
            # Calculate the edge cost
            id1, id2 = node1.id, node2.id
            cost = euclidean(node1,node2)

            # Compile the oriented matrix of distances between nodes, without depot
            dists[id1,id2] = cost

            # Create the edge
            if not node1.isdepot and not node2.isdepot: #and not node2.issource: - DEVE SER ACRESCENTADO CASO SOURCE FOR DIFERENTE DO DEPOT 
                edges.append(edge.Edge(node1,node2,cost))

        self.dists = dists
        self.edges = edges
        self.dists_norm = normalization_dists(edges, dists, depot, sources, self.n_nodes)
        normalization_edges_revenues(edges)

    def __hash__ (self):
        return id(self)

    def __repr__(self):
        return f"""
        Problem {self.name}
        -----------------------------------------------
        nodes: {self.n_nodes}
        vehicles: {np.count(self.vehicles)}
        products: {np.count(self.products)}
        multi-source/depot: {self.multi_depot}
        -----------------------------------------------
        """

    @property
    def multi_depot (self):
        return len(self.depot) > 1 #VERIFICAR

    def iternodes (self):
        """ A method to iterate over all the nodes of the problem (i.e., sources, customers, depot)"""
        return itertools.chain(self.sources, self.nodes, (self.depot,))

def read_nodes(filename='clientes.xlsx', path='', products='produto.xlsx'):
    """
    This method is used to read nodes from a file "client.xlsx" 
    and return a standard Problem instance

    :param filename: The name of file to read.
    :param path: The path where the file is
    :return: The nodes list and depot
    """

    # Read Problem data
    clients = pd.read_excel(filename)

    # Read Nodes parameters
    n_nodes = clients.value_counts

    # Initialise node lists
    baggages = []
    nodes, depot, sources = [], None , []

    # Read nodes characteristics
    for i, client in enumerate(clients.values):
        if client[0] == 'Depot':
            for id,qtd in zip(clients.columns[3:], client[3:]):
                baggages.append(baggage.Baggage(id,qtd))
            depot = node.Node(i, client[1], client[2], 0 ,None, baggages,isdepot=True)
            sources.append(node.Node(i, client[1], client[2], 0 ,None, baggages,isdepot=True))

        else:
            revenue = 0

            for id,qtd,product in zip(clients.columns[3:], client[3:], products):
                weight = qtd * product.weight
                volumn = qtd * product.volumn
                baggages.append(baggage.Baggage(id,qtd,weight,volumn))
                revenue += qtd * product.price #PREÇO TOTAL DOS PRODUTOS
            nodes.append(node.Node(i, client[1], client[2], revenue, baggages))
        
        baggages = []

    return nodes, depot, sources

def read_vehicle(filename = 'Carac veiculo.xlsx', path=''):
    """
    This method is used to read nodes from a file "vehicles.xlsx" 
    and return a vehicle list

    :param filename: The name of file to read.
    :param path: The path where the file is
    :return: The vehicles list
    """
    # Read Vehicles data
    data_vehicles = pd.read_excel(filename) 

    # Initialise vehicles lists
    vehicles = []

    # Read vehicles characteristics
    for i, data_vehicle in enumerate(data_vehicles.values):
        for n in range(int(data_vehicle[1])):
            vehicles.append(vehicle.Vehicle((str(i)+str(n)), data_vehicle[0], data_vehicle[2], data_vehicle[3], data_vehicle[4], data_vehicle[5], data_vehicle[6], data_vehicle[7]))

    return vehicles

def read_products(filename = 'produto.xlsx', path=''):
    """
    This method is used to read nodes from a file "produto.xlsx" 
    and return a products list

    :param filename: The name of file to read.
    :param path: The path where the file is
    :return: The products list
    """

    # Read Products data
    data_products = pd.read_excel(filename)

    # Initialise products lists
    products = []

    # Read products characteristics
    for i, data_product in enumerate(data_products.values):
        #TRANSFORMAR O ID DO PRODUCT DE STR PARA INT (ter um base de dado) - VERIFICAR
        products.append(product.Type_product(data_product[0], data_product[2],data_product[3],data_product[4],data_product[5]))

    return products

def read_problem(filename_client=None, filename_vehicle=None, filename_product=None, path=''):
    products = read_products(filename_product, path)
    nodes, depot, sources = read_nodes(filename_client, path, products)
    vehicles = read_vehicle(filename_vehicle, path)

    return Problem(filename_client, sources, nodes, depot, products, vehicles)

