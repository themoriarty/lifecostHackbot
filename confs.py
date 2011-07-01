# -*- coding: utf-8 -*-
import time
import traceback
import random

import xmpp

import utils
import config
import logic
import cooldown
import background
from registry import Registry

gConferences = {}

class Person(object):
    __slots__ = ["name", "health", "last_attack", "attacks"]
    def __init__(self, name, health):
        self.name, self.health = name, health
        self.last_attack = 0
        self.attacks = {}

    def revive(self, value):
        self.health = value

    def __str__(self):
        return "Person(name = %s, health = %d)" % (self.name, self.health)

    def isDead(self):
        return self.health <= 0

    def onExit(self, killed):
        if killed:
            cooldown.wasKilled(self.name)
        else:
            cooldown.didExit(self.name)
            self.health = -100

    def damage(self, conn, by, amount, conf):
        self.health -= amount
        print "damaged %s by %s by %d" % (self, by, amount)
        utils.sendConf(conn, conf, u"%s наносит %s повреждений: %d" % (by.name, self.name, amount))
        if self.isDead() and by:
            utils.sendPrivate(conn, by.name, u"Личный код атакующего %s" % self.name)


    def canAttack(self):
        return time.time() - self.last_attack > logic.getDirectAttackCooldown(self.name)

    def scheduleAttack(self, by, code, by_defender):
        self.attacks[time.time() + logic.getDirectAttackTime(by.name, self.name)] = (by, code, by_defender)
        if by.last_attack < time.time():
            by.last_attack = time.time()
        print "scheduled attack for %s by %s" % (self, by)

    def doDefend(self, code):
        correctCode = "".join(reversed(code))
        for t in [k for k, v in self.attacks.items() if v[1] == correctCode]:
            print "defended %s by %s" % (self, self.attacks[t][0]) 
            del self.attacks[t]

    def idle(self, conn, conf):
        currentTime = time.time()
        for k, v in self.attacks.items():
            if currentTime >= k:
                self.damage(conn, v[0], logic.getDirectAttackDamage(v[0], self.name, v[2]), conf)
                del self.attacks[k]

class Conf(object):
    __slots__ = ["target", "name", "health", "next_question", "defenders", "offenders", "question", "start_time", "registry", "cooldowns", "questions"]
    def __init__(self, target, name = None):
        self.target = target
        self.name = name if name else utils.randStr()
        self.health = logic.getSystemVitality(self.target)
        self.next_question = time.time() + 5
        self.start_time = self.next_question

        self.defenders = {}
        self.offenders = {}

        self.cooldowns = {}

        self.questions = logic.getQuestions(self.target)
        self.question = None
        self.registry = Registry()

#     def onExit(self, person):
#         self.cooldowns[person] = time.time() + logic.getCooldownOnExit(person, self.target)

#     def onEnter(self, conn, person, nickname):
#         if self.cooldowns.get(person, 0) > time.time():
#            utils.sendKick(conn, self.name, [nickname], u"Отдохни!")

    @utils.protect
    def onPresence(self, conn, person, nickname, alive):
        if not self.registry.onPresence(person, nickname, alive) and self.findPerson(person):
            self.findPerson(person).onExit(False)
