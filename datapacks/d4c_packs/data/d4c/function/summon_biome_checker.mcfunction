$execute as $(name) at @s rotated 0 0 positioned ~ 308 ~ summon minecraft:villager run tag @s add D4C_biomechecker
effect give @e[tag=D4C_biomechecker,limit=1] minecraft:invisibility infinite 1 true
attribute @e[tag=D4C_biomechecker,limit=1] minecraft:gravity base set 0
data modify entity @e[tag=D4C_biomechecker,limit=1] Silent set value 1b