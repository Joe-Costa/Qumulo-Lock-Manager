#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import requests
import urllib3
import sys
import configparser

version = "1.1.0beta"
who_am_i = ""


# Load the config file
config = configparser.ConfigParser()
config.read('qumulo_lock_manager.conf')

# Build a dict of clusters from the config file
cluster_list = {}
for section in config.sections():
    # Skip the DEFAULT section
    if section != 'DEFAULT':
        cluster_list[section] = dict(config.items(section))

# Choose the cluster set as the default
for key in cluster_list.keys():
    if cluster_list[key].get('default_option'):
        cluster_address = cluster_list[key].get('address')
        token = cluster_list[key].get('token')
        default_cluster = key
    # If 'default_option' is not set then choose the first cluster in the config
    else:
        cluster_address = cluster_list[list(cluster_list.keys())[0]].get('address')
        token = cluster_list[list(cluster_list.keys())[0]].get('token')
        default_cluster = key

# Disable InsecureRequestWarning from showing up in stdout; this is not needed if you have valid TLS certificates
if config['DEFAULT'].getboolean('ignore_ssl'):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# The RBAC privileges requred for successful user of this script
required_rights = ['PRIVILEGE_FS_LOCK_READ', 'PRIVILEGE_SMB_FILE_HANDLE_READ', 'PRIVILEGE_SMB_FILE_HANDLE_WRITE']

# This class handles error redirection to the GUI
class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def flush(self):
        # This method is required by sys.stdout not to barf
        pass

