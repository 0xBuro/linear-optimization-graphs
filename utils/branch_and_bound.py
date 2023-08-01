import gurobipy as gp
from gurobipy import GRB
import heapq

import networkx as nx
import matplotlib.pyplot as plt


# Funktion zum Erstellen eines Priority Nodes mit Priorität und Knotendaten
def create_priority_node(priority, node_data):
    """
    Erstellt einen Priority Node mit einer gegebenen Priorität und den Knotendaten.

    Parameters:
        priority (int): Die Priorität des Knotens.
        node_data (dict): Ein Dictionary mit den Knotendaten.

    Returns:
        tuple: Ein Tupel mit der Priorität und den Knotendaten (priority, node_data).
    """
    return (priority, node_data)


# Funktion zum Hinzufügen eines Knotens zur Priority Queue
def add_node_to_priority_queue(pq, node):
    """
    Fügt einen Knoten zur Priority Queue hinzu.

    Parameters:
        pq (list): Die Priority Queue als Heap-Liste.
        node (tuple): Ein Tuple mit der Priorität und den Knotendaten.

    Returns:
        None
    """
    heapq.heappush(pq, node)


# Funktion zum Abrufen des nächsten Knotens aus der Priority Queue
def get_next_node_from_priority_queue(pq):
    """
    Holt den nächsten Knoten aus der Priority Queue.

    Parameters:
        pq (list): Die Priority Queue als Heap-Liste.

    Returns:
        tuple or None: Das nächste Element aus der Priority Queue als Tuple (priority, node_data) oder None, wenn die Queue leer ist.
    """
    if pq:
        return heapq.heappop(pq)
    return None


# Funktion zur Lösung der LP-Relaxation
def lp_relaxation(set_obj, coefficients, operators, last_values, decision_variables):
    """
    Löst die LP-Relaxation des gegebenen Modells und gibt die optimalen Werte der Entscheidungsvariablen zurück.

    Parameters:
        set_obj (str): Das Ziel der Optimierung (entweder "MAXIMIZE" oder "MINIMIZE").
        coefficients (list): Eine Liste von Listen, die die Koeffizienten der Entscheidungsvariablen in den Zielfunktionen und Constraints darstellen.
        operators (list): Eine Liste von Strings, die die Vergleichsoperatoren der Constraints darstellen ("<=", ">=", "==").
        last_values (list): Eine Liste von Zahlen, die die rechte Seite der Constraints darstellen.
        decision_variables (list): Eine Liste von Strings, die die Namen der Entscheidungsvariablen darstellen.

    Returns:
        dict: Ein Dictionary, das die optimalen Werte der Entscheidungsvariablen enthält.
    """
    gp_model = gp.Model("LP_Relaxation")
    gp_model.setParam(GRB.Param.LogToConsole, 0)
    
    vars_dict = {}
    for var_name in decision_variables:
        vars_dict[var_name] = gp_model.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS, name=var_name)
    
    objective_expr = gp.quicksum(coeff * vars_dict[var_name] for coeff_row in coefficients for coeff, var_name in zip(coeff_row, decision_variables))    
    gp_model.setObjective(objective_expr, GRB.MAXIMIZE if set_obj == "MAXIMIZE" else GRB.MINIMIZE)
    
    # Füge die Constraints dynamisch hinzu
    for coeff_row, operator, last_value in zip(coefficients, operators, last_values):
        constraint_expr = gp.quicksum(coeff * vars_dict[var_name] for coeff, var_name in zip(coeff_row, decision_variables))
        if operator == '<=':
            gp_model.addConstr(constraint_expr <= last_value, f"constraint_{len(gp_model.getConstrs())+1}")
        elif operator == '>=':
            gp_model.addConstr(constraint_expr >= last_value, f"constraint_{len(gp_model.getConstrs())+1}")
        elif operator == '==':
            gp_model.addConstr(constraint_expr == last_value, f"constraint_{len(gp_model.getConstrs())+1}")
        else:
            raise ValueError(f"Invalid operator: {operator}")

    # Optimiere das Modell, um die LP-Relaxation Lösung zu finden
    gp_model.optimize()

    if gp_model.Status == GRB.OPTIMAL:
        relaxation = {var_name: var.X for var_name, var in vars_dict.items()}
        return relaxation
    
    
    
