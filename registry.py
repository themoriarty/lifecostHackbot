import xmpp

class Registry(object):
    __slots__ = ["persons"]
    def __init__(self):
        self.persons = {}
    def onPresence(self, person, nickname, is_alive):
        nickname = unicode(nickname)
        if is_alive:
            if nickname in self.persons:
                print "there is already %s with nickname %s" % (self.persons[nickname], nickname)
            self.persons[nickname] = person
        else:
            if nickname in self.persons:
                del self.persons[nickname]
                return False
        return True

    def __str__(self):
        return (u"Registry: " + u", ".join(["%s: %s" % (k, v) for k, v in self.persons.items()])).encode("utf-8")

    def __getitem__(self, nickname):
        nickname = unicode(nickname)
        return self.persons[nickname]

    def getNick(self, jid):
        ret = [n for n, p in self.persons.items() if p == jid]
        if ret:
            return ret[0]
        return None
