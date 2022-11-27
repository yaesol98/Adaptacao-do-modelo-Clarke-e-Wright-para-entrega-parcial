import collections
import operator
import copy
from pickle import TRUE

from sqlalchemy import false, true
from sympy import N, principal_branch

import baggage

class Route:
    """
    An instance of this class represent a route, 
    a path from depot - node - depot made by a vehicle
    """

    def __init__(self, source, depot, starting_node):
        """
        Initialise

        :param depot: The depot of the route
        :param staring_node: The first node included into the route

        :attr nodes: the nodes part of the route
        
        :attr cost: The total cost of the route
        :attr revenue: The total revenue of the route.
        :attr weight: The total weight of produts of the route.
        :attr weight: The total volumn of produts of the route.
        :attr total_saving: The total of saving of the route.
        """
        
        self.depot = depot
        self.source = source
        #self.starting_node = starting_node 

        self.nodes = collections.deque([starting_node])
        self.cost = starting_node.from_source + starting_node.to_depot
        self.revenue = starting_node.revenue
        self.weight = sum(baggage.weight for baggage in starting_node.dem)
        self.volumn = sum(baggage.volumn for baggage in starting_node.dem)
        self.total_saving = 0

        self.is_full = False
    
    def update_route_weight_volumn(self):
        self.weight = 0
        self.volumn = 0

        for node in self.nodes:
            self.weight += sum(baggage.weight for baggage in node.dem)
            self.volumn += sum(baggage.volumn for baggage in node.dem)
        
        return self

    def merge(self, other,edge,dists,depot):
        """
        This method merges in place this route with another route.

        :param other: The other route.
        :param edge: The edge used for merging.
        :param dists: The matrix of distances between nodes.
        """

        # Get the cost and the nodes of the edge
        inode, jnode = edge.inode, edge.jnode
        edge_cost = dists[inode.id,jnode.id]

        # Update the list of nodes in the route
        self.nodes.extend(other.nodes)

        # Disconnect inode -> depot and depot -> jnode
        inode.link_right = False
        jnode.link_left = False
        
        # Update the cost, weight and volumn of this route
        self.cost += edge_cost - inode.to_depot + (other.cost - jnode.from_source)
        self.weight += other.weight
        self.volumn += other.volumn
        self.total_saving += edge.savings[depot.id] + other.total_saving 

        # Update the route the nodes belong to - VERIFICAR
        for node in other.nodes:
            node.route = self


    def cut_merge(self, other,edge,dists,depot, best_route, problem):

        """
        This method merges in place this route with another route.

        :param other: The other route.
        :param edge: The edge used for merging.
        :param dists: The matrix of distances between nodes.
        """
        # Get the cost and the nodes of the edge
        inode, jnode = edge.inode, edge.jnode
        edge_cost = dists[inode.id,jnode.id]

        #print('INICIANDO CUT_MERGE: {},{}'.format(inode,jnode))

        #Se principal_route estiver conectando com node
        if len(other.nodes) == 1 or len(self.nodes) == 1:  
            
            if inode.route == best_route:
                if inode.is_attended(problem,best_route,inode):
                    inode.link_right = False
                
                if jnode.is_attended(problem,best_route,jnode):
                    jnode.link_left = False
                    self.cost += edge_cost - inode.to_depot + (other.cost - jnode.from_source)
                    self.weight += other.weight
                    self.volumn += other.volumn
                    self.total_saving += edge.savings[depot.id] + other.total_saving
                
                else:
                    vehicle = problem.vehicles_avaliable[0]
                    cap_weight = vehicle.max_weight - best_route.weight
                    cap_volumn = vehicle.max_vol - best_route.volumn
                    self.cost += edge_cost - inode.to_depot + (other.cost - jnode.from_source)

                    jnode.update_dem(cap_weight, cap_volumn, problem)
                    jnode.route.update_route_weight_volumn() 
                    best_route.is_full = True
                
                self.nodes.extend(other.nodes)
                
                for node in other.nodes:
                    if node.attended:
                        node.route = self
        

            elif jnode.route == best_route:
                if inode.is_attended(problem,best_route,inode):
                    inode.link_right = False
                    self.cost += edge_cost - inode.to_depot + (other.cost - jnode.from_source)
                    self.weight += other.weight
                    self.volumn += other.volumn
                    self.total_saving += edge.savings[depot.id] + other.total_saving

                    self.nodes.extend(other.nodes)
                
                    for node in other.nodes:
                        if node.attended:
                            node.route = self

                else:
                    vehicle = problem.vehicles_avaliable[0]
                    cap_weight = vehicle.max_weight - best_route.weight
                    cap_volumn = vehicle.max_vol - best_route.volumn
                    self.cost += edge_cost - inode.to_depot + (other.cost - jnode.from_source)

                    inode.update_dem(cap_weight, cap_volumn, problem) 
                    inode.route.update_route_weight_volumn()

                    best_route.is_full = True

                    other.nodes.extendleft(self.nodes)

                    for node in self.nodes:
                        if node.attended:
                            #print('ERROR - INODE ATTENDED')
                            exit()

                if jnode.is_attended(problem,best_route,jnode):
                    jnode.link_left = False

            else:
                #print('ERROR - NENHUM NODE É BESTROUTE')
                #print(best_route.nodes)
                #print(inode)
                #print(inode.route.nodes)
                #print(jnode)
                #print(jnode.route.nodes)
                exit()
        else:
            inode.link_right = False
            jnode.link_left = False

            # Update the cost, weight and volumn of this route
            self.cost += edge_cost - inode.to_depot + (other.cost - jnode.from_source)
            self.weight += other.weight
            self.volumn += other.volumn
            self.total_saving += edge.savings[depot.id] + other.total_saving 
        
        inode.cut_link_right = False
        jnode.cut_link_left = False

        return best_route

    

