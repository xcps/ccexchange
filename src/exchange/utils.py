
def my_round(x):
    round_level = 6
    if x < 1:
        floats = reversed(str(x).split('.')[1][:round_level])
        index = 0
        for c, f in enumerate(floats):
            if f != "0":
                round_level = round_level - c
                break
    x1 = round(x, round_level)
    return x1
