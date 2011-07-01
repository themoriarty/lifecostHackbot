import hashlib
import random
import traceback

import xmpp

import config


def protect(func):
    def impl(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            print traceback.format_exc()
            return None
    return impl

def normalize(s):
    return s.strip().lower()

def sEq(s1, s2):
    return normalize(s1) == normalize(s2)

def randStr():
    return hashlib.md5(str(random.getrandbits(1000))).hexdigest()

def jidStrip(person):
    j = xmpp.JID(person)
    #return str(xmpp.JID(node = j.getNode(), domain = j.getDomain())).lower()
    return j.getNode().lower()

def getConferenceJid(fullJid):
    return xmpp.JID(fullJid).getStripped()

def answerPrivate(conn, msg, text):
    conn.send(xmpp.Message(to = msg.getFrom(), body = text, typ = "chat"))

def sendPrivate(conn, person, text):
    conn.send(xmpp.Message(to = person, body = text, typ = "chat"))

def answerConf(conn, msg, text):
    conn.send(xmpp.Message(to = getConferenceJid(msg.getFrom()), body = text, typ = "groupchat"))

def sendConf(conn, confName, text, cb = None):
    msg = xmpp.Message(to = xmpp.JID(node = confName, domain = config.conference), body = text, typ = "groupchat")
    if not cb:
        conn.send(msg)
    else:
        conn.SendAndCallForResponse(msg, cb, {})

def sendKick(conn, confName, persons, text):
    msg = xmpp.Iq(to = xmpp.JID(node = confName, domain = config.conference), typ = "set")
    q = msg.setTag("query", namespace = xmpp.NS_MUC_ADMIN)
    for p in [x for x in persons if x]:
        q.setTag("item", {"nick": p, "role": "none"}).addData(text)
    conn.send(msg)

def leaveConf(conn, confName):
    p = xmpp.Presence(to = xmpp.JID(node = confName, domain = config.conference, resource = config.nickname), typ='unavailable')
    conn.send(p)