def PJS (problem, source, nodes, depot,alpha = 0.1):
    """
    """
    vehicle = problem.vehicles_avaliable[0]
    dists = problem.dists
    nodes = set(nodes)

    # Filter edges keeping only those that interest this subset of nodes and sort them
    sorted_edges = sorted([e for e in problem.edges if e.inode in nodes and e.jnode in nodes], key=lambda edge: edge.savings[depot.id], reverse=True)
    
    # Build a dummy solution where a vehicle starts from the source, visit a single node, and then goes to the depot
    routes = collections.deque()

    for node in nodes:
        # Calculate the distance from the node -> depot and depot -> node and save them
        node.from_source = dists[source.id,node.id]
        node.to_depot = dists[node.id,depot.id]
        
        # Eventually construct a new route that goes from the depot -> node and node -> depot
        while True:
            if (node.dem[0].weight > vehicle.max_weight) or (node.dem[0].volumn > vehicle.max_vol):
                node.update_dem(vehicle.max_weight, vehicle.max_vol, problem)
                route = Route(depot, depot, node)
                routes.append(route)
                
            else:
                route = Route(depot, depot, node)
                node.route = route
                node.link_left = True
                node.link_right = True
                routes.append(route)
                break
    
    # Filter edges keeping only those that interest this subset of nodes and sort them
    sorted_edges = sorted([e for e in problem.edges if e.inode in nodes and e.jnode in nodes], key=lambda edge: edge.savings[depot.id], reverse=True)
    
    # Merge the routes giving priority to edges with highest efficiency
    for edge in sorted_edges:
        
        inode, jnode = edge.inode, edge.jnode
        iroute, jroute = inode.route, jnode.route

        # If the edge connect node already into the same route next edge is considered
        if iroute is None or jroute is None or iroute == jroute:
            continue
                
        # If inode is the last of its route and jnode the first of its route, the merging is possible.
        if inode.link_right and jnode.link_left:
            # Compare the length of the new route to Tmax and other restriction
            if iroute.weight + jroute.weight <= vehicle.max_weight:  #CONSIDEREI APENAS 1º VEHÍCULO COM Nº INFINITO
                if iroute.volumn + jroute.volumn <= vehicle.max_vol:
                    # Merge the routes
                    iroute.merge(jroute, edge, dists,depot)
                    # Remove the route incorporated into iroute
                    routes.remove(jroute)

        # Interrupt if route exceed any restriction - ex: working-hour, volume anb weight
        #if len(routes) == None:
            #break
            
    # Return the solution as a list of the best possibile routes
    return sorted(routes, key = operator.attrgetter("cost"), reverse=False)#[:len(vehicles)]

















