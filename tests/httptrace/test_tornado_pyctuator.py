from tornado.httputil import HTTPHeaders

from pyctuator.impl.tornado_pyctuator import get_headers


def test_get_headers() -> None:
    tornado_headers = HTTPHeaders({"content-type": "text/html"})
    tornado_headers.add("Set-Cookie", "A=B")
    tornado_headers.add("Set-Cookie", "C=D")
    assert get_headers(tornado_headers) == {
        "content-type": ["text/html"],
        "set-cookie": ["A=B", "C=D"]
    }