# Funktion zur Ermittlung der nächsten Variablen für die Aufteilung (branching)    
def find_next_branch_var(relaxation):
    """
    Ermittelt die nächste Variablen für die Aufteilung (branching) aus der LP-Relaxation Lösung.

    Parameters:
        relaxation (dict): Ein Dictionary, das die optimalen Werte der Entscheidungsvariablen der LP-Relaxation enthält.

    Returns:
        str or None: Der Name der nächsten Aufteilungsvariablen (branching variable) oder None, wenn keine Variable zum Aufteilen gefunden wurde.
    """
    next_branch_var = None
    max_fractional_value = -1
    
    for var_name, var_value in relaxation.items():
        if 0 < var_value < 1 and var_value > max_fractional_value:
            next_branch_var = var_name
            max_fractional_value = var_value
    return next_branch_var        

def generate_root_node(set_obj, objective_coeffs, constraint_coeffs, operators, last_values, binary_vars, branch_var):
    """
    Generiert den Wurzelknoten im Branch-and-Bound-Baum durch Lösen der LP-Relaxation.

    Parameters:
        set_obj (str): Das Ziel der Optimierung (entweder "MAXIMIZE" oder "MINIMIZE").
        objective_coeffs (list): Eine Liste der Koeffizienten der Zielfunktion.
        constraint_coeffs (list): Eine Liste von Listen, die die Koeffizienten der Entscheidungsvariablen in den Constraints darstellen.
        operators (list): Eine Liste von Strings, die die Vergleichsoperatoren der Constraints darstellen ("<=", ">=", "==").
        last_values (list): Eine Liste von Zahlen, die die rechte Seite der Constraints darstellen.
        binary_vars (list): Eine Liste von Strings, die die Namen der binären Entscheidungsvariablen darstellen.
        branch_var (str): Der Name der Variablen, nach der später für die Aufteilung (branching) gesucht wird.

    Returns:
        dict: Ein Dictionary mit den Informationen des Wurzelknotens, einschließlich des optimalen Zielfunktionswerts und der Entscheidungsvariablen.
    """
    gp_model = gp.Model("Node_LP_Relaxation")
    gp_model.setParam(GRB.Param.LogToConsole, 0)
    
    vars_dict = {}
    for var_name in binary_vars:
        if var_name == branch_var:
            # Verwende die Grenzen der nächsten Aufteilungsvariable (branch_var) mit lb=ub, um ihren Wert zu fixieren
            vars_dict[var_name] = gp_model.addVar(lb=0, ub=1, vtype=GRB.BINARY, name=var_name)
        else:
            vars_dict[var_name] = gp_model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=var_name)

    # Setze die Zielfunktion dynamisch
    objective_expr = gp.quicksum(coeff * vars_dict[var_name] for coeff, var_name in zip(objective_coeffs, binary_vars))    
    gp_model.setObjective(objective_expr, GRB.MAXIMIZE if set_obj == "MAXIMIZE" else GRB.MINIMIZE)
    
    # Füge die Constraints dynamisch hinzu
    for coeff_row, operator, last_value in zip(constraint_coeffs, operators, last_values):
        constraint_expr = gp.quicksum(coeff * vars_dict[var_name] for coeff, var_name in zip(coeff_row, binary_vars))
        if operator == '<=':
            gp_model.addConstr(constraint_expr <= last_value, f"constraint_{len(gp_model.getConstrs())+1}")
        elif operator == '>=':
            gp_model.addConstr(constraint_expr >= last_value, f"constraint_{len(gp_model.getConstrs())+1}")
        elif operator == '==':
            gp_model.addConstr(constraint_expr == last_value, f"constraint_{len(gp_model.getConstrs())+1}")
        else:
            raise ValueError(f"Invalid operator: {operator}")

        # Optimiere das Modell, um die LP-Relaxation Lösung zu finden
    gp_model.optimize()
    
    node = {}
    if gp_model.Status == GRB.OPTIMAL:
        # Erhalte die LP-Relaxation Lösung
        node_solution = {var_name: var.X for var_name, var in vars_dict.items()}
        # Erhalte den optimalen Zielfunktionswert und runde ihn auf zwei Dezimalstellen
        optimal_value = round(gp_model.ObjVal, 2)

        # Speichere die Informationen im Knoten-Dictionary
        node['optimal_objective'] = optimal_value
        node['decision_vars'] = node_solution
    else:
        node["optimal_objective"] = "infeasible"
        node['decision_vars'] =  "infeasible"
        
    return node



