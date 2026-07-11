import asyncio
import time
from abc import ABC, abstractmethod

from loguru import logger as l
from tplink_omada_client.omadaapiconnection import OmadaApiConnection

from omada_ip.config import IP_CHECK_TIMEOUT, PPPOE_REDIAL_INTERVAL, IpConfig, config
from omada_ip.utils import get_public_ip


class IpRenewer(ABC):
    def __init__(self, cfg: IpConfig):
        self.cfg = cfg

    @property
    @abstractmethod
    def http_method(self) -> str: ...

    @property
    @abstractmethod
    def base_url(self) -> str: ...

    @abstractmethod
    def payload(self, turn_on: bool) -> dict: ...

    async def send_payload(self, api: OmadaApiConnection, turn_on: bool):
        target_url = api.format_url(self.base_url, self.cfg.site_id)
        l.info(f"Sending {turn_on=} to {target_url=}")

        payload = self.payload(turn_on)

        response = await api.request(self.http_method, target_url, json=payload)
        l.info(f"{response=}")

    async def renew_ip(self, delay: int) -> None:
        start_time = time.time()
        async with OmadaApiConnection(
            self.cfg.url,
            self.cfg.omada_user,
            self.cfg.omada_pass,
            verify_ssl=False,
        ) as api:
            await api.login()
            old_ip = await get_public_ip(IP_CHECK_TIMEOUT)

            l.info(f"Previous IP: {old_ip}")

            await self.send_payload(api, turn_on=False)
            await asyncio.sleep(delay)
            await self.send_payload(api, turn_on=True)

            new_ip = await get_public_ip(IP_CHECK_TIMEOUT)
            l.info(f"New IP: {new_ip}; took {(time.time() - start_time):.2f}s")

            if old_ip == new_ip:
                l.warning("IP address was not changed.")
            else:
                l.info("IP address changed successfully.")


class WanResetRenewer(IpRenewer):
    @property
    def http_method(self) -> str:
        return "put"

    @property
    def base_url(self) -> str:
        return f"gateways/{self.cfg.mac}/ports"

    def payload(self, turn_on: bool):
        return {
            "port": 2,
            "status": int(turn_on),
            "linkSpeed": 0,
            "duplex": 0,
            "flowControl": False,
            "loopbackControl": 0,
        }


class PppoeRenewer(IpRenewer):
    @property
    def http_method(self) -> str:
        return "patch"

    @property
    def base_url(self) -> str:
        return "wan/networks/port-setting"

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
                        "redialInterval": str(PPPOE_REDIAL_INTERVAL),
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


async def run_renew_ip(ip_renewer: type[IpRenewer], delay: int):
    renewer = ip_renewer(cfg=config)
    await renewer.renew_ip(delay=delay)
