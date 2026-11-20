"""Bound request bodies before FastAPI buffers and parses them."""
from starlette.types import ASGIApp, Message, Receive, Scope, Send


MAX_COLLECTION_PAGE_BODY_BYTES = 6_100_000
MAX_SOCIAL_INGEST_BODY_BYTES = 512_000


class CollectionPageBodyLimitMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http' or scope['method'] != 'POST':
            await self.app(scope, receive, send)
            return

        limit = {
            '/api/collection/pages': MAX_COLLECTION_PAGE_BODY_BYTES,
            '/api/v1/ingest/social': MAX_SOCIAL_INGEST_BODY_BYTES,
        }.get(scope['path'])
        if limit is None:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get('headers', []))
        try:
            content_length = int(headers.get(b'content-length', b''))
        except ValueError:
            content_length = 0
        if content_length > limit:
            await self._reject(send)
            return

        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            if len(body) + len(chunk) > limit:
                await self._reject(send)
                return
            body.extend(chunk)
            if not message.get('more_body', False):
                break

        cached_body = bytes(body)
        delivered = False

        async def replay_receive() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': cached_body, 'more_body': False}
            return await receive()

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _reject(send: Send) -> None:
        body = b'{"detail":"request body too large"}'
        await send({
            'type': 'http.response.start',
            'status': 413,
            'headers': [
                (b'content-type', b'application/json'),
                (b'content-length', str(len(body)).encode('ascii')),
            ],
        })
        await send({'type': 'http.response.body', 'body': body})
