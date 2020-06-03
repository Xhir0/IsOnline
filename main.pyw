from tkinter import ttk
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
        self.combobox_stringvar = tk.StringVar()
        self.config(textvariable=self.combobox_stringvar)
    
    def setv(self, values: any):
        self.config(values=values)
    
    def clear(self):
        self.config(values=[])


class App(tk.Frame):
    """ Main Application Window """
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        bg = "black"
        self.configure(bg=bg)

        self.submitted_hosts, self.threads = [gethostbyname(gethostname())], []
        self.hosts_combobox = DropDownTable(self, width=20, state="readonly", background=bg, foreground=bg, values=self.submitted_hosts)
        self.host_entry = tk.Entry(self, textvariable=tk.StringVar(), relief=tk.FLAT, font=("Ubuntu", 10, "bold"), bg=bg, fg="whitesmoke")
        self.submit_btn = tk.Button(self, text="GO", relief=tk.FLAT, command=self.start, bg=bg, fg="whitesmoke", activebackground=bg)

        self.host = "LOCALHOST"
        self.host_entry.insert(tk.END, self.host)

        self.active_windows = []

        self.hosts_combobox.place(relx=0.15, rely=0.15)
        self.host_entry.place(relx=0.15, rely=0.35)
        self.submit_btn.place(relx=0.725, rely=0.325)

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
        del tmp

    def display(self, host):
        """ Open a child window to display whether the host is responding or not """
        if len(self.active_windows) >= 1:
            return
        self.host = host

        if not host in self.submitted_hosts: self.submitted_hosts.append(host)
        self.hosts_combobox.setv(self.submitted_hosts)

        master = tk.Toplevel(self)
        if icon_available: master.iconbitmap("icon.ico")
        self.active_windows.append(master)
        master.wm_title("")
        master.configure(bg="black")

        self.lb = tk.Label(master, text=f"Pinging {host}", font=("Ubuntu", 13, "bold"), bg="black", fg="whitesmoke")
        self.lb.pack()

        self.update_thread = Thread(target=self.ping)
        self.threads.append(self.update_thread)

        self.root_update_thread = Thread(target=self.callback)
        self.threads.append(self.root_update_thread)

        for thread in self.threads:
            thread._is_running = True
            thread.start()

        master.protocol("WM_DELETE_WINDOW", lambda: self.exit_(master))


    def callback(self):
        """ Prevent main Tk from hanging by calling refresh every 1000 ms """
        if self.root_update_thread._is_running:
            self.after(1000, self.refresh)
    
    def refresh(self):
        """ Update the main Tk so it doesn't hang """
        if self.root_update_thread._is_running:
            self.update()
            self.callback()

    def ping(self):
        """ Ping a host and depending on the response update a label """
        cmd = f"PING {self.host} -l 32"
        while self.update_thread._is_running:
            try:
                if not getstatusoutput(cmd)[0]:
                    if self.update_thread._is_running: self.lb.configure(text=f"{self.host} ONLINE", fg="green")
                else:
                    if self.update_thread._is_running: self.lb.configure(text=f"{self.host} OFFLINE", fg="red")
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


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("250x100")
    root.title("IsOnline?")

    if icon_available := isfile("icon.ico"):
        root.iconbitmap("icon.ico")
    main = App(root)
    main.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    root.mainloop()
