from imagInfo import ImageMetadataViewer
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

def main():
    root = TkinterDnD.Tk()
    app = ImageMetadataViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
