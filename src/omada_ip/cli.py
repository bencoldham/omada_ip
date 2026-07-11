import asyncio

import typer

from omada_ip.core import PppoeRenewer, WanResetRenewer, run_renew_ip

app = typer.Typer()


@app.command()
def pppoe(delay: int = 5):
    asyncio.run(run_renew_ip(PppoeRenewer, delay=delay))
    print("PPPoE renewal complete.")


@app.command()
def wan(delay: int = 60):
    asyncio.run(run_renew_ip(WanResetRenewer, delay=delay))
    print("WAN port renewal complete.")


if __name__ == "__main__":
    app()
