from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

IP_CHECK_TIMEOUT = 2  # seconds
PPPOE_REDIAL_INTERVAL = 2

CONFIG_DIR = Path.home() / ".config" / "omada_ip"
ENV_FILE = CONFIG_DIR / ".env"


class IpConfig(BaseSettings):
    url: str = Field(..., alias="URL")
    omada_user: str = Field(..., alias="OMADA_USER")
    omada_pass: str = Field(..., alias="OMADA_PASS")
    site_id: str = Field(..., alias="SITE_ID")
    mac: str = Field(..., alias="MAC")
    wan_mac: str = Field(..., alias="WAN_MAC")
    port_uuid: str = Field(..., alias="PORT_UUID")
    isp_user: str = Field(..., alias="ISP_USER")
    isp_password: str = Field(..., alias="ISP_PASS")

    model_config = SettingsConfigDict(env_file=ENV_FILE)


config = IpConfig()