def to_attended(problem, principal_route, node):

    node.total_weight = sum(baggage.weight for baggage in node.dem)
    node.total_volumn = sum(baggage.volumn for baggage in node.dem)

    if (problem.vehicles_avaliable[0].max_weight - principal_route.weight >= node.total_weight) and (problem.vehicles_avaliable[0].max_vol - principal_route.volumn >= node.total_volumn):
        return 1 #True
    else:
        return 0 #False

def set_cut_saving(problem, best_route, best_routes_nodes = [], beta = 0.1, temp_best_nodes=[]):

    dists_norm, depot = problem.dists_norm, problem.depot
    best_routes_nodes = set(best_routes_nodes)
    start_node, final_node = None, None

    for node in best_route.nodes:
        if node.link_left == True:
            start_node = node
        if node.link_right == True:
            final_node = node  

    if start_node == None:
        #print('ERROR - SET_CUT_SAVING - START_NODE')
        #print('Best_route {}'.format(best_route.nodes))
        exit()
    if final_node == None:
        #print('ERROR - SET_CUT_SAVING - final_NODE')
        #print('Best_route {}'.format(best_route.nodes))
        exit()

    for edge in problem.edges:

        if edge.inode in best_route.nodes and edge.jnode in best_route.nodes:
            edge.cut_savings = {source.id : 0 for source in problem.sources}

        elif edge.inode.id in temp_best_nodes or edge.jnode.id in temp_best_nodes:
            edge.cut_savings = { source.id : 0 for source in problem.sources} 

        elif edge.inode == final_node: 
            costs, inode, jnode = edge.cost, edge.inode, edge.jnode

            attended = to_attended(problem, best_route, jnode) #return 1 or 0
            
            edge.cut_savings = {
                source.id : (1.0 - beta)*dists_norm[inode.id, jnode.id] + beta* attended
            for source in problem.sources}
           
        elif edge.jnode == start_node:

            costs, inode, jnode = edge.cost, edge.inode, edge.jnode

            attended = to_attended(problem, best_route, inode) # return 1 or 0

            edge.cut_savings = {
                source.id : (1.0 - beta)*dists_norm[inode.id, jnode.id] + beta* attended
            for source in problem.sources}
            
        else:
            edge.cut_savings = { source.id : 0 for source in problem.sources}

    return problem 


def break_route(worst_route,problem, routes, best_routes_nodes=[], temp_best_nodes=[], problem_cut = False):
    """"""
    best_route_deleted_id = []
    
    depot = problem.depot 
    source = problem.depot
    dists = problem.dists
    routes.remove(worst_route)     
    is_continue = False


    if not(problem_cut):
        for node in worst_route.nodes:
            node.from_source = dists[source.id,node.id]
            node.to_depot = dists[node.id,depot.id]

            best_route_deleted_id.append(node.id)  

            for route in routes:
                if route.nodes[0].id == node.id:
                    route.nodes.popleft()
                    route.is_full = False

                    for i in range(best_routes_nodes.count(node.id)):
                        best_routes_nodes.remove(node.id)

                    for i in range(temp_best_nodes.count(node.id)):
                        temp_best_nodes.remove(node.id)

                    
                    route.nodes[0].link_left = True
                    route.nodes[0].cut_link_left = True

                    #Atualizar a demanda utilizando invisble_qtd
                    node.reupdate_dem(problem)
                    node.route.update_route_weight_volumn() 

                    is_continue = True

                elif route.nodes[-1].id == node.id:
                    route.nodes.pop()
                    route.is_full = False

                    route.nodes[-1].link_right = True
                    route.nodes[-1].cut_link_right = True

                    for i in range(best_routes_nodes.count(node.id)):
                        best_routes_nodes.remove(node.id)

                    for i in range(temp_best_nodes.count(node.id)):
                        temp_best_nodes.remove(node.id)                

                    #Atualizar a demanda utilizando invisble_qtd
                    node.reupdate_dem(problem)      
                    node.route.update_route_weight_volumn()   

                    is_continue = True
    
    for node in worst_route.nodes:
        if node.id in best_routes_nodes:
            best_routes_nodes.remove(node.id)

        if node.id in temp_best_nodes:
            temp_best_nodes.remove(node.id)  

        route = Route(depot,depot, node)
        node.route = route
        node.link_left = True
        node.link_right = True
        node.cut_link_left = True
        node.cut_link_right = True
        node.attended = False
        routes.append(route)

    return routes, best_routes_nodes, temp_best_nodes, is_continue, best_route_deleted_id

