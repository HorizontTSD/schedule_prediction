#!/usr/bin/env python3
import subprocess
import socket

containers = {
    "tool_backend": {
        "name": "tool_backend",
        "in_port": 7070,
        "out_port": 7070,
        "container_id": "c2177ee3f4c7",
        "env_file": "Study/tool_backend/.env"
    },
    "schedule_prediction": {
        "name": "schedule_prediction",
        "in_port": 7072,
        "out_port": 7070,
        "container_id": "832adee2736f",
        "env_file": "horizon/schedule_prediction/.env"
    },
    "horizon_orchestrator_auth": {
        "name": "horizon_orchestrator_auth",
        "in_port": 8603,
        "out_port": 7070,
        "container_id": "3c938741bd43",
        "env_file": "horizon/horizon_orchestrator/.env"
    },
    "horizon_orchestrator": {
        "name": "horizon_orchestrator",
        "in_port": 7071,
        "out_port": 7070,
        "container_id": "2429071f1e5f",
        "env_file": "horizon/horizon_orchestrator/.env"
    },
    "auth_service_horizon": {
        "name": "auth_service_horizon",
        "in_port": 8601,
        "out_port": 7070,
        "container_id": "7e0ebabcc437",
        "env_file": "horizon/auth_service_horizon/.env"
    },
    "set_schedule_forecast": {
        "name": "set_schedule_forecast",
        "in_port": 8084,
        "out_port": 7070,
        "container_id": "c8f47f663f43",
        "env_file": "horizon/auth_service_horizon/.env"
    },

}

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def kill_process_on_port(port):
    try:
        cid = subprocess.check_output(
            ["sudo", "docker", "ps", "-q", "--filter", f"publish={port}"]
        ).decode().strip()
        if cid:
            subprocess.run(["sudo", "docker", "rm", "-f", cid])
    except subprocess.CalledProcessError:
        pass


def run_container(cfg):
    if is_port_in_use(cfg["out_port"]):
        kill_process_on_port(cfg["out_port"])
    subprocess.run(
        [
            "sudo", "docker", "rm", "-f", cfg["name"]
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    cmd = [
        "sudo", "docker", "run", "-d",
        "--name", cfg["name"],
        "--env-file", cfg["env_file"],
        "-p", f'{cfg["in_port"]}:{cfg["out_port"]}',
        cfg["container_id"]
    ]
    subprocess.run(cmd, check=True)

def main():
    for key, cfg in containers.items():
        print(f"Запускаю {cfg['name']}...")
        run_container(cfg)

if __name__ == "__main__":
    main()
