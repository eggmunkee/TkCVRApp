#!/usr/bin/python

import os
import subprocess
from signal import SIGINT
import tkinter as tk
from tkinter import filedialog, scrolledtext, StringVar
from pathlib import Path
import tkinter.ttk as ttk
from tkinter.ttk import *

class SyncProcessAndText():
    def __init__(self, tk_app, log_area, finished_cb):
        self.process_args = []
        self.app = tk_app
        self.log_area = log_area
        self.process = None
        self.process_gen = None
        self.finished_cb = finished_cb

    def start_process(self, process_args):
        print("Starting process with args: ", process_args)
        self.process_args = process_args
        self.process = subprocess.Popen(self.process_args, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True)

        # create a wait and check loop with poll and check_output to display log as process runs
        def check_process():
            if self.process:
                while self.process.poll() is None:
                    self.app.update_idletasks()
                    out_count = 0
                    while self.process_output() and out_count < 1:
                        out_count += 1
                    self.app.after(10, self.process_check)
                    yield
                # process is done
                self.finished_process()
            else:
                print("Reached check_process with no process!")

        # create a generator to run the process
        self.process_gen = check_process()
        print("Starting process...")
        # start the process by calling generator once
        next(self.process_gen)

    def process_output(self):
        i = 0
        done = False
        while i < 250: # limit to 100 characters at a time
            out = self.process.stdout.read(1)
            self.app.update_idletasks() # update the UI
            if out:
                self.log_area.insert(tk.END, out)
            else:
                done = True
                break
            i+=1
        self.log_area.see(tk.END)
        self.app.update_idletasks() # update the UI
        return done

    def process_check(self):
        if self.process_gen:
            # update the UI
            self.app.update()
            # run the generator
            try:
                next(self.process_gen)
            except StopIteration:
                print("Generator is done...")
                self.process_gen = None
        else:
            print("No generator to check")

    # Cancel the process from the outside
    def cancel_process(self):
        if self.process:
            # Send the signal to the process and let it finish on its own
            self.process.send_signal(SIGINT)

    def finished_process(self):
        # clear the generator variable
        self.process_gen = None
        # finish outputing information
        while self.process_output() == False:
            pass
        # check for errors
        err = self.process.stderr.readline()
        while err:
            print ("Error: ", err)
            err = self.process.stderr.readline()
        # clear process and reset button states
        self.process = None
        
        self.finished_cb()

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Read CVRs - Export To CSV")

        self.geometry("900x700")

        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc", font=("Arial", 11, "bold"))
        self.style.configure("Highlight.TButton", padding=6, relief="flat", background="#88d0ee")
        self.style.configure("Delete.TButton", padding=6, relief="flat", background="#e99")
        self.style.configure("HighlightOption", padding=6, relief="flat", background="#ccc")
        self.style.configure("KeyInformation.TLabel", padding=6, relief="flat", background="#88eed0", font=("Arial", 11, "bold"))
        self.style.configure("Highlight.TLabel", padding=6, relief="flat", background="#88d0ee", font=("Arial", 11, "bold"))

        print(self.style.layout("TButton"))

        # internal variables
        self.folder_path = None

        # frame around top controls
        self.top_frame = Frame(self, height=200, borderwidth=2, relief="groove")

        # Select File Type Step
        self.file_type_label = Label(self.top_frame, text="1) Select File Type: ", style="Highlight.TLabel")
        self.file_type_label.pack(pady=5, side="left")

        # Create a Tkinter variable for File Type
        self.file_type_var = StringVar(self)
        self.file_type_var.set("singlecvr") # default value

        # Create a Tkinter option menu for Single CVR File or CVR Report File
        self.file_type_menu = OptionMenu(self.top_frame, self.file_type_var, "Select Type", "singlecvr", "cvrreport")

        #self.file_type_menu.set_style(".HighligtOption")
        self.file_type_menu.pack(pady=5, side="left")
        self.file_type_var.set("singlecvr")

        # Choose CVR Folder Step
        self.folder_chooser = Button(self.top_frame, text="2) Choose CVRs Folder", command=self.choose_folder, style="Highlight.TButton")
        self.folder_chooser.pack(pady=10, side="top")

        self.top_frame.pack(fill="x")

        self.folder_path_bar = Frame(self, borderwidth=1, relief="raised")

        self.folder_path_label = Label(self.folder_path_bar, text="No folder selected", style="KeyInformation.TLabel")
        self.folder_path_label.pack(pady=3, side="left", fill="x", expand=True)
        self.folder_path_bar.pack(fill="x")


        self.process_control_frame = Frame(self, width=200, borderwidth=2, relief="groove")

        self.process_status_label = Label(self.process_control_frame, text="Process Status: Not Started")
        self.process_status_label.pack(pady=20)

        self.test_run_btn = Button(self.process_control_frame, text="Test Run (100 CVRs)", command=self.test_run_process, style="Highlight.TButton")
        self.test_run_btn.pack(pady=5)

        self.start_btn = Button(self.process_control_frame, text="Process Folder", command=self.start_process, style="Highlight.TButton")
        self.start_btn.pack(pady=5)

        self.cancel_btn = Button(self.process_control_frame, text="Cancel Process", command=self.cancel_process, style="Delete.TButton")
        self.cancel_btn.pack(pady=5)

        self.process_control_frame.pack(padx=20, pady=20, side="left", anchor="nw")

        # -------
        self.log_area_label = Label(self, text="Process Log:")
        self.log_area_label.pack(pady=5)


        self.log_frame = Frame(self)
        self.log_frame.pack(fill="both", expand=True)


        self.log_area = tk.Text(self.log_frame, wrap="word")
        vsb = Scrollbar(self.log_frame, command=self.log_area.yview, orient="vertical")
        self.log_area.configure(yscrollcommand=vsb.set) #, xscrollcommand=hsb.set)

        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        vsb.grid(row=0, column=1, sticky="ns")
        self.log_area.grid(row=0, column=0, sticky="nsew")

        self.clear_log_btn = Button(self.log_frame, text="Clear Log", command=self.clear_log, style="Delete.TButton")
        self.clear_log_btn.grid(row=1, column=0, pady=5, sticky="s")

        # --------
        
        self.sync_proc_text = SyncProcessAndText(self, self.log_area, self.finished_process)

        self.set_process_state(ready=False)


    def choose_folder(self):
        # open a file dialog to choose a folder
        folder = tk.filedialog.askdirectory()

        self.folder_path = folder
        if self.folder_path:
            self.set_process_state(ready=True)
            self.folder_path_label.config(text="Folder Selected: " + self.folder_path)
        else:
            self.set_process_state(ready=False)
            self.folder_path_label.config(text="No folder selected")

    def set_process_state(self, ready=False, started=False, canceling=False, finished=False):
        if ready:
            self.start_btn.config(state="normal")
            self.test_run_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
        elif started:
            self.start_btn.config(state="disabled")
            self.test_run_btn.config(state="disabled")
            self.cancel_btn.config(state="normal")
        elif finished:
            self.start_btn.config(state="normal")
            self.test_run_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
        elif canceling or not ready:
            self.start_btn.config(state="disabled")
            self.test_run_btn.config(state="disabled")
            self.cancel_btn.config(state="disabled")

        if canceling:
            self.process_status_label.config(text="Process Status: Cancelling...")
        elif started:
            self.process_status_label.config(text="Process Status: Running")
        elif finished:
            self.process_status_label.config(text="Process Status: Finished")
        else:
            self.process_status_label.config(text="Process Status: Not Started")

    def cancel_process(self):
        self.set_process_state(canceling=True)
        self.sync_proc_text.cancel_process()

    def test_run_process(self):
        self.start_process(test_run=True)

    def clear_log(self):
        self.log_area.delete('1.0', tk.END)

    def start_process(self, test_run=False):
        file_limit = test_run and "100" or "-1"
        command_path = os.path.join(os.path.dirname(__file__), 'bin', 'ReadCVRStats')

        self.set_process_state(started=True)
        self.sync_proc_text.start_process([command_path, self.folder_path, "", self.file_type_var.get(), file_limit, file_limit])

    def finished_process(self):        
        self.set_process_state(finished=True)

if __name__ == "__main__":
    print ("Starting TkCVRApp...")
    app = App()
    print ("App started...")
    app.mainloop()
    print ("Exit")