# Funktionen zur Generierung der Kindknoten (linkes und rechtes Kind) für die Aufteilung (branching)    
def generate_left_child_node(model, objective_coeffs, constraint_coeffs, operators, last_values, binary_vars, branch_var, root_decision_vars):
    """
    Generiert den linken Kindknoten (left child node) für die Aufteilung (branching) im Branch-and-Bound-Baum.

    Parameters:
        model (GurobiModel): Das Gurobi-Modell für den Wurzelknoten.
        objective_coeffs (list): Eine Liste der Koeffizienten der Zielfunktion.
        constraint_coeffs (list): Eine Liste von Listen, die die Koeffizienten der Entscheidungsvariablen in den Constraints darstellen.
        operators (list): Eine Liste von Strings, die die Vergleichsoperatoren der Constraints darstellen ("<=", ">=", "==").
        last_values (list): Eine Liste von Zahlen, die die rechte Seite der Constraints darstellen.
        binary_vars (list): Eine Liste von Strings, die die Namen der binären Entscheidungsvariablen darstellen.
        branch_var (str): Der Name der Variablen, nach der später für die Aufteilung (branching) gesucht wird.
        root_decision_vars (dict): Ein Dictionary, das die optimalen Werte der Entscheidungsvariablen des Wurzelknotens enthält.

    Returns:
        dict: Ein Dictionary mit den Informationen des linken Kindknotens, einschließlich des optimalen Zielfunktionswerts und der Entscheidungsvariablen.
    """
    gp_model = gp.Model("Node_LP_Relaxation")
    gp_model.setParam(GRB.Param.LogToConsole, 0)

    vars_dict = {}
    for var_name in binary_vars:
        if var_name == branch_var:
            # Überprüfe den Wert im Wurzelknoten
            root_var_value = root_decision_vars.get(var_name, None)
            if root_var_value is None or 0 <= root_var_value <= 1:
                # Wenn der Wert nicht ganzzahlig ist (0 <= Wert <= 1), setze ihn als binäre Variable mit lb=1, ub=1
                vars_dict[var_name] = gp_model.addVar(lb=1, ub=1, vtype=GRB.BINARY, name=var_name)
            elif root_var_value == 1:
                # Wenn der Wert 1 ist, setze ihn als kontinuierliche Variable mit lb=1, ub=1
                vars_dict[var_name] = gp_model.addVar(lb=1, ub=1, vtype=GRB.BINARY, name=var_name)
            elif root_var_value == 0:
                # Wenn der Wert 0 ist, setze ihn als binäre Variable mit lb=0, ub=0
                vars_dict[var_name] = gp_model.addVar(lb=0, ub=0, vtype=GRB.BINARY, name=var_name)
            else:
                raise ValueError(f"Invalid value for {var_name} in root_decision_vars.")
        else:
            vars_dict[var_name] = gp_model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=var_name)

    objective_expr = gp.quicksum(coeff * vars_dict[var_name] for coeff, var_name in zip(objective_coeffs, binary_vars))
    gp_model.setObjective(objective_expr, GRB.MAXIMIZE if model.set_obj == "MAXIMIZE" else GRB.MINIMIZE)

    for coeff_row, operator, last_value in zip(constraint_coeffs, operators, last_values):
        constraint_expr = gp.quicksum(coeff * vars_dict[var_name] for coeff, var_name in zip(coeff_row, binary_vars))
        if operator == '<=':
            gp_model.addConstr(constraint_expr <= last_value, f"constraint_{len(gp_model.getConstrs()) + 1}")
        elif operator == '>=':
            gp_model.addConstr(constraint_expr >= last_value, f"constraint_{len(gp_model.getConstrs()) + 1}")
        elif operator == '==':
            gp_model.addConstr(constraint_expr == last_value, f"constraint_{len(gp_model.getConstrs()) + 1}")
        else:
            raise ValueError(f"Invalid operator: {operator}")

    gp_model.optimize()

    node = {}
    if gp_model.Status == GRB.OPTIMAL:
        node_solution = {var_name: var.X for var_name, var in vars_dict.items()}
        optimal_value = round(gp_model.ObjVal, 2)

        node['optimal_objective'] = optimal_value
        node['decision_vars'] = node_solution
    else:
        node["optimal_objective"] = "infeasible"
        node['decision_vars'] =  "infeasible"

    return node

