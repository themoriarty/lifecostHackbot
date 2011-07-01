# -*- coding: utf-8 -*-
import config
import random
import utils
import math
import background
import json

gData = {
    "targets": 
    {"test": 
     {"questions": [{"text": "1 - 1 = ", "answer": "0", "level": 1}, {"text": "2 * 2 = ", "answer": "4", "level": 2}, {"text": "3 * 3 * 3 = ", "answer": "27", "level": 3}, {"text": "4 * 4 = ", "answer": "16", "level": 2}],
      "rewards": ["small", "medium", "huge"],
      "level": 0
      }
     },
    "hackers":
        {"m0riarty@ya.ru":
             {"level": 1}
        },
    "questions":
        [{"text": "2 + 2 = ", "answer": "4", "level": 1}, {"text": "3 + 3 = ", "answer": "6", "level": 1}, {"text": "4 + 4 = ", "answer": "8", "level": 1}, {"text": "5 + 5 = ", "answer": "10", "level": 1}]
    }

def forTarget(v, target, decrease = False):
    lvl = float(gData["targets"][target]["level"])
    if decrease:
        return v / math.pow(2, lvl)
    else:
        return v * math.pow(2, lvl)

def forHacker(v, hacker, decrease = False):
    lvl = float(gData["hackers"][hacker]["level"])
    if decrease:
        return v / math.pow(2, lvl)
    else:
        return v * math.pow(2, lvl)

def isValidTarget(person, target):
    person = utils.jidStrip(person)
    return target in gData["targets"]

def getSystemVitality(target):
    return forTarget(config.systemVitality, target)

def getVitalityOffend(person, target):
    person = utils.jidStrip(person)
    return forHacker(forTarget(config.offenderVitality, target), person, True)

def getVitalityDefend(person, target):
    person = utils.jidStrip(person)
    return forHacker(config.defenderVitality, person)

def getDamage(person, target):
    person = utils.jidStrip(person)
    return forHacker(config.offenderDamage, person)

def getDefenderDamage(person, target):
    person = utils.jidStrip(person)
    return config.defenderDamage

def getReward(target, seconds):
    maxSeconds = forTarget(config.defendSystemTime, target)
    rewards = gData["targets"][target]["rewards"]
    if seconds <= maxSeconds / 2:
        return rewards[min(2, len(rewards) - 1)]
    if seconds <= maxSeconds:
        return rewards[min(1, len(rewards) - 1)]
    return rewards[0]

def getDirectAttackCooldown(person):
    person = utils.jidStrip(person)
    return config.directAttackCooldown

def getDirectAttackTime(atttacker, attackee):
    return config.directAttackTime

def getDirectAttackDamage(attacker, attackee, by_defender):
    return config.directAttackDamageDefender if by_defender else config.directAttackDamageOffender


def getCooldownOnExit(person):
    person = utils.jidStrip(person)
    return config.cooldownOnExit

def getCooldownOnKilled(person):
    person = utils.jidStrip(person)
    return config.cooldownOnKilled

def getCooldownOnAttack(person):
    person = utils.jidStrip(person)
    return config.cooldownOnAttack

class Question(object):
    __slots__ = ["timeout", "text", "level", "answer"]
    def __init__(self, target, text, answer, level):
        self.text, self.answer, self.level = text, answer, float(level)
        self.timeout = forTarget(config.questionTime, target, True)

def getQuestions(target):
    specialQuestions = [Question(target, **x) for x in gData["targets"][target]["questions"]]
    random.shuffle(specialQuestions)
    commonQuestions = [Question(target, **x) for x in gData["questions"]]
    random.shuffle(commonQuestions)
    questions = (specialQuestions + commonQuestions)[:30]
    #random.shuffle(questions)
    return questions



def updateData():
    global gData
    gData = json.loads(background.getUrl("hack_data.php"))

background.startForever(updateData, 10)
