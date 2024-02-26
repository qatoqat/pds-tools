#!/usr/bin/env python3

import os.path
from subprocess import check_output, CalledProcessError, DEVNULL
from os import chdir, makedirs
from pathlib import Path
from time import sleep

# config, change these values ===================================

PDS_DOMAIN = "pds.qatoqat.com"
PDS_REPO_PATH = Path.home() / "pds"
PDS_ENV_PATH = f"{PDS_REPO_PATH}/service/.env"
SYSTEMD_UNIT_PATH = "/etc/systemd/system/pds.service"


# helper ========================================================
def run(command: str, exit_on_error=True) -> str:
    try:
        return check_output(command, text=True, stderr=DEVNULL, shell=True)
    except CalledProcessError as e:
        if exit_on_error:
            print("Error:", e)
            exit(e.returncode)
        raise e


# steps =========================================================
def check_requirements():
    requirements = [
        ("curl", "curl --version"),
        ("git", "git --version"),
        ("node", "node -v"),
        ("openssl", "openssl version"),
        ("pnpm", "pnpm -v"),
    ]

    results = []
    for item, command in requirements:
        result = f"{item} "
        try:
            run(command, exit_on_error=False)
            result += f"OK"
        except CalledProcessError:
            result += f"ERROR"
        results.append(result)

    result_str = "\n".join(results)

    message = f"""Requirements: 
{result_str}

PDS domain : {PDS_DOMAIN}
PDS git repo path : {PDS_REPO_PATH}
PDS service .env path : {PDS_ENV_PATH}
PDS systemd unit path : {SYSTEMD_UNIT_PATH}

Press "y" and "enter" to proceed, else press any key to exit ...
"""

    if not input(message).lower() == "y":
        exit()


def get_repo():
    if os.path.exists(PDS_REPO_PATH):
        cwd = os.getcwd()
        chdir(PDS_REPO_PATH)
        run(f"git pull")
        chdir(cwd)
    else:
        run(f"git clone https://github.com/bluesky-social/pds {PDS_REPO_PATH}")


def setup_env():
    if os.path.exists(PDS_ENV_PATH):
        return

    jwt_secret = run("openssl rand --hex 16")

    def private_key_hex() -> str:
        commands = [
            "openssl ecparam --name secp256k1 --genkey --noout --outform DER",
            "tail --bytes=+8",
            "head --bytes=32",
            "xxd --plain --cols 32"
        ]
        return run(" | ".join(commands)).strip()

    admin_password = private_key_hex()
    rotation_key = private_key_hex()

    env_str = f"""PDS_HOSTNAME="{PDS_DOMAIN}"
PDS_JWT_SECRET="{jwt_secret}"
PDS_ADMIN_PASSWORD="{admin_password}"
PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX="{rotation_key}"

PDS_DATA_DIRECTORY=./data
PDS_BLOBSTORE_DISK_LOCATION=./data/blocks
PDS_DID_PLC_URL=https://plc.directory
PDS_BSKY_APP_VIEW_URL=https://api.bsky.app
PDS_BSKY_APP_VIEW_DID=did:web:api.bsky.app
PDS_REPORT_SERVICE_URL=https://mod.bsky.app
PDS_REPORT_SERVICE_DID=did:plc:ar7c4by46qjdydhdevvrndac
PDS_CRAWLERS=https://bsky.network
LOG_ENABLED=true
NODE_ENV=production
PDS_PORT=3002
"""
    with open(PDS_ENV_PATH, "w") as f:
        f.write(env_str)


def setup_service():
    cwd = os.getcwd()
    chdir(f"{PDS_REPO_PATH}/service")
    run("pnpm install --production --frozen-lockfile")
    makedirs(f"{PDS_REPO_PATH}/service/data/blocks", exist_ok=True)
    chdir(cwd)


def setup_systemd_unit():
    if os.path.exists(SYSTEMD_UNIT_PATH):
        return

    unit_str = f"""[Unit]
Description=atproto personal data server

[Service]
WorkingDirectory={PDS_REPO_PATH}/service
ExecStart=node index.js
Restart=on-failure
EnvironmentFile={PDS_REPO_PATH}/service/.env

[Install]
WantedBy=default.target
"""

    with open("pds.service", "w") as f:
        f.write(unit_str)
    run(f"sudo mv pds.service {SYSTEMD_UNIT_PATH}")


def start_pds():
    run("sudo systemctl daemon-reload")
    run("sudo systemctl enable pds")
    run("sudo systemctl restart pds")


def checking_status():
    success = False
    max_retry = 5
    count = 0
    result: str | None = None
    while not success and count < max_retry:
        sleep(1)
        count += 1
        try:
            result = run("curl 127.0.0.1:3002/xrpc/_health", exit_on_error=False)
            success = True
        except CalledProcessError:
            print(f"Retrying ({count}) ...")

    if "version" not in result:
        print(f"Cannot check PDS status.")
        print(f"Navigate to 127.0.0.1:3002/xrpc/_health to check status.")


# run setup ====================================================
if __name__ == '__main__':
    step = 0


    def msg(info):
        global step
        step += 1
        print(f"[{step}]", info)


    check_requirements()

    msg("Cloning/updating pds repository ...")
    get_repo()

    msg("Setting up .env ...")
    setup_env()

    msg("Setting up service ...")
    setup_service()

    msg("Setting up systemd unit ...")
    setup_systemd_unit()

    msg("Starting PDS ...")
    start_pds()

    msg("Checking PDS status ...")
    checking_status()

    print("Done!")
