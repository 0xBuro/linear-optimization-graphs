"""
Startpunkt des Programms mit modularer/packetbasierter Projekt-Struktur.
Mit dem Befehl "python -m bnbPy" im Root-Verzeichnis kann die 
Main-Methode aufgerufen werden. 
"""
from .screen.root_screen import root_screen

def main():
    root_screen()

if __name__ == '__main__':
    main()