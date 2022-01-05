from aiohttp import web
import asyncio
from alas_controller import AlasController
from multiprocessing import Process

alas = AlasController()
p = Process(target=alas.run)

async def welcome(request):
    name = "https://github.com/LmeSzinc/AzurLaneAutoScript"
    text = "Hello, " + name
    return web.Response(text=text)

async def run(request):
    """ Run alas GUI """
    if not p.is_alive():
        try:
            p.start()
        except:
            text = "Alas running failed"
            return web.Response(text=text)
        # p.join()
        text = "Alas is running"
        return web.Response(text=text)
    else:
        text = "Alas is already running"
        return web.Response(text=text)
    
async def update(request):
    global p
    """ update Alas """
    if p.is_alive():
        p.terminate()
    alas.update()
    
    """ Restart alas """
    p = Process(target=alas.run)
    p.start()
    text = "Alas updated"
    return web.Response(text=text)

async def restart(request):
    global p
    """ restart Alas """
    if p.is_alive():
        p.terminate()

    p = Process(target=alas.run)
    p.start()
    text = "Alas is running"
    return web.Response(text=text)

async def stop(request):
    global p
    """ stop Alas """
    if p.is_alive():
        p.terminate()
        text = "Alas stopped"
        return web.Response(text=text)
    else:
        text = "Alas is not running"
        return web.Response(text=text)

app = web.Application()
app.add_routes([web.get('/', welcome),
                web.get('/run',run),
                web.get('/update',update),
                web.get('/restart',restart),
                web.get('/stop',stop)
                ])

if __name__ == '__main__':
    port = 18870
    host = '0.0.0.0'
    web.run_app(app,  host=host, port=port)
    