# nym-file-service-provider
A service provider for the Nym network, that saves locally received files.
It behaves as a server application and in a production environment should be available 24/7.

This is a minimal implentation. Communication is done with binary messages.

Tested on the Milhon testnet (nym-client v0.11.0)

Works best with
- Python 3.6.9

## Running
You can create a separate virtual env if you want in you repository clone:

- ```python3 -m venv env```

Activate it
- ```source env/bin/activate```

Install requirements
- ```pip install -r requirements.txt```

Start
- ```python app.py```


Requires a nym-client listening on `http://localhost:1977`

## Client

The client/GUI developed for this file service provider can be found here:  
  
[nym-file-uploader-client](https://github.com/marius-avram/nym-file-uploader-client)
