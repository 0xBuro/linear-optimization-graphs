import re

class Model:
    def __init__(self, set_obj, obj_f, constraints, binary_vars):
        """
        Initialisiert ein Model-Objekt.

        Parameter:
            set_obj (str): Der Name der Menge im linearen Modell.
            obj_f (str): Die Ziel-/Objective-Funktion des linearen Modells.
            constraints (list): Eine Liste der Constraints (Beschränkungen) des Modells.
            binary_vars (list): Eine Liste der Binärvariablen im Modell.
        """
        self.set_obj = set_obj
        self.obj_f = obj_f
        self.constraints = constraints
        self.binary_vars = binary_vars
    
    def extract_coefficients(self):
        """
        Extrahiert die Koeffizienten aus der Ziel-/Objective-Funktion und den Constraints des Modells.

        Rückgabe:
            tuple: Ein Tupel mit vier Listen: (objective_coefficients, constraint_coefficients, constraint_operators, constraint_last_values).
                - objective_coefficients (list): Eine Liste der Koeffizienten aus der Ziel-/Objective-Funktion.
                - constraint_coefficients (list): Eine Liste der Koeffizienten aus den Constraints.
                - constraint_operators (list): Eine Liste der relationalen Operatoren (<=, >=, ==) aus den Constraints.
                - constraint_last_values (list): Eine Liste der letzten Werte (rechte Seite) aus den Constraints.
        """
        obj_coefficients = re.findall(r'(\d+)\s*\*', self.obj_f)
        objective_coefficients = [int(num) for num in obj_coefficients]
        
        constraint_coefficients = []
        constraint_operators = []
        constraint_last_values = []
        
        for constraint in self.constraints:
            constraint_coeffs = [int(num) for num in re.findall(r'(\d+)\s*\*', constraint)]
            constraint_coefficients.append(constraint_coeffs)
            
            operator = re.findall(r'[<>=]+', constraint)[0]
            constraint_operators.append(operator)
            
            last_value = int(re.findall(r'(\d+)\s*$', constraint)[0])
            constraint_last_values.append(last_value)
        
        return objective_coefficients, constraint_coefficients, constraint_operators, constraint_last_values
