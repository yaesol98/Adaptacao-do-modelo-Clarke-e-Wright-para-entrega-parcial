import collections
import numpy as np
#from utils import calculate_weight

class Node:
    """
    An instance of this class represent a node to visit or depot
    """

    def __init__(self, id, loc_x, loc_y, revenue = 0, dem=[], stock=[], color = "fDDD71", isdepot=False):
        """
        Initialise.

        :param id: The unique id of the node.
        :param loc_x: The x-coordinate of the node.
        :param loc_y: The y-coordinate of the node.
        :param dem: The demand of n products in node.
        :param stock: The stock of n product in node.
        :param isdepot: A boolean variable that says if the node is the depot.
        :param revenue: The revenue.
        
        :param vehicles: The number of vehicles starting from this node (it is 0
                         if the node is not a source). - IT WILL BE USED IF PROBLEM IS MULTI-SOURCE

            *** Parameters used by the Mapper ***
        :attr assigend: True if the node is assigned to a source and 0 otherwise
        :attr preferences: Used in case of source node for the round-robin process.
        :attr nodes: Used in case of source for keeping the nodes assigned to it.

            *** Parameters used by the PJS ***
        :attr from_source: The length of the current path from the source to this node.
        :attr to_depot: The length of the current path from this node to the depot.
        :attr route: The current route corresponding to the node.
        :attr link_left: True if the vehicle is coming from depot, False otherwise.
        :attr link_right: True if the vehicle is going to depot, False otherwise.
        :attr attended: True if all demand was attended
        :atrr weight: Weight of all product to be delivere
        """

        self.id = id
        self.loc_x = loc_x
        self.loc_y = loc_y
        self.dem = dem
        self.stock = stock
        self.color = color
        self.isdepot = isdepot
        self.revenue = revenue
        
        #ADICIONAR OUTROS ATTR SE FOR DEPOT?

        # Attributes used by the Mapper - VERIFICAR
        self.assigned = False
        self.preference = collections.deque()
        self.nodes = collections.deque()

        # Attributes used by the PJS - VERIFICAR
        self.from_source = 0
        self.to_depot = 0
        self.route = None
        self.link_left = False
        self.link_right = False
        self.cut_link_left = True
        self.cut_link_right = True
        self.attended = False
        self.is_cut = False
    
    def full_attended (self,problem):
        for node in problem.nodes:
            if self.id == node.id:
                #print('{}:, self:{}, problem:{}'.format(self.id, self.dem[0].qtd, node.dem[0].qtd))
                if self.dem[0].qtd == node.dem[0].qtd:
                    self.attended = True
                else:
                    self.attended= False

        return self.attended
    
    def update_dem(self, cap_weight, cap_volumn, problem):
        product = problem.type_products[0]
        
        for baggage in self.dem:
            #CONSIDERAR QUE TRABALHA APENAS COM 1 TIPO DE PRODUTO
            qtd_product = min(np.trunc(cap_weight/product.weight), np.trunc(cap_volumn/product.volumn))
            self.dem[0].qtd -= qtd_product
            
        self.dem[0].weight = self.dem[0].qtd * product.weight
        self.dem[0].volumn = self.dem[0].qtd * product.volumn
        
        return self

    def update_dem_reverse(self, cap_weight, cap_volumn, problem):
        product = problem.type_products[0]
        
        for node in problem.nodes:
            if self.id == node.id:
                problem_node = node

        for baggage in self.dem:
            #CONSIDERAR QUE TRABALHA APENAS COM 1 TIPO DE PRODUTO
            qtd_product = min(np.trunc(cap_weight/product.weight), np.trunc(cap_volumn/product.volumn))
            self.dem[0].qtd = problem_node.dem[0].qtd - (self.dem[0].qtd + qtd_product)
            
        self.dem[0].weight = self.dem[0].qtd * product.weight
        self.dem[0].volumn = self.dem[0].qtd * product.volumn
        
        return self
    
    def reupdate_dem(self,problem):
        product = problem.type_products[0]
        
        for baggage in self.dem:
            self.dem[0].qtd = self.dem[0].invisible_qtd
        
        self.dem[0].weight = self.dem[0].qtd * product.weight
        self.dem[0].volumn = self.dem[0].qtd * product.volumn
        
        return self

    def is_attended(self, problem, principal_route, node):
        
        node.total_weight = sum(baggage.weight for baggage in node.dem)
        node.total_volumn = sum(baggage.volumn for baggage in node.dem)

        #if principal_route.nodes == None:
        #    print(principal_route.nodes)
        #    print(node)

        if node in principal_route.nodes:
            node.attended = True
            return True
        

        if (problem.vehicles_avaliable[0].max_weight - principal_route.weight >= node.total_weight) and (problem.vehicles_avaliable[0].max_vol - principal_route.volumn >= node.total_volumn):
            node.attended = True
            return True
        else:
            return False
    
    def __hash__ (self):
        return self.id

    def __repr__ (self):
        return f"Node {self.id}"
    
    #ALTERAR
    def isattended(self):
        if self.dem == self.stock:
            self.attended = True
        return None


