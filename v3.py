import uasyncio as asyncio


from src import zenautomate as ZenAutomate
from src import zenoutput4x4 as ZenOutput4x4
from src import divers


# Création des objets
arnaudmeuble = ZenOutput4x4.ZenOutput4x4()
automate_main = ZenAutomate.ZenAutomate(arnaudmeuble)

async def main():
    await automate_main.run()

asyncio.run(main())

#TODO : ne faudrait il pas faire un objet buffer ?
# cel pourrait faire parti d'un objet "programme" qui serait associé a automate et qui pourrait etre utlisé en interne ou par d'autre automates 


