try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, scrolledtext
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

import threading
from proxy_core import ProxyCore

class ProxyAppCLI:
    def __init__(self):
        self.proxy_core = ProxyCore(self.log)
        self.running = False

    def log(self, message):
        print(message)

    def start_proxy(self):
        self.proxy_core.start_proxy()
        self.running = True
        self.log("Proxy Server is Running...")

    def stop_proxy(self):
        self.proxy_core.stop_proxy()
        self.running = False
        self.log("Proxy Server is Stopped...")

    def generate_report(self):
        client_ip = input("Enter client IP address for the report: ")
        if client_ip:
            report_file_name = self.proxy_core.generate_report(client_ip)
            if report_file_name:
                self.log(f"Report for {client_ip} saved as {report_file_name}.")
            else:
                self.log("Error generating report.")

    def add_host_to_filter(self):
        host = input("Enter host to filter: ")
        if host:
            self.proxy_core.add_host_to_filter(host)
            self.log(f"{host} added to filter list.")

    def remove_host_from_filter(self):
        host = input("Enter host to remove from filter: ")
        if host:
            self.proxy_core.remove_host_from_filter(host)
            self.log(f"{host} removed from filter list.")

    def display_filtered_hosts(self):
        filtered_hosts = self.proxy_core.get_filtered_hosts()
        self.log("Filtered Hosts:\n" + "\n".join(filtered_hosts))

    def show_about(self):
        self.log("Transparent Proxy\nDeveloper: 20180702093")

    def run(self):
        while True:
            command = input("Enter command (start, stop, report, add, remove, display, about, exit): ").strip().lower()
            if command == "start":
                self.start_proxy()
            elif command == "stop":
                self.stop_proxy()
            elif command == "report":
                self.generate_report()
            elif command == "add":
                self.add_host_to_filter()
            elif command == "remove":
                self.remove_host_to_filter()
            elif command == "display":
                self.display_filtered_hosts()
            elif command == "about":
                self.show_about()
            elif command == "exit":
                if self.running:
                    self.stop_proxy()
                break
            else:
                self.log("Unknown command. Please try again.")

if TK_AVAILABLE:
    class ProxyApp:
        def __init__(self, root):
            self.root = root
            self.root.title("Transparent Proxy")
            self.root.geometry("600x400")

            self.menu_bar = tk.Menu(root)

            # File menu
            self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.file_menu.add_command(label="Start", command=self.start_proxy)
            self.file_menu.add_command(label="Stop", command=self.stop_proxy)
            self.file_menu.add_command(label="Report", command=self.generate_report)
            self.file_menu.add_command(label="Add host to filter", command=self.add_host_to_filter)
            self.file_menu.add_command(label="Remove host from filter", command=self.remove_host_from_filter)
            self.file_menu.add_command(label="Display current filtered hosts", command=self.display_filtered_hosts)
            self.file_menu.add_separator()
            self.file_menu.add_command(label="Exit", command=root.quit)
            self.menu_bar.add_cascade(label="File", menu=self.file_menu)

            # Help menu
            self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
            self.help_menu.add_command(label="About", command=self.show_about)
            self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

            root.config(menu=self.menu_bar)

            self.status_label = tk.Label(root, text="Proxy Server is Stopped...", font=("Helvetica", 16))
            self.status_label.pack(pady=10)

            self.log_text = scrolledtext.ScrolledText(root, width=70, height=15, state='disabled')
            self.log_text.pack(pady=10)

            self.proxy_core = ProxyCore(self.log)

        def log(self, message):
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.yview(tk.END)
            self.log_text.config(state='disabled')

        def start_proxy(self):
            self.proxy_core.start_proxy()
            self.status_label.config(text="Proxy Server is Running...")

        def stop_proxy(self):
            self.proxy_core.stop_proxy()
            self.status_label.config(text="Proxy Server is Stopped...")

        def generate_report(self):
            client_ip = simpledialog.askstring("Report", "Enter client IP address:")
            if client_ip:
                report_file_name = self.proxy_core.generate_report(client_ip)
                if report_file_name:
                    messagebox.showinfo("Report", f"Report for {client_ip} saved as {report_file_name}.")
                else:
                    messagebox.showerror("Error", "Error generating report.")

        def add_host_to_filter(self):
            host = simpledialog.askstring("Add Host", "Enter host to filter:")
            if host:
                self.proxy_core.add_host_to_filter(host)
                messagebox.showinfo("Add Host", f"{host} added to filter list.")

        def remove_host_from_filter(self):
            host = simpledialog.askstring("Remove Host", "Enter host to remove from filter:")
            if host:
                self.proxy_core.remove_host_from_filter(host)
                messagebox.showinfo("Remove Host", f"{host} removed from filter list.")

        def display_filtered_hosts(self):
            filtered_hosts = "\n".join(self.proxy_core.get_filtered_hosts())
            messagebox.showinfo("Filtered Hosts", filtered_hosts)

        def show_about(self):
            messagebox.showinfo("About", "Transparent Proxy\nDeveloper: 20180702093")

    if __name__ == "__main__":
        root = tk.Tk()
        app = ProxyApp(root)
        root.mainloop()
else:
    if __name__ == "__main__":
        app = ProxyAppCLI()
        app.run()
