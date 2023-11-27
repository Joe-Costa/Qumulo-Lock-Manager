# Qumulo-Lock-Manager

This script provides a `tkinter` based GUI to list and close SMB locks on a Qumulo cluster via the Qumulo REST API.  

## Requirements:

Tested with `Python 3.9` on Mac OS 13

** A GUI is required for use with a Linux client! **

The script requires `port 443` access to the Qumulo cluster.

The Python package `Tk` is required, check if it is available by running this on a terminal:

`python -m tkinter`

Linux:

- `sudo apt-get install python3-tk`

Mac:

- `brew install python-tk@3.9`

This script requires a valid session token for a user with the following RBAC privileges:

`['PRIVILEGE_FS_LOCK_READ', 'PRIVILEGE_SMB_FILE_HANDLE_READ', 'PRIVILEGE_SMB_FILE_HANDLE_WRITE']`


This information will likely be stored in a separate config file in future versions.

## Installation:

Install the `requirements.txt` file:

`pip -r install requirements.txt``

Copy `qumulo_lock_manager.py` to your machine, make it executable with `chmod +x qumulo_lock_manager.py`


Edit `qumulo_lock_manager.py` and enter your cluster address and valid Access Token on these variables:

`cluster_address = "your.cluster.here.com"`


`token = "session-v1:etc..etc..etc"`

## Operation:

Run the script with `/path/to/script/qumulo_lock_manager.py`

- Refresh the locks by clicking on the `List Locks` button
- Search for paths by typing in a part of the desired path and clicking on the `Search by Path` button
  * The Locks view will automatically refresh   
- Clear the search box and click on `Search by Path` to see all locks
- To close a file handle, select the desired File ID / Path in the UI and click on the `Close File` button
- To quit, simply close the window  



![Screenshot of UI](https://github.com/Joe-Costa/Qumulo-Lock-Manager/assets/76791218/2fa5cf42-2351-4227-afe2-e08d06d04188)




