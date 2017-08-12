""" Rootfile forservice """
from resources.lib.service_entry import Service

if __name__ == '__main__':
    service = Service()

    try:
        service.run()
    except Exception as e:
        service.shutdown()
