# -*- coding: utf-8 -*-

#это базовые настройки для level = 0, меняются в зависимости от уровня хакера/система
offenderVitality = 20
defenderVitality = 50
systemVitality = 100
offenderDamage = 40
questionTime = 10

#количество хитов, снимаемое с нападающих, всегда одинаковое
defenderDamage = 10

#эталонное время для системы уровня 0, по которому определяется награда за ее взлом.
#диапазон делится на 2 части, если систему взломали за 30 секунд - самая большая награда, за 60 секунд - поменьше, больше 60 секунд - самая маленькая
defendSystemTime = 60

#константы
directAttackCooldown = 5
directAttackTime = 10
directAttackDamageOffender = 1
directAttackDamageDefender = 10

#тоже константы - через сколько секунд можно:
cooldownOnKilled = 20  #зайти в любой канал после смерти
cooldownOnExit = 10    #зайти на любой канал после добровольного выхода
cooldownOnAttack = 60  #атаковать после *начала* предыдущей атаки


#а это уже настройки
conference = "conference.ya.ru"
server = "ya.ru"
nickname = u"Система"
mainChannel = "lcb2"
baseUrl = "http://billing.lifecost.tv/"
