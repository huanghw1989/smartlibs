from smart.rest import BootConfig, RestServiceApplication

boot = BootConfig()


@boot.crond()
@boot.service('app.*')
class TestRestApp(RestServiceApplication):
    pass
