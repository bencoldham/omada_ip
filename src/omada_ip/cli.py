import asyncio

import typer

from omada_ip.core import PppoeRenewer, WanResetRenewer, run_renew_ip

app = typer.Typer()


@app.command()
def pppoe():
    asyncio.run(run_renew_ip(PppoeRenewer, delay=60))
    print("PPPoE renewal complete.")


@app.command()
def wan():
    asyncio.run(run_renew_ip(WanResetRenewer, delay=30))
    print("WAN port renewal complete.")


if __name__ == "__main__":
    app()
