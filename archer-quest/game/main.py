"""Point d'entrée. Ordinateur : `python main.py`. Web : `pygbag .` (voir README)."""
import asyncio

from archer.app import App


async def main():
    await App().run()


asyncio.run(main())
