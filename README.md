# Qumulo-Lock-Manager

This script provides a `tkinter` based GUI to list and close SMB locks on a Qumulo cluster via the Qumulo REST API.  

## Why close file handles and what happens on the client when a file handle is closed?

The SMB protocol provides a system of locks which allow a client to set what kind of access it wants to a file stored in an SMB server.  Qumulo
supports most of those locks, such as Exclusive Read or Exclusive Write, but in a shared envionment this could lead to situations where users are
prevented from saving files or accessing files that others have locked.

In those situations the storage administrator could opt to force the closure of this file handle to allow other users access to the file.

Some very common example scenarios are when a user can't save an Excel spreasheet that another user has opened, or when the Mac Finder's Quick Look file previewer
triggered by one user prevents another user from saving a Photoshop or other graphics file.

Selecting a file in the GUI and clicking on `Close File` closes the file handle on the Qumulo cluster side, but the client will still 
have the file open on its end.  

The client is left with a "stale" version of the file that might be out of sync with the version stored in the cluster.  
The client will likely need to close the file locally and reopen it from the Qumulo cluster to get back in sync with the stored
version of the file.  There is a possibility that the user could lose work in progress if the file handle is closed before the file has been saved,
so use caution when closing file handles!


## Requirements:

Tested with `Python 3.9` on Mac OS 13

** A GUI is required for use with a Linux client! **

The script requires `port 443` access to the Qumulo cluster.

The Python package `Tk` is required, check if it is available by running this on a terminal:

`python -m tkinter`

Install Tk if needed:

Linux:

- `sudo apt-get install python3-tk`  (Ubuntu, Debian)
- `sudo yum install -y tkinter tk-devel`  (RHEL, CentOS, Oracle)
- `sudo dnf install python3-tkinter` (Fedora)
- `sudo pacman -S tk`  (Arch)

Mac:

- `brew install python-tk@3.9`

This script requires a valid session token for a user with the following RBAC privileges:

`['PRIVILEGE_FS_LOCK_READ', 'PRIVILEGE_SMB_FILE_HANDLE_READ', 'PRIVILEGE_SMB_FILE_HANDLE_WRITE']`


## Installation:

Install the `requirements.txt` file:

`pip install -r requirements.txt`

Copy `qumulo_lock_manager.py` to your machine, make it executable with `chmod +x qumulo_lock_manager.py`


Edit `qumulo_lock_manager.py` and enter your cluster address and valid Access Token on these variables:

- `cluster_address = "your.cluster.here.com"`

- `token = "session-v1:etc..etc..etc"`

[How to get an Access Token](https://care.qumulo.com/hc/en-us/articles/360004600994-Authenticating-with-Qumulo-s-REST-API#acquiring-a-bearer-token-by-using-the-web-ui-0-3) (Qumulo Care article)


## Operation:

Run the script with `/path/to/script/qumulo_lock_manager.py`

- Refresh the locks by clicking on the `List Locks` button
- Search for paths by typing in a part of the desired path and clicking on the `Search by Path` button
  * The Locks view will automatically refresh   
- Clear the search box and click on `Search by Path` to see all locks
- To close a file handle, select the desired File ID / Path in the UI and click on the `Close File` button
- To quit, simply close the window  

![Screenshot of UI](https://github.com/Joe-Costa/Qumulo-Lock-Manager/assets/76791218/2fa5cf42-2351-4227-afe2-e08d06d04188)