class QumuloSMBLockManager:
    def __init__(self, master, token=token, cluster=cluster_address):
        self.master = master

        # Set state of initial auto refresh
        self.first_run = True

        # Qumulo Cluster Login Information
        self.cluster_address = cluster
        self.token = token
        self.update_headers(self.token)
        self.who_am_i = self.update_name(self.cluster_address, self.token)

        # GUI Window title info
        # self.master.title(f"Qumulo SMB Lock Manager {version} - Cluster: {self.cluster_address}  Auth User: {who_am_i}")

        # Create GUI components
        self.create_widgets()
        self.lock_tree.bind("<ButtonRelease-1>", self.select_item)

        # Redirect stdout messages to text_widget, comment out for troubleshooting
        sys.stdout = StdoutRedirector(self.text_widget)

        # Verify user access level
        self.verify_rbac_privileges()

        # Get initial set of Locks
        self.refresh_locks()
    
    def update_headers(self, token):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @staticmethod
    def verify_rbac_privileges():
        # Verify the user has the correct RBAC privileges to perform the required API calls
        user_rbac_privileges = user_info['privileges']
        matching_rights = [ x for x in required_rights if x in user_rbac_privileges]
        if set(matching_rights) == set(required_rights):
            return True
        else:
            s = set(matching_rights)
            missing_rights = [ x for x in required_rights if x not in s]
            print(f"User {who_am_i} is missing these required RBAC privileges:")
            print(missing_rights)
            print("Unable to proceed")
            return False

    # Update Current User Name
    def update_name(self, address, token):
        url = f"https://{address}/api/v1/session/who-am-i"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers, verify=False)
        self.verify_rbac_privileges()
        self.who_am_i = response.json().get('name')

    # Cluster selection menu action - Change cluster, token and who_am_i
    def cluster_selector(self, *args):
        selected_item = self.var.get()
        if selected_item in cluster_list:
            self.cluster_address = cluster_list[selected_item]['address']
            self.token = cluster_list[selected_item]['token']
            self.update_name(self.cluster_address,self.token)
            self.update_headers(self.token)
            self.master.title(f"Qumulo SMB Lock Manager {version} - Cluster: {self.cluster_address}  Auth User: {self.who_am_i}")
        if not self.first_run:
            self.refresh_locks()
        self.first_run = False

    def create_widgets(self):
        # Frame for displaying SMB locks
        self.lock_frame = ttk.Frame(self.master)
        self.lock_frame.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        # Drop down menu for server selection
        self.var = tk.StringVar(self.master)
        self.var.trace_add("write", self.cluster_selector)
        self.option_text = tk.Label(self.master, text="Selected Cluster:")
        self.option_text.pack(side=tk.LEFT,padx=10,pady=10)
        self.option_menu = ttk.OptionMenu(self.master, self.var, default_cluster, *cluster_list.keys())
        self.option_menu.pack(side=tk.LEFT, padx=10, pady=10)

        # Treeview to display SMB locks
        self.lock_tree = ttk.Treeview(
            self.lock_frame, columns=("File ID", "File Path", "Mode", "Holder Address", "Node Address"), show="headings"
        )
        self.lock_tree.column("Holder Address", anchor=tk.N,width=120)
        self.lock_tree.column("Node Address", anchor=tk.N,width=120)
        self.lock_tree.column("Mode", anchor=tk.N, width=340)
        self.lock_tree.column("File ID", anchor=tk.N, width=100)
        self.lock_tree.heading("File ID", text="File ID")
        self.lock_tree.heading("File Path", text="File Path")
        self.lock_tree.heading("Mode", text="Lock Mode")
        self.lock_tree.heading("Holder Address", text="Holder Address")
        self.lock_tree.heading("Node Address", text="Node Address")
        self.lock_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Scroll bar for Treeview window
        self.scrollbar = ttk.Scrollbar(self.lock_frame, orient="vertical", command=self.lock_tree.yview)
        self.lock_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Redirect stdout to the GUI
        self.text_widget = tk.Text(self.master, wrap=tk.WORD, height=4, font=("Helvetica", 16))
        self.text_widget.pack(side=tk.TOP, padx=5, pady=(5,5),fill=tk.BOTH)

        # Button to refresh SMB locks
        refresh_button = ttk.Button(self.master, text="List Locks", command=self.refresh_locks)
        refresh_button.pack(side=tk.LEFT, padx=50, pady=20)

        # Text entry for filtering by file path
        self.file_path_entry = ttk.Entry(self.master, width=30)
        self.file_path_entry.pack(side=tk.LEFT, padx=(50,10), pady=20)

        # Button to apply file path filter
        filter_button = ttk.Button(self.master, text="Find Path or IP", command=self.refresh_locks)
        filter_button.pack(side=tk.LEFT, pady=20)

        # Button to close file handle
        closeHandle_button = ttk.Button(self.master, text="Close File", command=self.find_handle,style="Red.TButton")
        closeHandle_button.pack(side=tk.RIGHT, padx=50, pady=20)

    def find_handle(self):
        global handle_info
        # This function lists all open file handles and returns the handle info of the selected file ID
        # The entire JSON blob for the entry is needed by the API to close a handle
        # I should merge this with close_handle...
        for keys in handle_info:
            if keys["file_number"] == str(file_id):
                self.close_handle(keys)

    def close_handle(self, handle):
        # This function closes the file handle selected in the GUI
        # I think that findHandle and closeHandle could be merged, but eh.
        url = f"https://{self.cluster_address}/api/v1/smb/files/close"
        response = requests.post(url, headers=self.headers, json=[handle], verify=False)
        if response.status_code == 200:
            self.refresh_locks()
            print(f"File handle of {handle['handle_info']['path']} has been closed")
        else:
            print(f"Error closing file handle!! {response.status_code} - {response.text}")
            return

    def select_item(self, event):
        # This grabs the File ID field of the line selected by the user in the UI
        global file_id
        curItem = self.lock_tree.focus()
        itemJson = self.lock_tree.item(curItem)
        file_id = itemJson["values"][0]

    def refresh_locks(self):
        # Clear previous data in the lock list
        for item in self.lock_tree.get_children():
            self.lock_tree.delete(item)

        # Clear previous data in the stdout Text widget
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

        # Fetch SMB locks from Qumulo cluster, print lock count
        try:
            # Grammar counts so let's pluralize when needed...
            plural = ""
            smb_locks = self.get_smb_locks()
            lock_count = len(smb_locks['grants'])
            if lock_count == 1:
                plural = ""
            else:
                plural = "s"
            print(f"{lock_count} lock{plural} found")
        except:
            print(f"Did I break here? Token: {self.token} addr = {self.cluster_address}")
            # General error handler in case smb_locks fails
            return

        # Get the filter criteria
        filter_text = self.file_path_entry.get().lower()

        # Load all currently opened file handles and map ID to path
        file_number_to_path = self.path_loader()

        # Populate Treeview with SMB locks that match the filter criteria to enable search by Path
        for grant in smb_locks["grants"]:
            id = grant["file_id"]
            holder_ip_address = grant["owner_address"]
            try:
              file_path = file_number_to_path[id]
            except:
                # A common cause of errors here would be trying to resolve the path of a file handle that has 
                # already been closed. We could simplay pass, but I'll leave a message in case something else
                # is the cause.  We might see this when dealign with very many open file handles and the
                # 'List Locks' action being triggered and many handles are beign closed.
                print(f"File Handle {id} already closed?")
                pass
            if filter_text in file_path.lower() or filter_text in holder_ip_address.lower():
                self.lock_tree.insert(
                    "",
                    "end",
                    values=(
                        grant.get("file_id", ""),
                        file_path,
                        ", ".join(grant.get("mode", [])),
                        grant.get("owner_address", ""),
                        grant.get("node_address", ""),
                    ),
                )
    def path_loader(self):
        '''This function lists all open files and creates a dict of File IDs as Keys and Paths as Values to expedite
        the resolution of file paths. The timing of this vs the currently held locks should be good enough for
        our purposes'''

        global handle_info

        url = f"https://{self.cluster_address}/api/v1/smb/files/?resolve_paths=true"
        
        # Get the initial API response
        response = requests.get(url, headers=self.headers, verify=False).json()
        handles = response['file_handles']
        next = response['paging']['next']

        # I there are response pages to load, continue, esle return values
        if next != None:
            # Modify the url with pagination 'next' info for passes after the first response
            url = f"https://{cluster_address}/api" + next
            
            # Loop to handle API pagination
            while next:
                response = requests.get(url, headers=self.headers, verify=False).json()
                next = response['paging']['next']
                if next != None:
                  url = f"https://{cluster_address}/api" + next
                handles.extend(response['file_handles'])

        # This will be used by functions findHandle and closeHandle
        handle_info = handles 

        # This contains a file ID to path k,v index of all open files, we need this to display paths in the
        # GUI since  /v1/files/locks/smb/share-mode/ does not resolve paths'''
        file_number_to_path = {handle["file_number"]: handle["handle_info"]["path"] for handle in handles}
        return file_number_to_path
      

    def get_smb_locks(self):
        # Grab all currently held SMB locks 
        url = f"https://{self.cluster_address}/api/v1/files/locks/smb/share-mode/"
        # Grab the inital API response
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            after_cursor = response.json().get('paging',{})
        except:
            error = f"Error authenticating or reaching the cluster! {response.status_code} - {response.text}"
            return error
        
        # Load first page of locks in smb_locks or exit if status code is not 200
        if response.status_code == 200:
            smb_locks = response.json()
        else:
            # **** Make a better error handler here ***
            print(f"Error getting SMB locks! {response.status_code} - {response.text}")
        
        # Modify the URL with the pagination info after the first API response
        url = f"https://{self.cluster_address}/" + after_cursor['next'][1:]

        # Continue loading smb_locks as long as there are grants
        # Note that this pagination behavior is very different from 
        # /v1/smb/files/?resolve_paths=true used in function self.path_loader
        while response.json().get('grants'):
            response = requests.get(url, headers=self.headers, verify=False)
            after_cursor = response.json().get('paging',{})
            if response.json().get('grants'):
                smb_locks = {'grants': smb_locks['grants'] + response.json()['grants']}
            # Update url with the next page
            url = f"https://{self.cluster_address}/" + after_cursor['next'][1:]
        return smb_locks

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background="black", fieldbackground="black", foreground="white")
    style.configure("Red.TButton", foreground="red") 
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Get the Auth ID user's information
    url = f"https://{cluster_address}/api/v1/session/who-am-i"

    # Basic connectivity checks
    initial_response = requests.get(url, headers=headers, verify=False)
    ir_code = initial_response.status_code
    if ir_code == 200:
            pass
    elif ir_code == 401:  # Auth token check
        print(f"{initial_response.status_code} - Authentication Error! Has your auth token expired? ")
        exit()
    else:
        try:
            initial_response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print (f"Http Error: {err}")
            exit()
        except requests.exceptions.ConnectionError:
            print (f"Error Connecting, is the cluster address correct?")
            exit()
        except requests.exceptions.Timeout:
            print ("Timeout Error: Do you have a valid network connection to the cluster?")
            exit()
        except requests.exceptions.RequestException as err:
            print (f"General Error: {err}")
            exit()

    # If tests passed, proceed to GUI, we'll check if current user has the required rights in the Class
    user_info = initial_response.json()
    app = QumuloSMBLockManager(root, token, cluster_address)
    root.mainloop()

