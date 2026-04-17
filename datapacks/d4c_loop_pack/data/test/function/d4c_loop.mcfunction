# 並行世界での回復分身用
tp @n[type=mannequin,tag=D4C_alter_ego,tag=paralel] @n[type=wolf,tag=D4C_alter_ego,tag=paralel]
# オオカミが攻撃対象としているエンティティをマネキンが攻撃する。条件は攻撃射程距離（distance）に入る必要がある。on attackerによってコマンド実行者が変わるため注意。
execute as @n[type=wolf,tag=D4C_alter_ego,tag=paralel] at @s on attacker if entity @e[distance=..5,tag=D4C_alter_ego,tag=paralel] run damage @s 5 minecraft:player_attack by @n[type=mannequin,tag=D4C_alter_ego,tag=paralel]
# 上記と同条件にすることで攻撃とほぼ同時に攻撃モーションを行う。
execute as @n[type=wolf,tag=D4C_alter_ego,tag=paralel] at @s on attacker if entity @s[distance=..5,tag=D4C_alter_ego,tag=paralel] run swing @n[type=mannequin,tag=D4C_alter_ego,tag=paralel] mainhand
# もしマネキンが何らかの理由でワールドに存在しないなら追従元のオオカミもkillする。この時ログに出力されないよう主従関係を断つ。
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=paralel] run data modify entity @e[type=wolf,tag=D4C_alter_ego,tag=paralel,limit=1] Owner set value []
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=paralel] run kill @e[type=wolf,tag=D4C_alter_ego,tag=paralel]

# 残機用
tp @n[type=mannequin,tag=D4C_alter_ego,tag=0] @n[type=wolf,tag=D4C_alter_ego,tag=0]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=0] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=0] run damage @s 5 minecraft:player_attack by @n[type=mannequin,tag=D4C_alter_ego,tag=0]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=0] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=0] run swing @n[type=mannequin,tag=D4C_alter_ego,tag=0] mainhand
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=0] run data modify entity @e[type=wolf,tag=D4C_alter_ego,tag=0,limit=1] Owner set value []
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=0] run kill @e[type=wolf,tag=D4C_alter_ego,tag=0]

tp @n[type=mannequin,tag=D4C_alter_ego,tag=1] @n[type=wolf,tag=D4C_alter_ego,tag=1]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=1] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=1] run damage @s 5 minecraft:player_attack by @n[type=mannequin,tag=D4C_alter_ego,tag=1]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=1] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=1] run swing @n[type=mannequin,tag=D4C_alter_ego,tag=1] mainhand
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=1] run data modify entity @e[type=wolf,tag=D4C_alter_ego,tag=1,limit=1] Owner set value []
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=1] run kill @e[type=wolf,tag=D4C_alter_ego,tag=1]

tp @n[type=mannequin,tag=D4C_alter_ego,tag=2] @n[type=wolf,tag=D4C_alter_ego,tag=2]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=2] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=2] run damage @s 5 minecraft:player_attack by @n[type=mannequin,tag=D4C_alter_ego,tag=2]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=2] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=2] run swing @n[type=mannequin,tag=D4C_alter_ego,tag=2] mainhand
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=2] run data modify entity @e[type=wolf,tag=D4C_alter_ego,tag=2,limit=1] Owner set value []
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=2] run kill @e[type=wolf,tag=D4C_alter_ego,tag=2]

tp @n[type=mannequin,tag=D4C_alter_ego,tag=3] @n[type=wolf,tag=D4C_alter_ego,tag=3]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=3] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=3] run damage @s 5 minecraft:player_attack by @n[type=mannequin,tag=D4C_alter_ego,tag=3]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=3] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=3] run swing @n[type=mannequin,tag=D4C_alter_ego,tag=3] mainhand
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=3] run data modify entity @e[type=wolf,tag=D4C_alter_ego,tag=3,limit=1] Owner set value []
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=3] run kill @e[type=wolf,tag=D4C_alter_ego,tag=3]

tp @n[type=mannequin,tag=D4C_alter_ego,tag=4] @n[type=wolf,tag=D4C_alter_ego,tag=4]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=4] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=4] run damage @s 5 minecraft:player_attack by @n[type=mannequin,tag=D4C_alter_ego,tag=4]
execute as @n[type=wolf,tag=D4C_alter_ego,tag=4] at @s on attacker if entity @n[distance=..5,tag=D4C_alter_ego,tag=4] run swing @n[type=mannequin,tag=D4C_alter_ego,tag=4] mainhand
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=4] run data modify entity @e[type=wolf,tag=D4C_alter_ego,tag=4,limit=1] Owner set value []
execute unless entity @n[type=mannequin,tag=D4C_alter_ego,tag=4] run kill @e[type=wolf,tag=D4C_alter_ego,tag=4]