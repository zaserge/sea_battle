# Copyright (c) 2022 zaserge@gmail.com

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import random
from datetime import datetime


class BoardException(Exception):
    def __init__(self, *args: object) -> None:
        if args:
            self.msg = args[0]
        else:
            self.msg = None


class BoardOutException(BoardException):
    def __str__(self) -> str:
        if self.msg:
            return "Out of board: " + self.msg
        else:
            return "Out of board"


class BoardUsedException(BoardException):
    def __str__(self) -> str:
        if self.msg:
            return "Reused hit: " + self.msg
        else:
            return "Reused hit"


class BoardBadShipException(BoardException):
    def __str__(self) -> str:
        return "Bad ship place"


class CellState:
    FREE = " "
    MISS = "·"
    SHIP = "█"
    WRECK = "░"


class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = CellState.FREE

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __str__(self) -> str:
        return f"({Board.v_labels[self.x]}, {Board.h_labels[self.y]})"

    def __hash__(self) -> int:
        return self.x * 100 + self.y


class ShipState:
    HIT = 1
    MISS = 2
    SINK = 3


class Ship:

    def __init__(self):
        self.cells = set()

    def add_cell(self, cell: Cell):
        """Add cell to ship

        Args:
            cell (Cell): Cell
        """
        self.cells.add(cell)

    def get_hit(self, hit_point: Cell) -> Cell:
        """Get ships hit point or None if miss

        Args:
            hit_point (Cell): Cell

        Returns:
            Cell: Cell or None
        """
        for cell in self.cells:
            if cell == hit_point:
                return cell
        return None

    def hit(self, hit_point: Cell) -> ShipState:
        """Check hitting ship

        Args:
            hit_point (Cell): Cell

        Returns:
            ShipState: Hit state (sink, hit, miss)
        """
        if (cell := self.get_hit(hit_point)):
            self.cells.remove(cell)
            if self.cells:
                return ShipState.HIT
            else:
                return ShipState.SINK
        else:
            return ShipState.MISS

    def __str__(self) -> str:
        return f"SHIP: {len(self.cells)}, " + " ".join([str(item) for item in self.cells])


class ShipFactory:
    @staticmethod
    def build_ship(ship_size: int, board_size: int) -> Ship:
        """Ships factoty. Generate random ship

        Args:
            ship_size (int): ship lenght in cells
            board_size (int): board size in cells

        Returns:
            Ship: Ship object
        """
        ship = Ship()

        x = random.randint(0, board_size - ship_size)
        y = random.randint(0, board_size - ship_size)
        orientation = random.randint(0, 1)
        for _ in range(ship_size):
            ship.add_cell(Cell(x, y))
            if orientation:
                x += 1
            else:
                y += 1
        return ship


