import tkinter as tk
from tkinter.font import Font
from tkinter import messagebox

from ..utils.generate_values import open_file, extract_values, display_lines
from ..model.Model import Model
from ..utils.branch_and_bound import solve_branch_and_bound, create_branch_and_bound_tree, visualize_branch_and_bound_tree


def root_screen():
    """
    Tkinter root screen Methode. Erstellt ein Fenster mit
    Frames und allen nötigen labels und buttons.
    """
    def get_model_values():
        """
        Extrahiert die Werte aus der Textdatei und generiert den anzuzeigenden Text.
        Legt die extrahierten Werte für das Modell im root-Fenster ab.
        """
        model_data = extract_values(open_file())
        display_text = "\n".join(display_lines(model_data[0], model_data[1], model_data[2], model_data[3]))
        
        model_label.config(text=display_text)
        
        if submit_button:
            submit_button.pack_forget()
        
        submit_button.pack(pady=10, ipadx=20, ipady=10, padx=10)
        
        root.model_data = model_data
        
        print(model_data)
    
    def submit_model():
        """
        Erzeugt ein Modell-Objekt und löst das Branch-and-Bound-Verfahren, falls das Modell 
        zuvor im root-Fenster abgelegt wurde. Zeigt eine Fehlermeldung, falls kein Modell vorhanden ist.
        """
        if hasattr(root, 'model_data'):
            set_obj, obj_f, constraints, binary_vars = root.model_data
            model_object = Model(set_obj, obj_f, constraints, binary_vars)
            result = solve_branch_and_bound(model_object)
            tree = create_branch_and_bound_tree(model_object)
            visualize_branch_and_bound_tree(tree)
            
        else:
            show_alert()
    
    def show_alert():
        """
        Zeigt eine Fehlermeldung, wenn kein Modell aus der Textdatei erstellt werden konnte.
        """
        messagebox.showinfo("Modell Fehler", "Es konnte kein Modell aus der Textdatei erstellt werden!")

    # tkinter root
    root = tk.Tk()
    root.title("Branch and Bound (LP-Based)")
    
    # Window Konfiguration
    x = root.winfo_screenwidth() // 2
    y = int(root.winfo_screenheight() * 0.1)
    root.geometry('600x600+' + str(x) + '+' + str(y))
    
    # Frames
    frame1 = tk.Frame(root, width=600, height=600, bg="#fff")
    frame1.grid(row=0, column=0)
    frame1.pack_propagate(False)
    
    # Font
    font_style = Font(family="Arial", size=16, weight="bold")
    
    # Titel
    title = tk.Label(frame1, text="Branch & Bound (LP-Based)", font=font_style, bg="#fff")
    title.pack(pady=20)
    
    # Info Text
    text_label = tk.Label(
        frame1,
        text="Bitte stelle eine Textdatei mit einem linearen Modell zur Verfügung.",
        bg="#fff",
        font=("TkMenuFont", 12)
    ).pack(pady=20)
    
    # Button zum triggern der get_model_values Funktion
    button_style = {'bg': 'skyblue', 'fg': 'white', 'borderwidth': 0, 'relief': tk.RIDGE, 'highlightthickness': 0, 'cursor': 'hand2'}
    open_file_button = tk.Button(frame1, text="Modell einfügen", command=get_model_values, font=('Arial', 11, 'bold'), **button_style)
    open_file_button.pack(pady=10, ipadx=20, ipady=10, padx=10)
    
    # Titel Text für Modell Frame
    title_label = tk.Label(frame1, text="eingelesenes Modell", font=('Arial', 12, 'bold'), bg="#fff")
    title_label.pack(pady=10)
    
    # Frame für Modell Text
    model_label_frame = tk.LabelFrame(frame1, bg="#fff", padx=10, pady=10)
    model_label_frame.pack(pady=5, fill="both", expand=True)
    
    # Modell Text
    model_label = tk.Label(model_label_frame, text="", bg="#fff", font=('Times New Roman', 10), wraplength=500, justify="left")
    model_label.pack(fill="both", expand=True)
    
    submit_button = tk.Button(frame1, text="Lösen", command=submit_model, font=('Arial', 11, 'bold'), **button_style)
    
    root.mainloop()
 
 
