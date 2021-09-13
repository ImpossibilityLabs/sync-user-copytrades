# Copytrading Offline User Script

## Prerequisites

You will need to have Python 3, you can get it from https://www.python.org/downloads/. 
Script has been tested with Python versions 3.7.7 and 3.8.1 on Mac and Windows, but should work with later versions as well.
The script is written in Python so that everyone can have access to the source code.

You will need to install requirements using:

```
sudo pip3 install -r requirements.txt
```

## How to use

Before running the scripts you may require to set run permissions.

```
sudo chmod +x main.py
sudo chmod +x register.py
./main.py
```

### Registration

First you need to register with the API using the register.py script. It will ask your email and password so you can authenticate later using the main script.

### Copying trades

Run the main.py script 