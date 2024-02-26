# pds-tools  
Tools for atproto PDS. More items to be added.  

## [setup_pds.py](https://github.com/qatoqat/pds-tools/blob/main/setup_pds.py)  
Setup a bare minimum PDS, without container or reverse proxy.  
The server is hosted at `127.0.0.1:3002`.  
Users can manually setup their desired reverse proxy server like nginx or caddy.

### What this script does  
1 - Check for required tools: curl, git, node, openssl, pnpm 
2 - Git clone / pull [bluesky-social/pds](https://github.com/bluesky-social/pds) to `PDS_REPO_PATH`  
3 - Setup .env for `pds/service`    
4 - Setup systemd unit for pds  
5 - Run pds and check status at `127.0.0.1:3002/xrpc/_health`

### Before start
1 - Make sure the following items are installed and available in path:
 - curl
 - git
 - node
 - openssl
 - pnpm

2 - Check the top part of `setup_pds.py`. Change the values to your need.  
Most likely you only need to change `PDS_DOMAIN`
```python
# config, change these values ===================================

PDS_DOMAIN = "pds.qatoqat.com"
PDS_REPO_PATH = Path.home() / "pds"
PDS_ENV_PATH = f"{PDS_REPO_PATH}/service/.env"
SYSTEMD_UNIT_PATH = "/etc/systemd/system/pds.service"
``` 

### Running the script
Download the script or clone this `pds-tools` repo. Use python3 or run this in the command line:
```sh
python3 setup_pds.py
```