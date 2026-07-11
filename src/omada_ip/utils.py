import requests


def get_public_ip():
    response = requests.get("https://api.ipify.org")
    return response.text