def select_best_route(edge):
    """"""
    iroute = edge.inode.route
    jroute = edge.jnode.route

    if iroute.total_saving >= jroute.total_saving:
        best_route = iroute
        worst_route = jroute
    else:
        best_route = jroute
        worst_route = iroute

    return best_route, worst_route

def min_product(products):
    min_wei, min_vol  = float("inf"),float("inf")

    for product in products:
        if product.weight < min_wei:
            min_wei = product.weight
        if product.volumn < min_vol:
            min_vol = product.volumn

    return min_wei, min_vol

def set_savings (problem, alpha = 0.1, best_routes_nodes = []):
    """
    This method calculate the saving of edges #ACCORDING TO THE GIVEN ALPHA
    
    :param problem: The instance of the problem to solve
    :param alpha: The alpha parameter of the PJS
    :return: The problem instance modified in place
    """
    dists_norm, depot = problem.dists_norm, problem.depot
    best_routes_nodes = set(best_routes_nodes)
    
    for edge in problem.edges:
        cost, inode, jnode = edge.cost, edge.inode, edge.jnode
        if (edge.inode.id in best_routes_nodes) or (edge.jnode.id in best_routes_nodes):
            edge.savings = {source.id : 0 for source in problem.sources} 
        else:
            edge.savings = {
                source.id : (1.0 - alpha)*dists_norm[inode.id, jnode.id] + alpha* edge.revenue_norm
            for source in problem.sources}

    return problem  

