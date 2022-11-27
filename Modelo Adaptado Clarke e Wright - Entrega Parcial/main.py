import os
import time
import functools
import copy

import utils
#import iterators
import solver
import cut_solver
#from mapper import mapper
#from pjs import PJS

if __name__ == "__main__":


    problem = utils.read_problem("clientes.xlsx",'Carac veiculo.xlsx','produto.xlsx')

    temp_problem = copy.deepcopy(problem)
    alpha, best_cost = solver.alpha_optimisation(temp_problem)
    
    temp_problem = copy.deepcopy(problem)
    solver.set_savings(temp_problem, alpha=alpha)
    _start = time.time()
    costs,routes = solver.heuristic(temp_problem, alpha)  

    print('-------------------------MÉTODO TRADICIONAL-------------------------')
    print('TEMPO DE EXECUÇÃO: {}'.format(time.time() - _start))
    for r in routes:
      print(r.nodes)
    print('CUSTO TOTAL:{}'.format(costs))

    

    if cut_solver.check_cut(problem,routes):
        temp_problem = copy.deepcopy(problem)
        cut_alpha, cut_beta, best_cost = cut_solver.alpha_optimisation(temp_problem)

        temp_problem = copy.deepcopy(problem)
        cut_solver.set_savings(temp_problem, alpha = cut_alpha)

        _start = time.time()
        cut_costs,cut_routes = cut_solver.heuristic(temp_problem, cut_alpha, cut_beta)

        print()
        print('-------------------------MÉTODO ADAPTADO-------------------------')
        print('TEMPO DE EXECUÇÃO: {}'.format(time.time() - _start))
        for r in cut_routes:
          print(r.nodes)
        print('CUSTO TOTAL:{}'.format(cut_costs))
