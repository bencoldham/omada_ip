import requests


def get_public_ip():
    response = requests.get("https://api.ipify.org", timeout=300)
    return response.text
