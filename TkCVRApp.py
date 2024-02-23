#!/usr/bin/python

import os
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext
from pathlib import Path

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Read CVRs - Export To CSV")

        self.geometry("500x400")

        self.folder_path = None
        self.folder_chooser = tk.Button(self, text="Choose CVRs Folder", command=self.choose_folder)
        self.folder_chooser.pack(pady=10)

        self.folder_path_label = tk.Label(self, text="No folder selected")
        self.folder_path_label.pack(pady=10)

        self.btn = tk.Button(self, text="Start Process", command=self.start_process)
        self.btn.pack(pady=10)
        # disable button to start
        self.btn.config(state="disabled")

        self.log_area = scrolledtext.ScrolledText(self, height=30, width=80, wrap="word")
        self.log_area.pack(pady=20)

    def choose_folder(self):
        # open a file dialog to choose a folder
        folder = tk.filedialog.askdirectory()

        self.folder_path = folder
        if self.folder_path:
            self.btn.config(state="normal")
            self.folder_path_label.config(text="Folder Selected: " + self.folder_path)
        else:
            self.btn.config(state="disabled")

    def test_run_process(self):
        start_process(True)

    def start_process(self, test_run=False):
        file_limit = test_run and "100" or ""
        command_path = os.path.join(os.path.dirname(__file__), 'bin', 'ReadCVRStats')
        p = subprocess.Popen([command_path, self.folder_path, "", file_limit], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True)

        # create a wait and check loop with poll and check_output to display log as process runs
        while p.poll() is None:
            out = p.stdout.readline()
            self.log_area.insert(tk.END, out)
            self.log_area.see(tk.END)

            # wait for 1 second
            self.update_idletasks()

            

        # out, err = p.communicate()

        # for line in out.splitlines():
        #     #print (line)
        #     self.log_area.insert(tk.END, line + "\n")

        if p.stderr:
            print ("Error: ", p.stderr)


if __name__ == "__main__":
    print ("Starting TkCVRApp...")
    app = App()
    print ("App started...")
    app.mainloop()
    print ("Exit")