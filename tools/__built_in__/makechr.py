x = open('chr.txt', 'w')

for n in range(1000000):
    m = str(chr(n))
    x.write(m)

x.close()
