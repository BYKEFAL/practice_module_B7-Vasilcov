from random import randint, choice
from time import sleep


class BoardException(Exception):
    pass


class BoardWrongShipException(BoardException):
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return 'Нельзя стрелять за пределы доски! Попробуйте еще раз!'


class BoardShootException(BoardException):
    def __str__(self):
        return 'В эту клетку вы уже стреляли! Попробуйте еще раз!'


class Dot:
    def __init__(self, y, x):
        self.y = y
        self.x = x

    def __eq__(self, other):
        return self.y == other.y and self.x == other.x

    def __repr__(self):
        return f'Dot({self.y}, {self.x})'


class Ship:
    def __init__(self, length: int, stern_ship: Dot, ship_direction: bool):
        self.length = length
        self.stern_ship = stern_ship
        self.ship_direction = ship_direction
        self.lives = length

    @property
    def dots(self):  # метод возвращающий список всех точек корабля
        all_dots = []
        for i in range(self.length):
            cur_y = self.stern_ship.y
            cur_x = self.stern_ship.x
            if self.ship_direction:  # если корабль расположен вертикально, то True, горизонтально False
                cur_y += i
            else:
                cur_x += i
            all_dots.append(Dot(cur_y, cur_x))
        return all_dots

    def is_hit(self, value) -> bool:
        return value in self.dots


class Board:
    def __init__(self, size, hid=False):
        self.size = size
        self.field = [['O'] * self.size for i in range(self.size)]
        self.hid = hid
        self.busy_list = []
        self.ship_list = []
        self.ship_count = 0
        self.last_hit = []

    def __str__(self):
        board = '   ' + ' ' + '   '.join([str(i) for i in range(1, self.size + 1)]) + '  '
        for i, j in enumerate(self.field, start=1):
            board += f'\n{i} | ' + ' | '.join(j) + ' |'
        if self.hid:
            board = board.replace('■', 'O')
        return board

    def out(self, any_dot: Dot) -> bool:
        return not (0 <= any_dot.x < self.size and 0 <= any_dot.y < self.size)

    def add_ship(self, ship: Ship):
        for i in ship.dots:
            if i in self.busy_list or self.out(i):
                raise BoardWrongShipException()
        for i in ship.dots:
            self.field[i.y][i.x] = '■'
            self.busy_list.append(i)
        self.ship_list.append(ship)
        self.ship_count += 1
        self.contour(ship)

    def contour(self, ship: Ship, visible=False):
        around = [(i, j) for i in range(-1, 2) for j in range(-1, 2)]
        for dot in ship.dots:
            for dy, dx in around:
                curr_dot = Dot(dot.y + dy, dot.x + dx)
                if not self.out(curr_dot) and curr_dot not in self.busy_list:
                    if visible:  # видимость контура
                        self.field[curr_dot.y][curr_dot.x] = '.'
                    self.busy_list.append(curr_dot)

    def shot(self, any_dot: Dot) -> bool:  # возвращает True, если надо переходить либо вражеский корабль потоплен
        if any_dot in self.busy_list:
            raise BoardShootException()
        if self.out(any_dot):
            raise BoardOutException()
        self.busy_list.append(any_dot)

        for ship in self.ship_list:
            if ship.is_hit(any_dot):
                self.field[any_dot.y][any_dot.x] = 'X'
                print('Попадание!')
                ship.lives -= 1
                if ship.lives == 0:
                    self.contour(ship, visible=True)
                    print('Корабль уничтожен!\n')
                    self.ship_count -= 1
                    self.last_hit = []
                    return True
                else:
                    print('Корабль ранен!\n')
                    self.last_hit.append(any_dot)
                    return True

        self.field[any_dot.y][any_dot.x] = '.'
        print('Мимо!\n')
        return False

    def begin(self):
        self.busy_list = []


class Player:
    def __init__(self, own_board: Board, enemy_board: Board):
        self.own_board = own_board
        self.enemy_board = enemy_board
        # клетки вне поля, для компа, чтобы нормально добить корабли которые расположены по краю
        self.dots_player = [Dot(-1, i) for i in range(-1, 7)] + [Dot(6, i) for i in range(-1, 7)] + \
                           [Dot(i, -1) for i in range(-1, 7)] + [Dot(i, 6) for i in range(-1, 7)]

    def ask(self):
        raise NotImplementedError()

    def move(self) -> bool:
        while True:
            try:
                target = self.ask()
                repeat = self.enemy_board.shot(target)
                sleep(1)
                return repeat
            except BoardException as e:
                print(e)