def generate_right_child_node(model, objective_coeffs, constraint_coeffs, operators, last_values, binary_vars, branch_var, root_decision_vars):
    """
    Generiert den rechten Kindknoten (right child node) für die Aufteilung (branching) im Branch-and-Bound-Baum.

    Parameters:
        model (GurobiModel): Das Gurobi-Modell für den Wurzelknoten.
        objective_coeffs (list): Eine Liste der Koeffizienten der Zielfunktion.
        constraint_coeffs (list): Eine Liste von Listen, die die Koeffizienten der Entscheidungsvariablen in den Constraints darstellen.
        operators (list): Eine Liste von Strings, die die Vergleichsoperatoren der Constraints darstellen ("<=", ">=", "==").
        last_values (list): Eine Liste von Zahlen, die die rechte Seite der Constraints darstellen.
        binary_vars (list): Eine Liste von Strings, die die Namen der binären Entscheidungsvariablen darstellen.
        branch_var (str): Der Name der Variablen, nach der später für die Aufteilung (branching) gesucht wird.
        root_decision_vars (dict): Ein Dictionary, das die optimalen Werte der Entscheidungsvariablen des Wurzelknotens enthält.

    Returns:
        dict: Ein Dictionary mit den Informationen des rechten Kindknotens, einschließlich des optimalen Zielfunktionswerts und der Entscheidungsvariablen.
    """
    gp_model = gp.Model("Node_LP_Relaxation")
    gp_model.setParam(GRB.Param.LogToConsole, 0)

    vars_dict = {}
    for var_name in binary_vars:
        if var_name == branch_var:
            root_var_value = root_decision_vars.get(var_name, None)
            if root_var_value is None or 0 <= root_var_value <= 1:
                vars_dict[var_name] = gp_model.addVar(lb=0, ub=0, vtype=GRB.BINARY, name=var_name)
            elif root_var_value == 1:
                # Wenn 1, setzen als kontinuierliche Variable mit 0,0 für lb, ub
                vars_dict[var_name] = gp_model.addVar(lb=0, ub=0, vtype=GRB.CONTINUOUS, name=var_name)
            elif root_var_value == 0:
                # Wenn 0, setzen als binäre Variable 1
                vars_dict[var_name] = gp_model.addVar(lb=1, ub=1, vtype=GRB.BINARY, name=var_name)
            else:
                raise ValueError(f"Invalid value for {var_name} in root_decision_vars.")
        else:
            vars_dict[var_name] = gp_model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=var_name)
            

    objective_expr = gp.quicksum(coeff * vars_dict[var_name] for coeff, var_name in zip(objective_coeffs, binary_vars))
    gp_model.setObjective(objective_expr, GRB.MAXIMIZE if model.set_obj == "MAXIMIZE" else GRB.MINIMIZE)

    for coeff_row, operator, last_value in zip(constraint_coeffs, operators, last_values):
        constraint_expr = gp.quicksum(coeff * vars_dict[var_name] for coeff, var_name in zip(coeff_row, binary_vars))
        if operator == '<=':
            gp_model.addConstr(constraint_expr <= last_value, f"constraint_{len(gp_model.getConstrs()) + 1}")
        elif operator == '>=':
            gp_model.addConstr(constraint_expr >= last_value, f"constraint_{len(gp_model.getConstrs()) + 1}")
        elif operator == '==':
            gp_model.addConstr(constraint_expr == last_value, f"constraint_{len(gp_model.getConstrs()) + 1}")
        else:
            raise ValueError(f"Invalid operator: {operator}")

    gp_model.optimize()

    node = {}
    if gp_model.Status == GRB.OPTIMAL:
        node_solution = {var_name: var.X for var_name, var in vars_dict.items()}
        optimal_value = round(gp_model.ObjVal, 2)

        node['optimal_objective'] = optimal_value
        node['decision_vars'] = node_solution
    else:
        node["optimal_objective"] = "infeasible"
        node['decision_vars'] =  "infeasible"

    return node


