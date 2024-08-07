import pygame as pg
from random import randint as rand

ray, collis, swt = [], [], []
partic = []
LevelEnd = []
cam = (0, 0)
next_file = ['1.txt']


class Particle:
    def __init__(self, x, y, dx, dy, t, r=2):
        self.x, self.y, self.dx, self.dy, self.t, self.r = x, y, dx, dy, t, r
        self.c = (255,) * 3

    def upd(self, time):
        self.t -= time
        self.x += self.dx * time
        self.y += self.dy * time

    def draw(self, win):
        global cam
        pg.draw.circle(win, self.c, (int(self.x + cam[0]), int(self.y + cam[1])), self.r)


class Line:
    def __init__(self, x1, y1, x2, y2, autovis=True, mirror=False, stic=False, glass=False, kill=False):
        self.cltp = "Line"
        self.stic = stic
        self.kill = kill
        self.glass = glass
        if x1 == x2:
            x1 += 0.001
        if y1 == y2:
            y1 += 0.001
        self.visible = autovis
        self.autovis = autovis
        self.mirror = mirror
        self.x = [x1, x2]
        self.y = [y1, y2]
        self.a = y1 - y2
        self.b = x2 - x1
        self.color = (255,) * 3
        if stic:
            self.color = (0, 150, 0)
        if kill:
            self.color = (255, 0, 0)
        self.c = -x1 * self.a - self.b * y1

    def upper(self, x, y):
        return 0 <= x * self.a + y * self.b + self.c

    def getvec(self):
        r = (self.a * self.a + self.b * self.b) ** 0.5
        return self.b / r, -self.a / r

    def xot(self, other):
        if other.cltp == 'Cir':
            return other.xot(self)
        q = (self.a * other.b - other.a * self.b)
        if q == 0:
            q = 0.1
        y = (self.c * other.a - other.c * self.a) / q
        q = self.a
        if q == 0:
            q = 0.1
        x = (-self.b * y - self.c) / q
        X = [min(self.x), max(self.x), min(other.x), max(other.x)]
        if not(X[0] <= x <= X[1]) or not(X[2] <= x <= X[3]):
            return False, 0, 0
        Y = [min(self.y), max(self.y), min(other.y), max(other.y)]
        if not (Y[0] <= y <= Y[1]) or not (Y[2] <= y <= Y[3]):
            return False, 0, 0

        return True, int(x), int(y)

    def draw(self, win):
        global cam
        pg.draw.line(win, self.color, (int(self.x[0] + cam[0]), int(self.y[0] + cam[1])), (int(self.x[1] + cam[0]), int(self.y[1] + cam[1])))


class Circle:
    def __init__(self, x, y, r,autovis=True, mirror=False):
        self.x, self.y, self.r = x, y, r
        self.cltp = "Cir"
        self.autovis = autovis
        self.visible = autovis
        self.mirror = mirror
        self.c = (255, ) * 3
        if mirror:
            self.c = (150,) * 3

    def draw(self, win):
        global cam
        pg.draw.circle(win, self.c, (int(self.x + cam[0]), int(self.y + cam[1])), self.r, 1)

    def xot(self, other):
        global ray
        if other.cltp == 'Line':
            xx, yy = self.getvec(other.x[1], other.y[1])
            if xx * (other.x[1] - other.x[0]) + yy * (other.y[1] - other.y[0]) < 0:
                return ((self.x - other.x[1]) ** 2 + (self.y - other.y[1]) ** 2) ** 0.5 <= self.r, 1, 1

            xx, yy = self.getvec(other.x[0], other.y[0])
            if xx * (other.x[0] - other.x[1]) + yy * (other.y[0] - other.y[1]) < 0:
                return ((self.x - other.x[0]) ** 2 + (self.y - other.y[0]) ** 2) ** 0.5 <= self.r, 1, 1
            xx1, yy1 = other.getvec()
            xx1, yy1 = -yy1, xx1
            r = xx * xx1 + yy * yy1
            rr = ((self.x - other.x[0]) ** 2 + (self.y - other.y[0]) ** 2) ** 0.5
            if self.r >= abs(r * rr):
                return True, 0, 0
            else:
                return False, 0, 0

    def getvec(self, x, y):
        x -= self.x
        y -= self.y
        r = (x ** 2 + y ** 2) ** 0.5
        if r > 0:
            x /= r
            y /= r
        return x, y


class Switch(Circle):
    def __init__(self, x, y, r):
        super().__init__(x, y, r)
        self.was = False

    def action(self, pl):
        pass

    def notaction(self):
        pass


class Gravityswitch(Switch):
    def __init__(self, x, y, r, power, R=1000):
        super().__init__(x, y, r)
        self.power = power
        self.R = R

    def action(self, pl):
        x, y = pl.x - self.x, pl.y - self.y
        r = (x ** 2 + y ** 2) ** 0.5
        if self.R > r > 0:
            pl.dx += x * self.power / (r) * pl.time_for_other
            pl.dy += y * self.power / (r) * pl.time_for_other