#            self.onExit(person)
#        else:
#            self.onEnter(conn, person, nickname)

    def revive(self):
        self.health = logic.getSystemVitality(self.target)
        [person.revive(logic.getVitalityDefend(name, self.target)) for name, person in self.defenders.items()]

    def __str__(self):
        return unicode(u"Conference(target = %s, name = %s, health = %s, defenders = [%s], offenders = [%s]" % (self.target, self.name, self.health, ", ".join("(%s: %s)" % (k, v) for k, v in self.defenders.iteritems()), ", ".join("(%s: %s)" % (k, v) for k, v in self.offenders.iteritems()))).encode("utf-8")

    def newOffender(self, p):
        if p not in self.offenders:
            self.offenders[p] = Person(p, logic.getVitalityOffend(p, self.target))

    def newDefender(self, p):
        if p not in self.defenders:
            self.defenders[p] = Person(p, logic.getVitalityDefend(p, self.target))

    def idle(self, conn):
        if self.allDone():
            msg = u"Конец!"
            if self.defeated():
                msg = logic.getReward(self.target, time.time() - self.start_time)
                background.getUrlBackground("hack_done.php?", {"hackers": ",".join(x.getNode() for x in self.offenders.keys()), "target": self.target})

            utils.sendConf(conn, self.name, msg, lambda sess, s: utils.leaveConf(conn, self.name))
            return True

        if not self.offenders:
            self.revive()               

        for l in [self.defenders, self.offenders]:
            [p.idle(conn, self.name) for p in l.values()]

        self.kickDeads(conn)

        currentTime = time.time()
        if currentTime > self.next_question:
            self.question = self.nextQuestion()
            self.next_question = currentTime + self.question.timeout
            #utils.sendConf(conn, self.name, u"%s (время: %d)" % (self.question.text, self.question.timeout))
            utils.sendConf(conn, self.name, self.question.text)
        return False

    def nextQuestion(self):
        return random.choice(self.questions)

    def allDone(self):
        return self.defeated()

    def defeated(self):
        return self.health <= 0

    def kickDeads(self, conn):
        toKick = []
        for l in [self.offenders, self.defenders]:
            toDelete = []
            for name, person in [x for x in l.iteritems() if x[1].isDead()]:
                toKick.append(self.registry.getNick(person.name))
                person.onExit(True)
                toDelete.append(name)
            for x in toDelete:
                del l[x]
        utils.sendKick(conn, self.name, toKick, u"Готов")
                
    def findPerson(self, person):
        for l in [self.offenders, self.defenders]:
            if person in l:
                return l[person]
        return None

    def onMessage(self, conn, msg):
        person = self.registry[msg.getFrom().getResource()]
        if not self.findPerson(person):
            return
        if self.question and utils.sEq(msg.getBody(), self.question.answer):            
            if person in self.offenders:
                damage = logic.getDamage(person, self.target)
                self.health -= damage
                if not self.defeated():
                    utils.answerConf(conn, msg, u"Нанесено урона: %d, осталось: %d" % (damage, self.health))
            elif person in self.defenders:
                for p in self.offenders.itervalues():
                    p.damage(conn, self.findPerson(person), logic.getDefenderDamage(person, self.target), self.name)
            else:
                return
            
            self.kickDeads(conn)

            self.question = None
            self.next_question = time.time() + 1
        else:
            parts = [utils.normalize(x) for x in msg.getBody().strip().split(" ")]
            if parts:
                {"stat": self.printStats, "attack": self.scheduleAttack, "defend": self.doDefend}.get(parts[0], lambda x, y, z: None)(conn, person, parts[1:])
    
    def printStats(self, conn, person, args):
        utils.sendConf(conn, self.name, str(self))

    def scheduleAttack(self, conn, person, args):
        attackPerson = self.findPerson(person)
        if not attackPerson or not attackPerson.canAttack():
            return
        try:
            code, target = args[0], args[1]
            if len(code) == 4 and int(code) >= 0:
                targetPerson = self.findPerson(self.registry[target])
                if targetPerson:
                    targetPerson.scheduleAttack(attackPerson, code, person in self.defenders)
        except:
            print traceback.format_exc()

    def doDefend(self, conn, person, args):
        defenderPerson = self.findPerson(person)
        if not defenderPerson:
            return
        try:
            code = args[0]
            if len(args) == 2:
                targetPerson = self.findPerson(self.registry[args[1]])
            else:
                targetPerson = defenderPerson
            targetPerson.doDefend(code)
        except:
            print traceback.format_exc()
            
                

def getConfs():
    global gConferences
    return gConferences

def getConfByTarget(targetRaw):
    target = utils.normalize(targetRaw)
    if target in getConfs():
        return getConfs()[target]
    newConf = Conf(target)
    print newConf
    getConfs()[target] = newConf
    return newConf

def getConfByName(name):
    ret = [c for (t, c) in getConfs().iteritems() if utils.sEq(c.name, name)]
    if ret:
        return ret[0]
    return None
