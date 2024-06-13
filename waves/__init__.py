#! python3
import os

path = os.path.dirname(__file__)

Waves = {}

for file in os.listdir(path):
    if file.endswith('.txt'):
        name, ext = os.path.splitext(file)

        text = open(f'{path}/{file}', 'r').read().replace(',', ' ')

        Waves[name] = [int(x, 16) for x in text.split()]




if __name__ == '__main__':
    from pylab import *

    if False:    # 正弦波
        x = arange(300) / 300 * np.pi * 2
        y = sin(x)

        y = y * 2047 + 2048
        y = y.astype(int)

    if False:    # 方波
        x = range(100)
        y = [0] * 50 + [4095] * 50

    if True:    # 三角波
        x = range(100)
        y = arange(50) / 50 * 4095
        y = list(y.astype(int))
        y = y + y[::-1]

    for i, z in enumerate(y):
        if i % 20 == 0:
            print()

        print(f'{z:03X}, ', end='')
    print()

    plot(x, y)
    show()