def cut_PJS(problem, source, nodes, depot, alpha = 0.1, beta=0.1, min_vehicle = 0):
    """
    """
    vehicle = problem.vehicles_avaliable[0]
    dists = problem.dists
    nodes = set(nodes)
    is_done = False
    is_done_partial = False

    # Build a dummy solution where a vehicle starts from the source, visit a single node, and then goes to the depot
    routes = collections.deque()
    best_routes_nodes = []
    best_routes =[]

    for node in problem.nodes:
        node.from_source = dists[source.id,node.id]
        node.to_depot = dists[node.id,depot.id]

        while True:

            if (node.dem[0].weight > vehicle.max_weight) or (node.dem[0].volumn > vehicle.max_vol):
                node.update_dem(vehicle.max_weight, vehicle.max_vol, problem)
                route = Route(depot, depot, node)
                routes.append(route)

            else:
                route = Route(depot, depot, node)
                node.route = route
                node.link_left = True
                node.link_right = True
                routes.append(route)
                break

    while True:
        if is_done:
            break

        if len(routes) == min_vehicle:
            is_done = True
            break
        
        elif len(routes) < min_vehicle:
            #print('PROBLEM - MIN_vehicle')
            exit()

        is_done_partial = False
                                    
        set_savings(problem,alpha,best_routes_nodes)
        
        # Filter edges keeping only those that interest this subset of nodes and sort them
        sorted_edges = sorted([e for e in problem.edges], key=lambda edge: edge.savings[depot.id], reverse=True)

        # Merge the routes giving priority to edges with highest efficiency
        for edge in sorted_edges:
            
            if len(routes) == min_vehicle:
                is_done_partial = True
            
            if is_done_partial:
                break

            inode, jnode = edge.inode, edge.jnode
            iroute, jroute = inode.route, jnode.route

            # If the edge connect node already into the same route next edge is considered
            if iroute is None or jroute is None or iroute == jroute:
                continue

            # If inode is the last of its route and jnode the first of its route, the merging is possible.
            if inode.link_right and jnode.link_left:
                # Compare the length of the new route to Tmax and other restriction
                if (iroute.weight + jroute.weight <= vehicle.max_weight) and (iroute.volumn + jroute.volumn <= vehicle.max_vol):
                        # Merge the routes
                        iroute.merge(jroute, edge, dists,depot)
                        # Remove the route incorporated into iroute
                        routes.remove(jroute)

                else:
                    #ESCOLHA DE ROUTE A SER QUEBRADO + QUEBRAR ROUTE SELECIONADO
                    best_route, worst_route = select_best_route(edge)

                    if best_route in best_routes:
                        continue 

                    if best_route.is_full:
                        continue
                    
                    if len(worst_route.nodes) > 1:
                        routes, best_routes_nodes, temp_best_nodes, is_continue, best_route_deleted_id = break_route(worst_route, problem, routes,best_routes_nodes)

                        if is_continue:
                            best_route_deleted_id = []
                            continue
                        
                    for node in best_route.nodes:
                        node.attended = True

                    while True:
                        if best_route.is_full:
                            for node in problem.nodes:
                                node.cut_link_left = True
                                node.cut_link_right = True
                                is_done_partial = True

                            for edge in problem.edges:
                                edge.cut_savings[depot.id] = 0
                            break 
                            
                        partial_partial_fim = False
                        temp_best_nodes = []
                        
                        while True:

                            if partial_partial_fim:
                                break

                            set_cut_saving(problem, best_route, best_routes_nodes, beta, temp_best_nodes)
                            
                            cut_edges = sorted([e for e in problem.edges if e.cut_savings[depot.id]>0], key=lambda edge: edge.cut_savings[depot.id], reverse=True)
                            
                            if cut_edges == [] or cut_edges == None:
                                exit()

                            cut_edge = cut_edges[0]

                            inode, jnode = cut_edge.inode, cut_edge.jnode
                            iroute, jroute = inode.route, jnode.route

                            
                            if best_route.weight == vehicle.max_weight or best_route.volumn == vehicle.max_vol:
                                best_routes.append(best_route)
                                partial_partial_fim = True
                                best_route.is_full = True
                                
                                temp_best_route_nodes = [node for node in list(best_route.nodes) if node.attended == True]
                                
                                for node in temp_best_route_nodes:
                                    best_routes_nodes.append(node.id)

                            
                            elif (inode.cut_link_right and jnode.cut_link_left):
                                if iroute == best_route:
                                    temp_node = jnode
                                    is_iroute = True
                                elif jroute == best_route:
                                    temp_node = inode #copy.deepcopy(inode)
                                    is_iroute = False
                                else:
                                    #print('ERROR TEMP_ROUTE')
                                    #print('inode:{}, jnode:{}'.format(inode,jnode))
                                    exit()
                                
                                if (iroute.weight + jroute.weight > vehicle.max_weight) or (iroute.volumn + jroute.volumn > vehicle.max_vol) or (jroute == best_route and len(iroute.nodes) > 1):
                                    temp_best_route, temp_worst_route = select_best_route(cut_edge)

                                    if temp_best_route in best_routes:
                                        for node in temp_best_route.nodes:
                                            temp_best_nodes.append(node.id)
                                        continue

                                    if temp_worst_route == best_route:
                                        best_route = temp_best_route
                                        break 
                                    
                                    best_route = temp_best_route
                                    worst_route = temp_worst_route

                                    if (len(worst_route.nodes) > 1):
                                        routes, best_routes_nodes, temp_best_nodes,is_continue_cut, best_route_deleted_id = break_route(worst_route, problem, routes,best_routes_nodes,temp_best_nodes)
                                        
                                        if is_continue_cut:
                                            for temp_node in best_route.nodes:
                                                if temp_node.id in best_route_deleted_id:
                                                    routes, best_routes_nodes, temp_best_nodes,is_continue_cut, best_route_deleted_id = break_route(best_route, problem, routes,best_routes_nodes,temp_best_nodes,True  )
                                                    partial_partial_fim = True
                                                    
                                                    return None

                                                    
                                            best_route_deleted_id = []
                                            continue
                                    
                                    iroute, jroute = inode.route, jnode.route
                                    iroute.cut_merge(jroute,cut_edge,dists,depot,best_route,problem)
                                    routes.remove(jroute)

                                    if not(is_iroute) and temp_node.attended:
                                        best_route = iroute
                                    
                                    if not(temp_node.attended):
                                        if is_iroute:
                                            routes.append(temp_node.route)
                                        else:
                                            routes.append(best_route.nodes[1].route)
                                        best_routes.append(best_route)
                                        partial_partial_fim = True
                                        best_route.is_full = True
                                    
                                    temp_best_route_nodes = [node for node in list(best_route.nodes) if node.attended == True]
                                    
                                    for node in temp_best_route_nodes:
                                        best_routes_nodes.append(node.id)
                                                                        
                                else:
                                    iroute.cut_merge(jroute,cut_edge,dists,depot,best_route,problem)
                                    routes.remove(jroute)
                                    inode.attended = True
                                    jnode.attended = True
                                    
                                    if jroute == best_route:
                                        best_route = iroute
                                        
                            else:
                                #print("ERROR - SET_CUT_SAVINGS")
                                #print("{}.{}".format(inode.id,jnode.id))
                                #print("{}.{}".format(inode.cut_link_right,jnode.cut_link_right))
                                exit()
    return sorted(routes, key =operator.attrgetter("cost"), reverse=False)#[:len(vehicles)]

























