from tkinter import filedialog

def open_file():
    """
    liest eine Textdatei ein und returnt 
    die zeilenweise Ausgabe in content.
    """
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, 'r') as file:
            content = file.readlines()
        
        if content:
            return content
            
def extract_values(content):
    """
    extrahiert die Zeilen aus dem gegebenen content und
    legt die rohen Werte in entsprechende Variablen oder Listen ab.
    returnt result mit den für das Modell benötigten Variablen.
    """
    setObj = None
    obj_f = None
    constraints = []
    binary_vars = []
    
    # Ziel (Maximieren, Minimieren) auslesen
    if content:
        setObj = content[0].strip()
    
    # Zielfunktion/Objective Function Z auslesen
    if len(content) > 1:
        obj_f = content[1].strip()
        
    # Einschränkungen auslesen  
    if len(content) > 2:  
        constraints = [line.strip() for line in content[2:-1] for line in line.split(",")]
    else:
        constraints = [line.strip() for line in content[2:-1]]    
    
    # Entscheidungsvariablen auslesen
    if content:
        last_line_values = content[-1].strip().split(',')
        binary_vars = [value.strip() for value in last_line_values]
    
    result = setObj, obj_f, constraints, binary_vars
    return result


def display_lines(setObj, obj_f, constraints, binary_vars):
    """
    Zeilenweise Ausgabe der Werte in display_text
    für Anzeige auf der graphischen Oberfläche/Frame
    return display_text.
    """
    if setObj == "MAXIMIZE":
        setObj_text = "max"
    else:
        setObj_text = "min"
    setObj_text += " " + obj_f + "\n"     
    
    constraints_text = "s.t \n"
    constraints_text += ", \n".join(constraints) + "\n"     
    
    variables_text = ", ".join(binary_vars) + " = 1 or 0"
        
    display_text = [setObj_text, constraints_text, variables_text]


    return display_text
    