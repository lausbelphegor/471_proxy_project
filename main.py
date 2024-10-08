try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, scrolledtext
    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

import threading
from proxy_core import ProxyCore
from flask import Flask, request, jsonify

class ProxyAppCLI:
    def __init__(self):
        self.proxy_core = ProxyCore(self.log)
        self.running = False
        self.app = Flask(__name__)
        self.setup_routes()

    def log(self, message):
        print(message)

    def start_proxy(self):
        self.proxy_core.start_proxy()
        self.running = True
        self.log("Proxy Server is Running...")
        return "Proxy Server is Running..."

    def stop_proxy(self):
        self.proxy_core.stop_proxy()
        self.running = False
        self.log("Proxy Server is Stopped...")
        return "Proxy Server is Stopped..."

    def generate_report(self, client_ip):
        if client_ip:
            report_file_name = self.proxy_core.generate_report(client_ip)
            if report_file_name:
                self.log(f"Report for {client_ip} saved as {report_file_name}.")
                return f"Report for {client_ip} saved as {report_file_name}."
            else:
                self.log("Error generating report.")
                return "Error generating report."
        return "Client IP not provided."

    def add_host_to_filter(self, host):
        if host:
            self.proxy_core.add_host_to_filter(host)
            self.log(f"{host} added to filter list.")
            return f"{host} added to filter list."
        return "Host not provided."

    def remove_host_from_filter(self, host):
        if host:
            self.proxy_core.remove_host_from_filter(host)
            self.log(f"{host} removed from filter list.")
            return f"{host} removed from filter list."
        return "Host not provided."

    def display_filtered_hosts(self):
        filtered_hosts = self.proxy_core.get_filtered_hosts()
        self.log("Filtered Hosts:\n" + "\n".join(filtered_hosts))
        return "\n".join(filtered_hosts)

    def show_about(self):
        about_message = "Transparent Proxy\nDeveloper: 20180702093"
        self.log(about_message)
        return about_message

    def setup_routes(self):
        @self.app.route('/start', methods=['POST'])
        def start():
            return self.start_proxy()

        @self.app.route('/stop', methods=['POST'])
        def stop():
            return self.stop_proxy()

        @self.app.route('/report', methods=['POST'])
        def report():
            client_ip = request.json.get('client_ip')
            return self.generate_report(client_ip)

        @self.app.route('/add_host', methods=['POST'])
        def add_host():
            host = request.json.get('host')
            return self.add_host_to_filter(host)

        @self.app.route('/remove_host', methods=['POST'])
        def remove_host():
            host = request.json.get('host')
            return self.remove_host_from_filter(host)

        @self.app.route('/display_hosts', methods=['GET'])
        def display_hosts():
            return self.display_filtered_hosts()

        @self.app.route('/about', methods=['GET'])
        def about():
            return self.show_about()

    def run(self):
        self.app.run(port=8081)
        
def create_app():
    proxy_app = ProxyAppCLI()
    return proxy_app.app

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
        app.start_proxy()
        root.mainloop()
else:
    if __name__ == "__main__":
        app = ProxyAppCLI()
        app.start_proxy()
        app.run()

