import inspect
from typing import Any
import inspect


from parse import parse
from webob import Request, Response
from requests import Session as RequestsSession
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter


class API:
    def __init__(self) -> None:
        self.routes = {}

    def __call__(self, environ, start_response, *args: Any, **kwds: Any) -> Any:
        request = Request(environ)

        response = self.handle_request(request)

        return response(environ, start_response)


    def find_handler(self, request_path):
        for path, handler in self.routes.items():
            parse_result = parse(path, request_path)
            if parse_result is not None:
                return handler, parse_result.named

        return None, None

    def handle_request(self, request):
        response = Response()

        handler, kwargs = self.find_handler(request_path=request.path)

        if handler is not None:
            if inspect.isclass(handler):
                handler = getattr(handler(), request.method.lower(), None)
                if handler is None:
                    raise AttributeError("Method not allowed", request.method)

            handler(request, response, **kwargs)
        else:
            self.default_response(response)

        return response

    def route(self, path):
        def wrapper(handler):
            self.add_route(path, handler)
            return handler

        return wrapper


    def add_route(self, path, handler):
        if path in self.routes:
            raise ValueError("Such route already exists.")

        self.routes[path] = handler

    def default_response(self, response):
        response.status_code = 404
        response.text = "Not found."

    def test_session(self, base_url="http://testserver"):
        session = RequestsSession()
        session.mount(prefix=base_url, adapter=RequestsWSGIAdapter(self))
        return session