from d20 import roll

while True:
    roll_result = roll(input(), allow_comments=True)
    print(str(roll_result))
