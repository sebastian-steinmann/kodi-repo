""" Rootfile forservice """
from resources.lib.service_entry import Service

def run():
    service = Service()

    try:
        service.run()
    except Exception as e:
        service.shutdown()

if __name__ == '__main__':
    run()
