#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import xmpp

from confs import getConfs, getConfByTarget, getConfByName
from utils import sEq, answerPrivate, answerConf, getConferenceJid, normalize, protect
from registry import Registry
from logic import *

import config
import cooldown
import background

registry = Registry()

def onPrivateMessage(conn, msg):
    answerPrivate(conn, msg, u"Я не бот!")

@protect
def onMessage(conn, msg):
    if msg.getFrom().getDomain() != config.conference:
        return onPrivateMessage(conn, msg)

    if msg.getFrom().getNode() != config.mainChannel:
        return onBattleMessage(conn, msg, msg.getFrom().getNode())

    processCommand(conn, msg, msg.getBody())

@protect
def onPresence(conn, msg):
    if msg.getFrom().getDomain() == config.conference:
        conf, nickname = msg.getFrom().getNode(), msg.getFrom().getResource()
        role = msg.getTag("x", namespace = xmpp.NS_MUC_USER)
        if role and role.getTag("item").getAttr("jid"):
            person = xmpp.JID(role.getTag("item").getAttr("jid"))
            alive = role.getTag("item").getAttr("role") != "none" and msg.getAttr("type") != "unavailable"
            #print "%s: %s is %s and is he alive: %s" % (conf, person, nickname, alive)
            if conf == config.mainChannel:
                registry.onPresence(person, nickname, alive)
            else:
                confObj = getConfByName(conf)
                if confObj:
                    confObj.onPresence(conn, person, nickname, alive)

def onBattleMessage(conn, msg, confName):
    conf = getConfByName(confName)
    if conf:
        conf.onMessage(conn, msg)


@protect
def sendInvite(conn, to, conf):
    invite = xmpp.Message(to = xmpp.JID(node = conf, domain = config.conference))
    invite.setTag('x', namespace = xmpp.NS_MUC_USER).setTag('invite', {'to': to})
    conn.send(invite)

def processCommand(conn, msg, msgText):
    parts = [normalize(x) for x in msgText.strip().split(" ")]
    if len(parts) != 3:
        return
    cmd, target, action = parts
    is_defend = sEq(action, u"защита")
    is_offend = sEq(action, u"атака")
    if sEq(cmd, "connect") and (is_offend or is_defend):
        person = registry[msg.getFrom().getResource()]
        if isValidTarget(person, target) and cooldown.canEnter(person):
            if is_offend and not cooldown.canAttack(person):
                answerPrivate(conn, msg, u"Передохни, выпей пивка")
                return
            conf = getConfByTarget(target)
            joinConference(conn, config.conference, conf.name, config.nickname)
            sendInvite(conn, person, conf.name)
            if is_offend:
                conf.newOffender(person)
                cooldown.startedAttack(person)
            else:
                conf.newDefender(person)
        else:
            answerPrivate(conn, msg, u"Тебе туда нельзя")


def doStep(conn):
    try:
        return conn.Process(0.1)
    except KeyboardInterrupt: 
        return 0

def doIdle(conn):
    toDelete = []
    for target, conf in getConfs().iteritems():
        if conf.idle(conn):
            toDelete.append(target)

    for t in toDelete:
        del getConfs()[t]

def joinConference(conn, server, room, nickname, password = ""):
    p = xmpp.Presence(to = xmpp.JID(node = room, domain = server, resource = nickname))
    p.setTag('x',namespace=xmpp.NS_MUC).setTagData('password', password)
    p.getTag('x').addChild('history',{'maxchars':'0','maxstanzas':'0'})
    conn.send(p)


def main(name):
    if len(sys.argv)<3:
        print "Usage: bot.py username@server.net password"
    else:
        background.start()

        jid = xmpp.JID(node = sys.argv[1], domain = config.server, resource = "LC")
        user, server, password = jid.getNode(), jid.getDomain(),sys.argv[2]

        conn = xmpp.Client(server, debug=[])
        conres = conn.connect()
        if not conres:
            print "Unable to connect to server %s!"%server
            return 1
        if conres<>'tls':
            print "Warning: unable to estabilish secure connection - TLS failed!"
        
        authres = conn.auth(user,password)
        if not authres:
            print "Unable to authorize on %s - check login/password."%server
            return 1
        if authres != 'sasl':
            print "Warning: unable to perform SASL auth os %s. Old authentication method used!"%server

        conn.RegisterHandler('message', onMessage)
        conn.RegisterHandler('presence', onPresence)
        conn.sendInitPresence()
        joinConference(conn, config.conference, room = config.mainChannel, nickname = name, password = "")
        print "Bot started."

        counter = 10
        while True:
            result = doStep(conn)
            if result == 0:
                break
            if result == '0' or counter == 0:
                doIdle(conn)
                counter = 10
            else:
                counter -= 1


if __name__ == "__main__":
    sys.exit(main(config.nickname))
