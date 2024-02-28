#!/usr/bin/python

import os
import subprocess
from signal import SIGINT
import tkinter as tk
from tkinter import filedialog, scrolledtext
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
                    self.process_output()
                    self.app.after(50, self.process_check)
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
        while i < 100: # limit to 100 characters at a time
            out = self.process.stdout.read(1)
            if out:
                self.log_area.insert(tk.END, out)
                self.log_area.see(tk.END)
                self.app.update_idletasks() # update the UI
            else:
                done = True
                break
            i+=1
        return done

    def process_check(self):
        if self.process_gen:
            # update the UI
            self.app.update_idletasks()
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

        ttk.Style().configure("TButton", padding=6, relief="flat", background="#ccc")

        # internal variables
        self.folder_path = None

        # frame around top controls
        self.top_frame = tk.Frame(self, height=200, borderwidth=2, relief="groove")

        # Select File Type Step
        self.file_type_label = tk.Label(self.top_frame, text="Select File Type")
        self.file_type_label.pack(pady=5, side="left")

        # Create a Tkinter variable for File Type
        self.file_type_var = tk.StringVar(self)
        self.file_type_var.set("singlecvr") # default value

        # Create a Tkinter option menu for Single CVR File or CVR Report File
        self.file_type_menu = tk.OptionMenu(self.top_frame, self.file_type_var, "singlecvr", "cvrreport")
        self.file_type_menu.pack(pady=5, side="left")

        # Choose CVR Folder Step
        self.folder_chooser = tk.Button(self.top_frame, text="Choose CVRs Folder", command=self.choose_folder)
        self.folder_chooser.pack(pady=10, side="bottom")

        self.folder_path_label = tk.Label(self.top_frame, text="No folder selected")
        self.folder_path_label.pack(pady=10, side="bottom")

        self.top_frame.pack(fill="x")

        self.process_control_frame = tk.Frame(self, width=200, borderwidth=2, relief="groove")

        self.process_status_label = tk.Label(self.process_control_frame, text="Process Status: Not Started")
        self.process_status_label.pack(pady=20)

        self.test_run_btn = tk.Button(self.process_control_frame, text="Test Run (100 CVRs)", command=self.test_run_process)
        self.test_run_btn.pack(pady=5)

        self.start_btn = tk.Button(self.process_control_frame, text="Process Folder", command=self.start_process)
        self.start_btn.pack(pady=5)

        self.cancel_btn = tk.Button(self.process_control_frame, text="Cancel Process", command=self.cancel_process)
        self.cancel_btn.pack(pady=5)

        self.process_control_frame.pack(padx=20, pady=20, side="left", anchor="nw")

        self.log_area_label = tk.Label(self, text="Process Log:")
        self.log_area_label.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(self, height=30, width=80, wrap="word")
        self.log_area.pack(expand=True, fill="both")

        self.clear_log_btn = tk.Button(self, text="Clear Log", command=self.clear_log)
        self.clear_log_btn.pack(pady=5, side="bottom")
        
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