def generate_child_nodes(model, decision_vars, next_branch_var, root_node_vars):
    """
    Generiert die Kindknoten (links und rechts) für die Aufteilung (branching) im Branch-and-Bound-Baum.

    Parameters:
        model (GurobiModel): Das Gurobi-Modell für den Wurzelknoten.
        decision_vars (list): Eine Liste der Entscheidungsvariablen des aktuellen Knotens.
        next_branch_var (str): Der Name der Variablen, nach der für die Aufteilung (branching) gesucht wird.
        root_node_vars (dict): Ein Dictionary, das die optimalen Werte der Entscheidungsvariablen des Wurzelknotens enthält.

    Returns:
        tuple: Ein Tupel mit den Informationen des linken und rechten Kindknotens, jeweils als Dictionarys, einschließlich des optimalen Zielfunktionswerts und der Entscheidungsvariablen.
    """
    objective_coeffs, constraint_coeffs, operators, last_values = model.extract_coefficients()
    left_child_node = generate_left_child_node(model, objective_coeffs, constraint_coeffs, operators, last_values, decision_vars, next_branch_var, root_node_vars)
    right_child_node = generate_right_child_node(model, objective_coeffs, constraint_coeffs, operators, last_values, decision_vars, next_branch_var, root_node_vars)
    
    return left_child_node, right_child_node

def all_binary_check(current_vars):
    """
    Überprüft, ob alle Werte in der gegebenen Entscheidungsvariablen-Datenstruktur binär sind (0 oder 1).

    Parameters:
        current_vars (dict): Ein Dictionary mit den Entscheidungsvariablen und ihren Werten.

    Returns:
        bool: True, wenn alle Werte binär sind, andernfalls False.
    """
    for value in current_vars.values():
        if not (value == 0 or value == 1):
            return False
    return True

def solve_branch_and_bound(model):
    """
    Löst das Branch-and-Bound-Verfahren, um das optimale Ergebnis für das gegebene Modell zu finden.

    Parameters:
        model (GurobiModel): Das Gurobi-Modell, das gelöst werden soll.

    Returns:
        set: Ein Set mit den besuchten Knoten (darunter die Entscheidungsvariablen) im Branch-and-Bound-Baum.
    """
    node_list = []  # Liste zum Speichern der Knoten
    visited_nodes = set()  # Set zum Speichern der besuchten Knoten

    objective_coeffs, constraint_coeffs, operators, last_values = model.extract_coefficients()
    relaxation = lp_relaxation(model.set_obj, constraint_coeffs, operators, last_values, model.binary_vars)
    next_branch_var = find_next_branch_var(relaxation)

    root_node = generate_root_node(model.set_obj, objective_coeffs, constraint_coeffs, operators, last_values, model.binary_vars, next_branch_var)

    current_node_vars = root_node['decision_vars']

    print("root node")
    print(f"Optimal Objective Value: {root_node['optimal_objective']}")
    print("Decision Variables:")
    for var_name, var_value in root_node['decision_vars'].items():
        print(f"{var_name}: {var_value}")
    print("-------------------")

    node_list.append((root_node, current_node_vars))  # Speichern des Wurzelknoten mit Entscheidungsvariablen
    visited_nodes.add(tuple(root_node['decision_vars'].items()))  # Markiere Wurzelknoten als besucht

    while node_list:
        current_node, current_node_vars = node_list.pop(0)  # Untersuchen der nodes in richtiger Reihenfolge

        # Linken und rechten Kindknoten erstellen
        decision_vars = current_node['decision_vars']
        next_branch_var = find_next_branch_var(decision_vars)
        left_child_node, right_child_node = generate_child_nodes(model, decision_vars, next_branch_var, current_node_vars)

        # Falls noch nicht besucht, Kindknoten zur node_list hinzufügen
        if left_child_node and tuple(left_child_node['decision_vars'].items()) not in visited_nodes:
            node_list.append((left_child_node, current_node_vars))
            visited_nodes.add(tuple(left_child_node['decision_vars'].items()))  # Knoten besucht
            print(f"left child node:")
            print(f"Optimal Objective Value: {left_child_node['optimal_objective']}")
            print("Decision Variables:")
            for var_name, var_value in left_child_node['decision_vars'].items():
                print(f"{var_name}: {var_value}")
            print("-------------------")

        if right_child_node and tuple(right_child_node['decision_vars'].items()) not in visited_nodes:
            node_list.append((right_child_node, right_child_node['decision_vars'])) 
            visited_nodes.add(tuple(right_child_node['decision_vars'].items()))  # Knoten besucht
            print(f"right child node:")
            print(f"Optimal Objective Value: {right_child_node['optimal_objective']}")
            print("Decision Variables:")
            for var_name, var_value in right_child_node['decision_vars'].items():
                print(f"{var_name}: {var_value}")
            print("-------------------")

    return visited_nodes 