def calc_min_routes(problem, routes):

    lowest_weight, lowest_volumn = float("inf"), float("inf")

    for route in routes:
        if lowest_weight > route.weight:
            lowest_weight_route = route
        if lowest_volumn > route.volumn:
            lowest_volumn_route = route
        
    if lowest_weight_route != lowest_volumn_route:
        print("ERROR - HÁ DIFERENÇA DE MENOR ROUTE")
        exit()
        
    return lowest_weight_route

def calc_cap_route (problem):
    """"""
    total_weight = 0
    total_volumn = 0
    
    for routes in problem.routes:
        total_weight += routes.weight
        total_volumn += routes.volumn
    
    cap_weight = len(routes)*problem.vehicles_avaliable[0].max_weight - total_weight 
    cap_volumn = len(routes)*problem.vehicles_avaliable[0].max_vol - total_volumn 
    problem.cap_weight = cap_weight
    problem.cap_volumn = cap_volumn

    return cap_weight, cap_volumn

def reverse_PJS(problem, routes): #source, nodes, depot, alpha = 0.1, beta=0.1):
    final_routes = []
    nodes_cut = []
    
    min_routes = calc_min_routes(problem, routes)
    
    for node in min_routes.nodes:
        if node.is_cut:
            nodes_cut.append(node)
    
    #ALTERAR
    #CALCULAR O MIN % ATENDIDO DO NODE POR ROTA - PRIORIZAÇÃO DE CUT_NODE
    #sorted[node] lambda: node.%attended
    sorted_nodes_cut = sorted([node for node in nodes_cut.append], key=lambda node: node.revenue, reverse=True)

    #Calcular capacidade atual da rota
    cap_weight = problem.vehicles_avaliable[0].max_weight - min_routes.weight 
    cap_volumn = problem.vehicles_avaliable[0].max_vol - min_routes.volumn
    
    for node in sorted_nodes_cut:
        #CONSIDERAR APENAS OS PEDIDOS QUE NÃO FORAM ATENDIDO PELO ESSE ROUTE
        if sum(baggage.weight for baggage in node.dem) <= cap_weight and sum(baggage.volumn for baggage in node.dem) <= cap_volumns:
            #como constar o route que foi afetado # fazer uma lista e chamar função para rodar até que não tenha nenhum route afetado
            affected_route = None

    return sorted(final_routes, key = operator.attrgetter("cost"), reverse=False)