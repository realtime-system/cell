"""cl.result"""

from __future__ import absolute_import, with_statement

from cl.exceptions import clError, NoReplyError


class AsyncResult(object):
    Error = clError
    NoReplyError = NoReplyError

    def __init__(self, ticket, actor):
        self.ticket = ticket
        self.actor = actor

    def _first(self, replies):
        if replies is not None:
            replies = list(replies)
            if replies:
                return replies[0]
        raise self.NoReplyError("No reply received within time constraint")

    def get(self, **kwargs):
        return self._first(self.gather(**dict(kwargs, limit=1)))

    def gather(self, limit=None, timeout=2, propagate=False, **kwargs):
        gather = self._gather
        producers = self.actor.producers
        with producers.acquire(block=True) as producer:
            for r in gather(producer.connection, producer.channel, self.ticket,
                            limit=limit, propagate=propagate,
                            timeout=timeout, **kwargs):
                yield r

    def _gather(self, *args, **kwargs):
        return (self.to_python(reply, propagate=kwargs.pop("propagate", False))
                    for reply in self.actor._collect_replies(*args, **kwargs))

    def to_python(self, reply, propagate=False):
        try:
            return reply["ok"]
        except KeyError:
            error = self.Error(*reply.get("nok") or ())
            if propagate:
                raise error
            return error