class Dyswitch(Switch):
    def action(self, pl):
        pl.dy = 0


class Visibleswitch(Switch):
    def action(self, pl):
        global collis
        if self.was:
            return
        for i in collis:
            i.autovis = not i.autovis
        self.was = True

    def notaction(self):
        self.was = False


class Changegravityswitch(Switch):
    def action(self, pl):
        if self.was:
            return
        global partic
        pl.grav *= -1
        self.was = True
        for i in range(100):
            speed = rand(1, 30) / 100.0
            if pl.grav < 0:
                partic += [Particle(rand(int(pl.x - pl.w), int(pl.x + pl.w * 2)), pl.y + pl.h + rand(-5, 5),
                                0, -speed, min(100 / speed + rand(-50, 50), 500 + rand(0, 500)))]
            else:
                partic += [Particle(rand(int(pl.x - pl.w), int(pl.x + pl.w * 2)), pl.y + rand(-5, 5),
                                    0, speed, min(100 / speed + rand(-50, 50), 500 + rand(0, 500)))]

    def notaction(self):
        self.was = False


class Rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.cltp = "Rect"

    def xot(self, other):
        if other.cltp == "Rect":
            if self.x <= other.x + other.w and other.x <= self.x + self.w:
                if self.y <= other.y + other.h and other.y <= self.y + self.h:
                    return True
        if other.cltp == "Line":
            if self.x > max(other.x) or self.x + self.w < min(other.x):
                return False
            if self.y > max(other.y) or self.y + self.h < min(other.y):
                return False
            a, b, = False, False
            for i in range(2):
                for j in range(2):
                    if other.upper(self.x + self.w * i, self.y + self.h * j):
                        a = True
                    else:
                        b = True
            return a and b
        return False

    def center(self):
        return self.x + self.w / 2, self.y + self.h / 2

    def point_in(self, x, y):
        return (0 < x - self.x < self.w) and (0 < y - self.y < self.h)


class Player(Rect):
    def __init__(self, x, y, w, h):
        self.dx, self.dy = 0, 0
        self.frx, self.fry, self.frp = 0, 0, 0.4
        self.speed = 0.0005
        self.grav = 0.5
        self.jump = 250
        self.onground = False
        self.mxspeed = 800
        self.time_for_other = 0
        super().__init__(x, y, w, h)

    def upd(self, time):
        global ray, collis, cam, nowgame
        self.time_for_other = time
        k = pg.key.get_pressed()
        self.x += self.dx * time * self.speed
        self.y += self.dy * time * self.speed
        ddd = self.dx, self.dy
        self.onground = False
        for i in collis:
            if not i.visible:
                continue
            if self.xot(i):
                if i.kill:
                    nowgame = LooseGame()
                # Праллель
                for point in range(2):
                    if self.point_in(i.x[point], i.y[point]):
                        self.y = i.y[point] - (self.h if self.grav > 0 else 0)
                        break
                yy, xx = i.getvec()
                if i.upper(*self.center()):
                    xx *= -1
                else:
                    yy *= -1
                self.frx -= xx
                self.fry -= yy
                if abs(yy / xx) > 0.5 or i.stic:
                    self.onground = True

                cs = xx * self.dx + yy * self.dy
                if cs < 0:
                    self.dx -= xx * cs
                    self.dy -= yy * cs
        self.x += (self.dx - ddd[0]) * time * self.speed
        self.y += (self.dy - ddd[1]) * time * self.speed

        self.dy += self.grav * time
        koof = (self.frx ** 2 + self.fry ** 2) ** 0.5
        if koof > 0:
            self.frx /= koof
            self.fry /= koof
            self.frx = int(self.frx * 1000) / 1000.0
            self.fry = int(self.fry * 1000) / 1000.0
        if k[pg.K_SPACE] and self.onground:
            self.dx -= self.jump * self.frx
            self.dy -= self.jump * (self.fry + self.grav / abs(self.grav))
            self.onground = False
        if abs(self.dx) < self.mxspeed:
            self.dx += (int(k[pg.K_d]) - int(k[pg.K_a])) * time

        # Трение
        if koof > 0:
            self.frx, self.fry = abs(self.fry), abs(self.frx)
            if self.dx > 0:
                self.dx = max(0, self.dx - self.frx * self.frp * time)
            else:
                self.dx = min(0, self.dx + self.frx * self.frp * time)

            if self.dy > 0:
                self.dy = max(0, self.dy - self.fry * self.frp * time)
            else:
                self.dy = min(0, self.dy + self.fry * self.frp * time)
            self.frx, self.fry = 0, 0

        if pg.mouse.get_pressed()[0]:
            fff = True
            for i in collis:
                if not i.autovis:
                    if i.visible or i.glass:
                        continue
                    if self.xot(i):
                        fff = False
                        break
            if fff:
                sx, sy = pg.mouse.get_pos()
                sx -= cam[0]
                sy -= cam[1]
                l = Line(*self.center(), sx, sy)
                sx, sy = l.getvec()
                r = 1e5
                ray += [Line(l.x[0], l.y[0], sx * r, sy * r)]
        cam = self.center()
        wd, ht = win.get_size()
        cam = (-cam[0] + wd / 2, -cam[1] + ht / 2)

    def draw(self, win):
        global cam
        pg.draw.rect(win, (150, 150, 150), (self.x + cam[0], self.y + cam[1], self.w, self.h))


