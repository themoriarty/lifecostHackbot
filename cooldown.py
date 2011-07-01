import logic
import time

gCooldowns = {}

def setCooldown(who, action, delta):
    global gCooldowns
    newCooldown = time.time() + delta
    k = (who, action)
    if gCooldowns.get(k, 0) < newCooldown:
        gCooldowns[k] = newCooldown

def wasKilled(who):
    setCooldown(who, 'enter', logic.getCooldownOnKilled(who))

def didExit(who):
    setCooldown(who, 'enter', logic.getCooldownOnExit(who))

def startedAttack(who):
    setCooldown(who, 'attack', logic.getCooldownOnAttack(who))

def can(who, action):
    return time.time() > gCooldowns.get((who, action), 0)

def canEnter(who):
    return can(who, 'enter')

def canAttack(who):
    return can(who, 'attack')
