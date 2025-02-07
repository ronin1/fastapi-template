# import os
from locust import HttpUser, task


# SEE: https://locust.io
class PingOnly(HttpUser):

    @task
    def nginx(self) -> None:
        self.client.get("/")

    @task
    def api(self) -> None:
        self.client.get("/color")

    @task
    def worker(self) -> None:
        self.client.get("/worker")