class Game:
    def __init__(self):
        pass

    def upd(self, time):
        pass

    def draw(self, win):
        pass


class MainGame(Game):
    def __init__(self):
        W, H = 20, 50
        self.p = Player(-W/2, -H/2, W, H)

    def upd(self, time):
        global ray, collis, LevelEnd, nowgame, partic
        ray = []
        self.p.upd(time)
        for i in range(len(LevelEnd)):
            if self.p.xot(LevelEnd[i]):
                nowgame = WinGame(i)
                return
        for i in collis:
            i.visible = i.autovis
        for i in ray:
            ch = -1
            chi = 0
            for j in collis:
                if j.glass:
                    continue
                fxy = False, 0, 0
                a, b, c = i.xot(j)
                if a:
                    i.x[1], i.y[1] = b, c
                    if j.mirror:
                        fxy = (True,) + j.getvec()
                    if not j.autovis:
                        ch = chi
                if fxy[0]:
                    xx, yy = fxy[2], -fxy[1]
                    xx1, yy1 = i.getvec()
                    xx1, yy1 = -xx1, -yy1
                    r = xx * xx1 + yy * yy1
                    if r < 0:
                        xx *= -1
                        yy *= -1
                        r *= -1
                    if r != 0:
                        xx = xx * 2 - xx1 / r
                        yy = yy * 2 - yy1 / r
                    r = (xx ** 2 + yy ** 2) ** 0.5
                    if r != 0:
                        xx /= r
                        yy /= r
                    r = 1e5
                    ray += [Line(i.x[1] + xx1 * 1.5, i.y[1] + yy1 * 1.5, i.x[1] + xx * r, i.y[1] + yy * r)]
                    continue
                chi += 1
            if ch >= 0:
                collis[ch].visible = True
        for j in swt:
            fff = True
            for i in ray:
                if j.xot(i)[0]:
                    j.action(self.p)
                    fff = False
            if fff:
                j.notaction()
        for i in range(len(partic)-1, -1, -1):
            partic[i].upd(time)
            if partic[i].t < 0:
                partic.pop(i)

    def draw(self, win):
        global ray, collis, cam, LevelEnd, swt, partic
        for i in ray:
            i.color = (155, 255, 255)
            i.draw(win)

        for i in swt:
            i.draw(win)

        for i in collis:
            if i.mirror:
                i.color = (155,) * 3

        for i in collis:
            if i.cltp == "Line" and i.visible:
                i.draw(win)
        for i in LevelEnd:
            pg.draw.rect(win, (255, 255, 0), (i.x + cam[0], i.y + cam[1], i.w, i.h))
        self.p.draw(win)
        for i in partic:
            i.draw(win)


class WinGame(Game):
    def __init__(self, gate=0):
        super().__init__()
        self.gate = gate

    def draw(self, win):
        global next_file
        if next_file[self.gate] == 'WIN':
            txt = pg.font.Font('arial.ttf', 200).render('You win', True, (255, ) * 3)
            ss = txt.get_size()
            wd, ht = win.get_size()
            win.blit(txt, (wd / 2 - ss[0] // 2, ht / 2 - ss[1] // 2))


class LooseGame(Game):
    def draw(self, win):
        txt = pg.font.Font('arial.ttf', 170).render('You loose', True, (255, ) * 3)
        ss = txt.get_size()
        wd, ht = win.get_size()
        win.blit(txt, (wd / 2 - ss[0] // 2, ht / 2 - ss[1] // 2))


def load_from_file(i=0):
    global next_file
    global collis, swt, LevelEnd
    if next_file[i] == 'WIN':
        return
    f = eval(open(next_file[i]).read())
    collis, swt = f[0], f[1]
    LevelEnd = []
    next_file = []
    for j in f[2]:
        LevelEnd += [Rect(j[0], j[1], j[2], j[3])]
        next_file += [j[4]]


pg.init()
load_from_file()
win = pg.display.set_mode((800, 600))
run = True
clock = pg.time.Clock()

nowgame = MainGame()

while run:
    if type(nowgame) is WinGame:
        if next_file[nowgame.gate] != 'WIN':
            load_from_file(nowgame.gate)
            nowgame = MainGame()
            continue
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False
        if event.type == pg.KEYDOWN:
            if type(nowgame) is LooseGame:
                nowgame = MainGame()
                continue
            if event.key == pg.K_ESCAPE:
                run = False
                break
            if pg.K_1 <= event.key <= pg.K_7:
                next_file = [f'{event.key - pg.K_0}.txt']
                load_from_file()
                nowgame = MainGame()
                continue
    win.fill((0,) * 3)
    time = clock.tick()
    nowgame.upd(time)
    nowgame.draw(win)
    pg.display.flip()


