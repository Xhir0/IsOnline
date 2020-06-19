"""
@author: xhir0
https://github.com/Xhir0/IsOnline.git
"""

from tkinter import ttk
from tkinter.font import Font
import tkinter as tk
from time import sleep
from threading import Thread
from subprocess import getstatusoutput
from os.path import isfile
from socket import gethostname, gethostbyname

class DropDownTable(ttk.Combobox):
    """ Drop Down Combobox """
    def __init__(self, parent, **kwargs):
        ttk.Combobox.__init__(self, parent, **kwargs)
        self._combobox_stringvar = tk.StringVar()
        self.config(textvariable=self._combobox_stringvar)
    
    def setv(self, values: any):
        self.config(values=values)
    
    def clear(self):
        self.config(values=[])


class App(object):
    """ Main Application Window """
    def __init__(self, root, WIDTH=250, HEIGHT=100):
        self.root = root

        root.resizable(0, 0)
        root.geometry(f"{WIDTH}x{HEIGHT}")
        root.title("IsOnline?")

        if icon_available := isfile("icon.ico"):
            root.iconbitmap("icon.ico")
        self.icon_available = icon_available

        canvas = tk.Canvas(root, highlightthickness=0, width=WIDTH, height=HEIGHT, bg="grey23")
        canvas.pack()

        self.bg, self.fg = "black", "whitesmoke"
        self.output_lb_font = Font(family="Ubuntu", size=13)
        canvas.configure(bg=self.bg)

        self.submitted_hosts = [gethostbyname(gethostname())]
        
        self.hosts_combobox = DropDownTable(canvas, width=20, state="readonly", background=self.bg, foreground=self.fg, values=self.submitted_hosts)
        canvas.create_window(110, 20, window=self.hosts_combobox)
        self.host_entry = tk.Entry(textvariable=tk.StringVar(), relief=tk.FLAT, font=("Ubuntu", 10, "bold"), bg=self.bg, fg=self.fg)
        canvas.create_window(110, 56, window=self.host_entry)
        self.submit_btn = tk.Button(text="GO", relief=tk.FLAT, command=self.start, bg=self.bg, fg=self.fg, activebackground=self.bg)
        canvas.create_window(210, 57, window=self.submit_btn)

        canvas.create_line(40, 70, 180, 70, fill="white")
        canvas.create_line(200, 70, 220, 70, fill="white")

        self.host = "LOCALHOST"
        self.host_entry.insert(tk.END, self.host)

        self.active_windows = []
        #self.hosts_combobox.place(relx=0.15, rely=0.15)
        #self.host_entry.place(relx=0.15, rely=0.35)
        #self.submit_btn.place(relx=0.725, rely=0.325)

        self.hosts_combobox.bind("<<ComboboxSelected>>", self.combobox_select)
        self.host_entry.bind("<Return>", self.start)

    def combobox_select(self, event=None):
        """ Match entry to currently selected item in DropDownTable """
        self.host_entry.delete(0, tk.END)
        self.host_entry.insert(0, self.hosts_combobox.get())

    def start(self, event=None):
        """ Get host from entry box and store it """
        if not (tmp := self.host_entry.get().strip()) == "":
            self.host_entry.delete(0, tk.END)
            self.display(tmp)

    def display(self, host):
        """ Open a child window to display whether the host is responding or not """
        if len(self.active_windows) >= 1:
            return
        self.host = host

        if not host in self.submitted_hosts: self.submitted_hosts.append(host)
        self.hosts_combobox.setv(self.submitted_hosts)

        master = tk.Toplevel(root)
        if self.icon_available: master.iconbitmap("icon.ico")
        self.active_windows.append(master)
        master.wm_title("")
        master.configure(bg="black")

        self.lb = tk.Label(master, text=f"Pinging {host}", font=self.output_lb_font, bg=self.bg, fg=self.fg)
        self.lb.pack()
        
        self.ping_worker = Thread(target=self.ping)
        self.hang_update_worker = Thread(target=self.callback)
        self.threads = [self.ping_worker, self.hang_update_worker]

        for thread in self.threads:
            thread._is_running = True
            thread.start()

        master.protocol("WM_DELETE_WINDOW", lambda: self.exit_(master))
        master.bind("<Control-minus>", lambda e: self.change_font(interv=-1))
        master.bind("<Control-plus>", lambda e: self.change_font(interv=1))
        master.bind("<Control-=>", lambda e: self.change_font(interv=1))


    def callback(self):
        """ Prevent main Tk from hanging by calling refresh every 1000 ms """
        if self.hang_update_worker._is_running:
            root.after(1000, self.refresh)
    
    def refresh(self):
        """ Update the main Tk so it doesn't hang """
        if self.hang_update_worker._is_running:
            root.update()
            self.callback()

    def ping(self):
        """ Ping a host and depending on the response update a label """
        cmd = f"PING -n 1 {self.host} | FIND \"TTL=\""
        while self.ping_worker._is_running:
            try:
                if not getstatusoutput(cmd)[0]:
                    if self.ping_worker._is_running: self.lb.configure(text=f"{self.host} ONLINE", fg="green")
                else:
                    if self.ping_worker._is_running: self.lb.configure(text=f"{self.host} OFFLINE", fg="red")
            except Exception as e:
                print(f"CAUGHT\n{e}\n")
                exit(1)

    def exit_(self,  master):
        """ Stop all threads before closing Toplevel window """
        for thread in self.threads:
            thread._is_running = False
            thread.join()

        master.destroy()
        self.active_windows.remove(master)
        self.threads.clear()


    def change_font(self, interv: int):
        self.output_lb_font["size"] += interv
        self.lb.config(font=self.output_lb_font)


if __name__ == "__main__":
    root = tk.Tk()
    main = App(root)
    root.mainloop()