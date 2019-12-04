from abc import ABC
from typing import Any

from pyctuator.pyctuator_impl import PyctuatorImpl


class PyctuatorRouter(ABC):

    def __init__(
            self,
            app: Any,
            pyctuator_impl: PyctuatorImpl,
    ):
        self.app = app
        self.pyctuator_impl = pyctuator_impl