class User(Player):
    def ask(self) -> Dot:
        while True:
            coords = list(input('Введите координаты выстрела: '))
            if len(coords) != 2:
                print('Введите координаты в формате 11, 26, 35 и т.д.')
                continue
            y, x = coords
            if not all((y.isdigit(), x.isdigit())):
                print('Координаты должны быть числами')
                continue
            return Dot(int(y) - 1, int(x) - 1)


class AI(Player):  # сделать умное добивание корабля

    def ask(self) -> Dot:
        while True:  # Добивание кораблей многопалубных кораблей
            any_dot = Dot(randint(0, 5), randint(0, 5))
            last_hit = self.enemy_board.last_hit

            if last_hit:
                if len(last_hit) == 1:
                    near_hit = choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                    any_dot = Dot(last_hit[-1].y + near_hit[0], last_hit[-1].x + near_hit[1])
                elif len(last_hit) >= 2:
                    if last_hit[-2].x == last_hit[-1].x:
                        near_hit = choice([(1, 0), (-1, 0)])
                        any_dot = Dot(last_hit[-1].y + near_hit[0], last_hit[-1].x + near_hit[1])
                    elif last_hit[-2].y == last_hit[-1].y:
                        near_hit = choice([(0, 1), (0, -1)])
                        any_dot = Dot(last_hit[-1].y + near_hit[0], last_hit[-1].x + near_hit[1])
                    for ship in self.enemy_board.ship_list:
                        if last_hit:
                            if (ship.dots[-1] == last_hit[1]) or (ship.dots[0] == last_hit[1]):
                                last_hit.insert(len(last_hit), last_hit[0])

            if any_dot in self.dots_player:
                continue
            if any_dot in self.enemy_board.busy_list:
                continue

            sleep(0.5 * randint(2, 4))
            print(f"Ход компьютера: {any_dot.y + 1}{any_dot.x + 1}")
            break
        self.dots_player.append(any_dot)
        return any_dot


class Game:
    def __init__(self, size=6):
        self.size = size
        self.lens = (3, 2, 2, 1, 1, 1, 1)
        ai_board = self.random_board()
        user_board = self.random_board()
        ai_board.hid = True

        self.ai = AI(ai_board, user_board)
        self.us = User(user_board, ai_board)

    def random_board(self):
        board = None
        while board is None:
            board = self.try_gen_board()
        return board

    def try_gen_board(self):
        attempts = 0
        board = Board(size=self.size)
        for i in self.lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(i, Dot(randint(0, self.size), (randint(0, self.size))), bool(randint(0, 1)))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    @staticmethod
    def greet():
        print('\n'
              '\tВас приветствует игра "морской бой" - "sea battle"!!!\n'
              '-----------------------------------------------------------------\n'
              '\tКорабли выставлены автоматически, в случайном порядке\n'
              '       \t(как для игрока, так и для компьютера)\n'
              '-----------------------------------------------------------------\n'
              '\tИнструкция:\n'
              '       1. Чтобы поменять расположение кораблей, начните заново.\n'
              '       2. Для начала игры, введите в окно ввода координаты,\n'
              '          в формате "yx", где "y" - это cтрока, "x" - это столбец\n'
              '          (Пример: 11, 23, 45 и т.д.), без ПРОБЕЛА!!!\n'
              '       3. Кто потопит корабли противника первый, тот выиграл!\n'
              '\tОбозначения:\n'
              '       "O" - клетка поля, "■" - отсек корабля, "X" - отсек подбит,\n'
              '       "." - выстрел мимо, либо контур вокруг потопленного корабля\n'
              '-------------------------------------------------------------------\n'
              '                    7 ФУТОВ ПОД КИЛЕМ!!!\n')

    def print_board(self):
        print('Ваша доска:' + ' \t ' * self.size + 'Доска компьютера:\n')
        s = self.us.own_board.__str__().split('\n')
        c = self.ai.own_board.__str__().split('\n')
        for i, j in zip(s, c):
            print(i + " " * 10 + j)
        print()

    def loop(self):
        step = None
        self.print_board()
        while True:
            q = input('Выберите кто ходит первый, "1" - компьютер, "2" - игрок: ')
            print()
            if q == '1':
                step = 1
                break
            elif q == '2':
                step = 0
                break
            else:
                continue

        while True:
            self.print_board()
            if step % 2 == 0:
                print('Ваш ход!')
                repeat = self.us.move()
            else:
                print('Ходит компьютер!')
                repeat = self.ai.move()
            if repeat:
                step -= 1

            if self.ai.own_board.ship_count == 0:
                self.print_board()
                print('Поздравляю Вы выиграли!')
                break
            if self.us.own_board.ship_count == 0:
                self.print_board()
                print('Все плохо, вы проиграли!!!')
                break
            step += 1

    def start(self):
        self.greet()
        self.loop()


g = Game()
g.start()
