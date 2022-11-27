import numpy as np
import random
import functools
import collections
from pjs import PJS, cut_PJS



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



def alpha_optimisation (problem, alpha_range = np.arange(0.0, 1.1, 0.1)):
    """
    """
    #ALTERAR SE DEPOT FOR DIFERENTE DO SOURCE
    dists, depot, sources, nodes = problem.dists, problem.depot, problem.sources, problem.nodes

    # Initialise the best cost to infinity and best_alpha to zero
    best_alpha, best_cost = 0.0, float("inf")

    for alphatest in alpha_range:

        #Tray a new value of alpha
        alphatest = round(alphatest,1)

        # Compute the edges savings
        set_savings(problem, alphatest)
        
        # Sort vehicles according cost-benefit rules - VERIFICAR RULES

        # Run a deterministic version of the PJS algorithm
        #For source in problem.sources:
        routes = []
    
        for source in sources:
            partial_routes = PJS(problem, source, tuple(problem.nodes) ,depot, alphatest) # add vehicles param
            routes.extend(partial_routes)

        # Total cost -A ACRESCENTAR OTIF POR QTD
        total_cost = sum(route.cost for route in routes)

        if total_cost < best_cost:
            best_alpha, best_cost = alphatest, total_cost

    #Set the sabing of the edges by using the best found alpha
    set_savings(problem,best_alpha)

    #Return the best alpha and best_costobtained
    return best_alpha, best_cost

def heuristic (problem, alpha):
    """
    This is the main executiom of the solver.
    It can be deterministic of stochastic depending on the iterator
    passed as argument.

    :param problem: The problem instance to solve.
    :param iterator: The iterator to be passed to the mapper.
    :param alpha: The alpha value used to calculate edges savings (used only for caching)
    :return: The solution as a set of routes, their total revenue, the mapping represented a matrix.
    """

    #MAPPING - A VERIFICAR
    #mapping = mapper(problem, iterator)

    #PJS on routes
    routes = []

    for source in problem.sources:
        route = PJS(problem, source, tuple(problem.nodes), problem.depot, alpha)
        routes.extend(route)

    #Calculate total revenue
    costs = sum(r.cost for r in routes)

    return costs, tuple(routes)