class Board:
    v_labels = list("ABCDEFGHIJ")
    h_labels = list("1234567890")

    def __init__(self, size=6):
        self.v_labels = self.v_labels[:size]
        self.h_labels = self.h_labels[:size]

        self.size = size if size <= 6 else 6
        self.show_ships = True

        self.field = [[CellState.FREE]*self.size for _ in range(self.size)]

        self.shots = set()
        self.ships = set()

    def __str__(self):
        buffer = "  |  " + " ".join(self.h_labels) + "|"
        buffer += "\n--|" + "-"*self.size*2 + "-|--"
        for i, row in enumerate(self.field):
            buffer += f"\n{self.v_labels[i]} | "
            for c in row:
                buffer += c + c
            buffer += f"| {self.v_labels[i]}"
        buffer += "\n--|" + "-"*self.size*2 + "-|--"
        buffer += "\n  |  " + " ".join(self.h_labels) + "|"

        return buffer

    def get_cell(self, cell: Cell) -> CellState:
        """Get cell value

        Args:
            cell (Cell): Cell

        Raises:
            BoardOutException: Raise if out of board boundary

        Returns:
            CellState: Cell status (free, ship, wreck, miss)
        """
        if all([
            0 <= cell.x < self.size,
            0 <= cell.y < self.size
        ]):
            return self.field[cell.x][cell.y]
        else:
            raise BoardOutException(str(cell))

    def set_cell(self, cell: Cell, value: CellState):
        """Set cell value

        Args:
            cell (Cell): Cell
            value (CellState): Value

        Raises:
            BoardOutException: Raise if out of board boundary
        """
        if all([
            0 <= cell.x < self.size,
            0 <= cell.y < self.size
        ]):
            self.field[cell.x][cell.y] = value
        else:
            raise BoardOutException(str(cell))

    def get_nbhd(self, cell: Cell) -> list:
        """Get neighborhood cells

        Args:
            cell (Cell): Cell

        Returns:
            list: Neighborhood cell list
        """
        nbhd = []
        for offset_x in [-1, 0, 1]:
            for offset_y in [-1, 0, 1]:
                if offset_x == 0 and offset_y == 0:
                    continue
                else:
                    if all([
                        0 <= (cell.x + offset_x) < self.size,
                        0 <= (cell.y + offset_y) < self.size
                    ]):
                        nbhd.append(Cell(cell.x + offset_x, cell.y + offset_y))

        return nbhd

    def add_ship(self, ship: Ship):
        """Add ship to board

        Args:
            ship (Ship): Ship

        Raises:
            BoardBadShipException: Raise if ship doesn't fit
        """
        for cell in ship.cells:
            if (self.get_cell(cell) != CellState.FREE):
                raise BoardBadShipException
            for nbhd_cell in self.get_nbhd(cell):
                if (self.get_cell(nbhd_cell) != CellState.FREE):
                    raise BoardBadShipException

        if (self.show_ships):
            for cell in ship.cells:
                self.set_cell(cell, CellState.SHIP)

        self.ships.add(ship)

    def shot(self, hit_point: Cell) -> ShipState:
        """Check shot. Check every ship from board to hit.
        Remove cell if hit or remove ship if sink

        Args:
            hit_point (Cell): Cell

        Raises:
            BoardUsedException: Raise if this cell was used

        Returns:
            ShipState: Ship status (hit, sink, miss)
        """
        if hit_point in self.shots:
            raise BoardUsedException(str(hit_point))
        else:
            self.shots.add(hit_point)

        self.get_cell(hit_point)

        for ship in self.ships:
            if (ret := ship.hit(hit_point)) == ShipState.HIT:
                self.set_cell(hit_point, CellState.WRECK)
                return ret
            elif ret == ShipState.SINK:
                self.ships.remove(ship)
                self.set_cell(hit_point, CellState.WRECK)
                return ret

        self.set_cell(hit_point, CellState.MISS)
        return ShipState.MISS

    def clear(self):
        """Clear board
        """
        self.ships.clear()
        self.field = [[CellState.FREE]*self.size for _ in range(self.size)]


BOARD_SIZE = 6
SHIP_SET = [3, 2, 2, 1, 1, 1, 1]
random.seed(datetime.now().timestamp())

board = Board(BOARD_SIZE)
while True:
    for ship_size in SHIP_SET:
        for _ in range(1000):
            ship = ShipFactory.build_ship(ship_size, board.size)
            try:
                board.add_ship(ship)
                break
            except BoardBadShipException as err:
                ship = None
        if ship is None:
            board.clear()
            print("Resetting board")
            break
    if len(board.ships):
        break

turn = 1
print("Move #", turn)
print(board)
#while cmd := input("Move: "):
while True:
    #x, y = list(cmd.upper())[:2]
    x = random.randint(0, 5)
    y = random.randint(0, 5)
    try:
        #ret = board.shot(Cell(ord(x) - ord("A"), int(y) - 1))
        ret = board.shot(Cell(x, y))
    except BoardOutException:
        print("Too far")
    except BoardUsedException:
        #print("Used cell")
        pass
    else:
        if ret == ShipState.HIT:
            print("Hit!")
        elif ret == ShipState.SINK:
            print("Sink!!!!")
        else:
            print("Miss")

        print("Move #", turn)
        if(not board.ships):
            print(board)
            print("You're won!")
            break
        else:
            turn += 1
            print(board)

