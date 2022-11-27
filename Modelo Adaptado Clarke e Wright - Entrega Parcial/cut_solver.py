import numpy as np
import random
import functools
import collections
from pjs import PJS, cut_PJS
from reverse_pjs import reverse_pjs
from math import ceil
import copy

def calc_min_vehicle(problem):
    """
    """
    total_weight, total_volumn = 0,0

    #Import total weight and volumns of all nodes
    for node in problem.nodes:
        for baggage in node.dem:
            total_weight += baggage.weight
            total_volumn += baggage.volumn

    #Import vehicle's data
    n_vehicle_weight = total_weight/problem.vehicles_avaliable[0].max_weight
    n_vehicle_volumn = total_volumn/problem.vehicles_avaliable[0].max_vol
    min_vehicle = max(n_vehicle_weight,n_vehicle_volumn)

    return ceil(min_vehicle)


def check_cut(problem,routes):

    min_vehicle = calc_min_vehicle(problem)
    
    #VERIFICAR SE REALMENTE NÃO É NECESSÁRIO O CORTE
    if min_vehicle < len(routes):
        return True
    return False


#CALCULAR OUTRO SET_SAVING PARA CORTE CONSIDERANDO % QUE FOI ATENDIDO
def set_savings (problem, alpha = 0.1):
    """
    This method calculate the saving of edges #ACCORDING TO THE GIVEN ALPHA
    
    :param problem: The instance of the problem to solve
    :param alpha: The alpha parameter of the PJS
    :return: The problem instance modified in place
    """
    dists_norm, depot = problem.dists_norm, problem.depot

    for edge in problem.edges:
        cost, inode, jnode = edge.cost, edge.inode, edge.jnode
        edge.savings = {
            source.id : (1.0 - alpha)*dists_norm[inode.id, jnode.id] + alpha* edge.revenue_norm
        for source in problem.sources}

    return problem  
    

def alpha_optimisation (problem, alpha_range = np.arange(0.1, 1.0, 0.1), beta_range= np.arange(0.1, 1.0, 0.1)):
    """
    """
    #ALTERAR SE DEPOT FOR DIFERENTE DO SOURCE
    dists, depot, sources, nodes = problem.dists, problem.depot, problem.sources, problem.nodes

    # Initialise the best cost to infinity and best_alpha to zero
    best_alpha, best_beta, best_cost = 0.0, 0.0, float("inf")


    for alphatest in alpha_range:

        #Tray a new value of alpha
        alphatest = round(alphatest,1)

        # Compute the edges savings
        set_savings(problem, alphatest)
        
        # Sort vehicles according cost-benefit rules - VERIFICAR RULES

        # Run a deterministic version of the PJS algorithm
        #For source in problem.sources:

        for betatest in beta_range:
            routes = []
            #alphatest,betatest = 0.3, 0.1

            betatest = round(betatest,1)
            bug = False
            temp_problem = copy.deepcopy(problem)
            
            for source in sources:
                try:
                    partial_routes = cut_PJS(temp_problem, source, tuple(nodes) ,depot, alphatest, betatest, calc_min_vehicle(problem))

                    if partial_routes == None:
                        bug = True
                        break

                    temp_problem = copy.deepcopy(problem)
                    partial_routes = reverse_pjs(temp_problem, partial_routes, tuple(temp_problem.nodes))

                except:
                    bug  = True
                    continue

                routes.extend(partial_routes)
            total_cost = sum(route.cost for route in routes)
        
            if total_cost < best_cost and not(bug):
                best_alpha, best_beta, best_cost = alphatest, betatest, total_cost
        
    total_cost = sum(route.cost for route in routes)

    #Set the saving of the edges by using the best found alpha
    set_savings(problem,best_alpha)

    #Return the best alpha and best_costobtained
    return best_alpha, best_beta, best_cost

def heuristic (problem, alpha, beta):
    """
    This is the main executiom of the solver.
    It can be deterministic of stochastic depending on the iterator
    passed as argument.

    :param problem: The problem instance to solve.
    :param iterator: The iterator to be passed to the mapper.
    :param alpha: The alpha value used to calculate edges savings (used only for caching)
    :return: The solution as a set of routes, their total revenue, the mapping represented a matrix.
    """
    routes = []

    temp_problem = copy.deepcopy(problem)

    for source in problem.sources:
        route = cut_PJS(problem, source, tuple(problem.nodes), problem.depot, alpha, beta, calc_min_vehicle(problem))        
        route = reverse_pjs(temp_problem, route, tuple(temp_problem.nodes))
        routes.extend(route)

    #Calculate total revenue
    costs = sum(r.cost for r in routes)

    return costs, tuple(routes)