def create_branch_and_bound_tree(model):
    """
    Erstellt den Branch-and-Bound-Baum für das gegebene Modell und gibt ihn als gerichteten Graphen (DiGraph) zurück.

    Parameters:
        model (GurobiModel): Das Gurobi-Modell, für das der Branch-and-Bound-Baum erstellt werden soll.

    Returns:
        nx.DiGraph: Ein gerichteter Graph (DiGraph) als Darstellung des Branch-and-Bound-Baums.
    """
    graph = nx.DiGraph()

    node_list = []
    visited_nodes = set()

    objective_coeffs, constraint_coeffs, operators, last_values = model.extract_coefficients()
    relaxation = lp_relaxation(model.set_obj, constraint_coeffs, operators, last_values, model.binary_vars)
    next_branch_var = find_next_branch_var(relaxation)

    root_node = generate_root_node(model.set_obj, objective_coeffs, constraint_coeffs, operators, last_values, model.binary_vars, next_branch_var)
    current_node_vars = root_node['decision_vars'] 
    optimal_objective = root_node['optimal_objective']  

     # Speichern von optimal_objective im node Attribut
    graph.add_node(tuple(current_node_vars.items()), optimal_objective=optimal_objective)

    node_list.append((root_node, current_node_vars, "root"))
    visited_nodes.add(tuple(current_node_vars.items()))

    while node_list:
        current_node, current_node_vars, node_type = node_list.pop(0)

        decision_vars = current_node['decision_vars']
        next_branch_var = find_next_branch_var(decision_vars)
        left_child_node, right_child_node = generate_child_nodes(model, decision_vars, next_branch_var, current_node_vars)

        if left_child_node:
            left_child_vars = left_child_node['decision_vars']
            left_child_optimal_obj = left_child_node['optimal_objective']
            graph.add_node(tuple(left_child_vars.items()), optimal_objective=left_child_optimal_obj)
            graph.add_edge(tuple(current_node_vars.items()), tuple(left_child_vars.items()))

            if tuple(left_child_vars.items()) not in visited_nodes:
                node_list.append((left_child_node, current_node_vars, "left"))
                visited_nodes.add(tuple(left_child_vars.items()))

        if right_child_node:
            right_child_vars = right_child_node['decision_vars']
            right_child_optimal_obj = right_child_node['optimal_objective']
            graph.add_node(tuple(right_child_vars.items()), optimal_objective=right_child_optimal_obj)
            graph.add_edge(tuple(current_node_vars.items()), tuple(right_child_vars.items()))

            if tuple(right_child_vars.items()) not in visited_nodes:
                node_list.append((right_child_node, right_child_node['decision_vars'], "right"))
                visited_nodes.add(tuple(right_child_vars.items()))

    return graph

def visualize_branch_and_bound_tree(tree):
    """
    Visualisiert den gegebenen Branch-and-Bound-Baum (gerichteter Graph) mit den optimalen Zielfunktionswerten und Entscheidungsvariablen.

    Parameters:
        tree (nx.DiGraph): Ein gerichteter Graph (DiGraph) als Darstellung des Branch-and-Bound-Baums.

    Returns:
        None
    """
    plt.figure(figsize=(12, 8))
    pos = nx.nx_pydot.graphviz_layout(tree, prog='dot')

    # Ausgabe Knoten-labels mit decision_vars und optimal_objective
    node_labels = {}
    for node, data in tree.nodes(data=True):
        optimal_objective = data.get('optimal_objective', 'N/A')
        decision_vars = data.get('decision_vars', {})
        decision_vars_str = "\n".join([f"{var_name}: {var_value}" for var_name, var_value in decision_vars.items()])
        node_labels[node] = f"Objective: {optimal_objective}\n{decision_vars_str}"

    nx.draw(tree, pos, with_labels=True, labels=node_labels, node_size=1000, node_color="skyblue", font_size=10, font_weight='bold', arrowsize=12)
    plt.title("Branch and Bound Tree")
    plt.show()
