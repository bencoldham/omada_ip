import asyncio
from abc import ABC, abstractmethod

from loguru import logger as l
from tplink_omada_client.omadaapiconnection import OmadaApiConnection

from omada_ip.config import IpConfig, config
from omada_ip.utils import get_public_ip


class IpRenewer(ABC):
    def __init__(self, cfg: IpConfig):
        self.cfg = cfg

    @property
    def base_url(self) -> str:
        return f"gateways/{self.cfg.mac}/ports"

    @abstractmethod
    def payload(self, turn_on: bool) -> dict: ...

    @abstractmethod
    async def send_payload(self, api: OmadaApiConnection, turn_on: bool): ...

    async def renew_ip(self, delay: int) -> None:
        async with OmadaApiConnection(
            self.cfg.url,
            self.cfg.omada_user,
            self.cfg.omada_pass,
            verify_ssl=False,
        ) as api:
            await api.login()
            l.info(f"Previous IP: {get_public_ip()}")

            await self.send_payload(api, turn_on=False)
            await asyncio.sleep(delay)
            await self.send_payload(api, turn_on=True)

            l.info(f"New IP: {get_public_ip()}")


class WanResetRenewer(IpRenewer):
    def payload(self, turn_on: bool):
        return {
            "port": 2,
            "status": int(turn_on),
            "linkSpeed": 0,
            "duplex": 0,
            "flowControl": False,
            "loopbackControl": 0,
        }

    @property
    def base_url(self) -> str:
        return f"gateways/{self.cfg.mac}/ports"

    async def send_payload(self, api: OmadaApiConnection, turn_on: bool):
        target_url = api.format_url(self.base_url, self.cfg.site_id)
        l.info(f"Sending {turn_on=} to {self.cfg.mac} Port 2.... URL = {target_url}")

        json = self.payload(turn_on)
        l.info(f"{json=}")

        response = await api.request("put", target_url, json=json)
        l.info(f"Response: {response}")


class PppoeRenewer(IpRenewer):
    def payload(self, turn_on: bool):
        return {
            "wanPortSetting": {
                "portUuid": self.cfg.port_uuid,
                "portDesc": "null",
                "wanPortIpv4Setting": {
                    "portUuid": self.cfg.port_uuid,
                    "portDesc": "null",
                    "proto": "pppoe",
                    "vlanId": 0,
                    "supportQosTagEnable": "true",
                    "supportInternetVlan": "true",
                    "qosTagEnable": "false",
                    "vlanPriority": 0,
                    "ipv4Pppoe": {
                        "mtu": 1492,
                        "mru": 1492,
                        "dns1": "1.1.1.1",
                        "dns2": "1.0.0.1",
                        "userName": self.cfg.isp_user,
                        "password": self.cfg.isp_password,
                        "ipFromIsp": "on",
                        "linkType": "auto" if turn_on else "manual",
                        "mssClampingType": 1,
                        "mssClampingValue": "null",
                        "ipv4Connection2": {
                            "proto": "static",
                            "ipaddr": "192.168.100.2",
                            "netmask": "255.255.255.0",
                        },
                    },
                },
                "wanPortMacSetting": {
                    "method": "set",
                    "mac": self.cfg.wan_mac,
                    "portUuid": self.cfg.port_uuid,
                },
                "wanPortIpv6Setting": {
                    "portUuid": self.cfg.port_uuid,
                    "enable": 0,
                },
            },
            "type": 0,
        }

    async def send_payload(self, api: OmadaApiConnection, turn_on: bool):
        target_url = api.format_url(f"gateways/{self.cfg.mac}/ports", self.cfg.site_id)
        l.info(f"Sending port reset to {self.cfg.mac} Port 2.... URL = {target_url}")
        response = await api.request("put", target_url, json=self.payload(turn_on))
        l.info(f"Response: {response}")


async def run_renew_ip(ip_renewer: type[IpRenewer], delay: int):
    renewer = ip_renewer(cfg=config)
    await renewer.renew_ip(delay=delay)
