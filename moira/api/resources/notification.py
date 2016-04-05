from moira.api.request import delayed
from twisted.internet import defer
from moira.api.resources.redis import RedisResouce


class Notifications(RedisResouce):

    def __init__(self, db):
        RedisResouce.__init__(self, db)

    @delayed
    @defer.inlineCallbacks
    def render_GET(self, request):
        notifications, total = yield self.db.getNotifications(request.args.get('start')[0],
                                                              request.args.get('end')[0])
        self.write_json(request, {"list": notifications, "total": total})

    @delayed
    @defer.inlineCallbacks
    def render_DELETE(self, request):
        result = yield self.db.removeNotification(request.args.get('json')[0])
        self.write_json(request, {"result": result})

    def getChild(self, path, request):
        if not path:
            return self