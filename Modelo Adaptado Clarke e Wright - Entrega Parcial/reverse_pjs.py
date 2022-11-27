import collections
import copy
import operator
from pickle import TRUE

from sqlalchemy import false, true
from sympy import N, principal_branch


def find_duplicated(nodes):
    length = len(nodes)
    duplicates_nodes = []
    
    for i in range(length):
        n = i+1

        for a in range(n,length):
            if nodes[i] == nodes[a] and nodes[i] not in duplicates_nodes:
                duplicates_nodes.append(nodes[i])

    return duplicates_nodes

def sort_nodes_full (problem, min_route, duplicated_nodes):
    nodes_full = []

    for node in min_route.nodes:
        node.dem[0].delta_qtd = 0

        if node in duplicated_nodes: #pode ser que não funcione por compara entre Class
            node.dem[0].delta_qtd = node.dem[0].invisible_qtd - node.dem[0].qtd
            nodes_full.append(node)

    sorted_nodes_full = sorted([node for node in nodes_full], key=lambda node:node.dem[0].delta_qtd, reverse = True)
    
    return sorted_nodes_full

def reverse_pjs(problem, routes, nodes):
    nodes_attended = collections.deque()
    min_route = None
    routes_affeted = []
    vehicle = problem.vehicles_avaliable[0]
    
    for route in routes:
        nodes_attended.extend(route.nodes)

        if route.is_full == False:  
            min_route = route  
    
    node_affected = []
    is_done = False
    
    duplicated_nodes = find_duplicated(nodes_attended)

    sorted_nodes_full = sort_nodes_full(problem, min_route, duplicated_nodes)

    
    node_affected_id = []
    node_full_affected_id = []
    node_partial_affected_id = []

    for i in range(len(sorted_nodes_full)):
        if is_done:
            break

        for node in min_route.nodes: 
            if is_done:
                break

            if node == sorted_nodes_full[i]:
                min_route.weight -= node.dem[0].weight 
                min_route.volumn -= node.dem[0].volumn

                node_affected.append(node)
                node_affected_id.append(node.id)

                node.reupdate_dem(problem)

                #Verificar o máximo cap de node 
                if min_route.weight + node.dem[0].weight <= vehicle.max_weight and min_route.volumn + node.dem[0].volumn <= vehicle.max_vol:
                    min_route.weight += node.dem[0].weight
                    min_route.volumn += node.dem[0].volumn
                    node_full_affected_id.append(node.id)
                    node.attended = True

                else:
                    cap_weight = vehicle.max_weight - min_route.weight
                    cap_volumn = vehicle.max_vol - min_route.volumn

                    node_weight = copy.deepcopy(node.dem[0].weight)
                    node_volumn = copy.deepcopy(node.dem[0].volumn)

                    node.update_dem(cap_weight, cap_volumn, problem)

                    min_route.weight += (node_weight - node.dem[0].weight)
                    min_route.volumn += (node_volumn - node.dem[0].volumn)

                    node.attended = False
                    is_done = True #to finish min_route loop

                    node_partial_affected_id.append(node.id)

    
    #procurando os routes que foram afetados pela alteração do min_route
    dists = problem.dists
    depot = problem.depot

    while True:

        if node_affected_id == []:
            break

        routes_affeted = []    
        
        for route in routes:
            if route == min_route:
                continue
            else:
                for node in route.nodes:
                    if node.id in node_affected_id and route not in routes_affeted:
                        routes_affeted.append(route)

        min_route = None 

        for route in routes_affeted:
            nodes_to_remove = []

            for node in route.nodes:
                if node.id in node_full_affected_id:
                    nodes_to_remove.append(node) 

                elif node.id in node_partial_affected_id:
                    route.update_route_weight_volumn() 
                    
            for node in nodes_to_remove:
                if node in route.nodes:
                    route.nodes.remove(node)
                    route.update_route_weight_volumn()

            #Verificar quais nodes não estão atendidos apenas pela 1 visita
            for node in route.nodes:
                node.full_attended(problem) 
                
            cap_weight = vehicle.max_weight - route.weight
            cap_volumn = vehicle.max_vol - route.volumn
            
        node_full_affected_id_sec = []
        node_partial_affected_id_sec = []
        node_affected_id_sec = []
        node_affected_sec = []

        for route in routes_affeted:
            for node in route.nodes:
                if not(node.attended) and (node not in node_affected):
                    if route.weight + node.dem[0].weight <= vehicle.max_weight and route.volumn + node.dem[0].volumn <= vehicle.max_vol:
                        node_full_affected_id_sec.append(node.id)
                        node_affected_id_sec.append(node.id)
                        node_affected_sec.append(node)
                        node.reupdate_dem(problem)
                        node.attended = True
                    else:
                        node_partial_affected_id_sec.append(node.id)
                        node_affected_id_sec.append(node.id)
                        node_affected_sec.append(node)
                        node.update_dem_reverse(cap_weight, cap_volumn, problem)
            
            route.weight = 0
            route.volumn = 0
            for node in route.nodes:
                route.weight += sum(baggage.weight for baggage in node.dem if node.attended)
                route.volumn += sum(baggage.volumn for baggage in node.dem if node.attended)
            
            min_route = route
        
        node_full_affected_id = node_full_affected_id_sec
        node_partial_affected_id = node_partial_affected_id_sec
        node_affected_id = node_affected_id_sec
        node_affected = node_affected_sec


    #Recalcular os savings e costs
    for route in routes:
        first_node_id = route.nodes[0].id
        last_node_id = route.nodes[-1].id
        route.cost = dists[depot.id,first_node_id] + dists[depot.id,last_node_id] 


        for i in range(len(route.nodes)-1):
            inode_id = route.nodes[i].id
            jnode_id = route.nodes[i+1].id
            route.cost += dists[inode_id,jnode_id]


    return routes