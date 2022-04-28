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

#pylint: disable=C0111

from mimetypes import init
import random
from datetime import datetime
import time

VERSION = "0.5"


BOARD_SIZE = 10
SHIP_SET = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]


class BoardException(BaseException):
    def __init__(self, *args: object) -> None:  # pylint: disable=super-init-not-called
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
            return "Same hit: " + self.msg
        else:
            return "Same hit"


class BoardShipPlacementException(BoardException):
    def __str__(self) -> str:
        if self.msg:
            return "No room for ship: " + self.msg
        else:
            return "No room for ship"


class BadGamerException(BoardException):
    def __str__(self) -> str:
        if self.msg:
            return "Error gamer initializing: " + self.msg
        else:
            return "Error gamer initializing"


class CellState:
    FREE = " "
    #MISS = "-"
    MISS = "·"
    SHIP = "█"
    WRECK = "░"


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.type = CellState.FREE

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col

    def __str__(self) -> str:
        return f"({Board.V_LABELS[self.row]}, {Board.H_LABELS[self.col]})"

    def __hash__(self) -> int:
        return self.row * 100 + self.col


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

        row = random.randint(0, board_size - ship_size)
        col = random.randint(0, board_size - ship_size)
        orientation = random.randint(0, 1)
        for _ in range(ship_size):
            ship.add_cell(Cell(row, col))
            if orientation:
                row += 1
            else:
                col += 1
        return ship


class Board:
    V_LABELS = list("ABCDEFGHIJ")
    H_LABELS = list("1234567890")

    def __init__(self, size=6):
        self.size = size if size > 10 else 10

        # self.v_labels = self.v_labels[:self.size]
        # self.h_labels = self.h_labels[:self.size]

        self.show_ships = True

        self.field = [[CellState.FREE]*self.size for _ in range(self.size)]

        self.shots = set()
        self.ships = set()

    def __str__(self):
        buffer = "  |  " + " ".join(self.H_LABELS) + "|"
        buffer += "\n--|" + "-"*(self.size*2) + "-|--"
        for i, row in enumerate(self.field):
            buffer += f"\n{self.V_LABELS[i]} | "
            for cell in row:
                if not self.visible and cell == CellState.SHIP:
                    buffer += CellState.FREE*2
                else:
                    buffer += cell*2
            buffer += f"| {self.V_LABELS[i]}"
        buffer += "\n--|" + "-"*(self.size*2) + "-|--"
        buffer += "\n  |  " + " ".join(self.H_LABELS) + "|"

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
            0 <= cell.row < self.size,
            0 <= cell.col < self.size
        ]):
            return self.field[cell.row][cell.col]
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
            0 <= cell.row < self.size,
            0 <= cell.col < self.size
        ]):
            self.field[cell.row][cell.col] = value
        else:
            raise BoardOutException(str(cell))

    AREA_FULL = [-1, 0, 1]
    AREA_DIAG = [-1, 1]

    def get_nbhd(self, cell: Cell, area: list = AREA_FULL) -> set:  # pylint: disable=dangerous-default-value
        """Get neighborhood cells

        Args:
            cell (Cell): Cell
            area (list): AREA_FULL = around, AREA_DIAG = diag

        Returns:
            list: Neighborhood cell list
        """
        nbhd = set()
        for offset_row in area:
            for offset_col in area:
                if offset_row == 0 and offset_col == 0:
                    continue

                if all([
                    0 <= (cell.row + offset_row) < self.size,
                    0 <= (cell.col + offset_col) < self.size
                ]):
                    nbhd.add(Cell(cell.row + offset_row, cell.col + offset_col))

        # for cell in nbhd:
        #    self.set_cell(cell, "+")
        return nbhd

    def get_nbhd_v(self, cell: Cell) -> set:
        """Get neighborhood cells up/down

        Args:
            cell (Cell): Cell

        Returns:
            list: Neighborhood cell list
        """
        nbhd = set()
        for offset in [-1, 1]:
            if 0 <= (cell.row + offset) < self.size:
                nbhd.add(Cell(cell.row + offset, cell.col))

        return nbhd

    def get_nbhd_h(self, cell: Cell) -> set:
        """Get neighborhood cells left/right

        Args:
            cell (Cell): Cell

        Returns:
            list: Neighborhood cell list
        """
        nbhd = set()
        for offset in [-1, 1]:
            if 0 <= (cell.col + offset) < self.size:
                nbhd.add(Cell(cell.row, cell.col + offset))

        return nbhd

    def add_ship(self, ship: Ship):
        """Add ship to board

        Args:
            ship (Ship): Ship

        Raises:
            BoardBadShipException: Raise if ship doesn't fit
        """
        for cell in ship.cells:
            if self.get_cell(cell) != CellState.FREE:
                raise BoardShipPlacementException
            for nbhd_cell in self.get_nbhd(cell):
                if self.get_cell(nbhd_cell) == CellState.SHIP:
                    raise BoardShipPlacementException

        self.ships.add(ship)

        for cell in ship.cells:
            self.set_cell(cell, CellState.SHIP)

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

    @property
    def visible(self) -> bool:
        return self.show_ships

    @visible.setter
    def visible(self, visible: bool):
        self.show_ships = visible


class Player:
    name = "Player" + str(random.randint(1, 100))
    board_size = 0

    def __init__(self, board_size: int, name: str = None) -> None:
        if name:
            self.name = name

        if 0 < board_size <= 10:
            self.board_size = board_size
        else:
            raise BadGamerException

    def __str__(self) -> str:
        return self.name

    def get_move(self) -> Cell:
        raise NotImplementedError

    def proceed_answer(self, answer: ShipState):
        raise NotImplementedError


class Human(Player):
    def __init__(self, board_size: int, name: str = None) -> None:
        if name:
            super().__init__(board_size, "Human" + str(random.randint(1, 100)))
        else:
            super().__init__(board_size, name)

    def get_move(self) -> Cell:
        cmd = input("Move: ")
        if not cmd:
            return None

        row, col = list(cmd.upper())[:2]
        return Cell(Board.V_LABELS.index(row), Board.H_LABELS.index(col))


    def proceed_answer(self, answer: ShipState):
        pass


class Robot(Player):
    hits = []
    old_shots = []
    board = None

    def __init__(self, board_size: int, name: str = None) -> None:
        if name:
            super().__init__(board_size, "Robot" + str(random.randint(1, 100)))
        else:
            super().__init__(board_size, name)

        self.board = Board(board_size)

    def _chase(self) -> Cell:
        print("hits: ", [str(cell) for cell in self.hits])
        nbhd = set()

        # search around cells if hits is only 1 cell
        if len(self.hits) == 1:
            nbhd = self.board.get_nbhd_v(self.hits[0]).union(
                self.board.get_nbhd_h(self.hits[0]))

        # else if hits more then 1 calc direction and seach
        else:
            # True if vertical, False if horizontal
            is_vertical = self.hits[0].row - self.hits[1].row
            for cell in self.hits:
                nbhd = nbhd.union(self.board.get_nbhd_v(cell) if is_vertical
                                  else self.board.get_nbhd_h(cell))

        # if area of area hits cells contain wreck remove this cell
        for cell in nbhd.copy():
            for cell_ in self.board.get_nbhd(cell):
                if (self.board.get_cell(cell_) == CellState.WRECK) and (cell_ not in self.hits):
                    nbhd.remove(cell)
                    break

        # return first free cell
        for cell in nbhd:
            if self.board.get_cell(cell) != CellState.MISS and cell not in self.hits:
                return cell

    def _random_hit(self) -> Cell:
        # random shot with some checks (do not be repeted and hit near wrecks)
        while True:
            row = random.randint(0, self.board_size - 1)
            col = random.randint(0, self.board_size - 1)
            target = Cell(row, col)

            if target in self.old_shots:
                continue

            # check neighborhood cells for wrecks
            for cell in self.board.get_nbhd(target):
                if self.board.get_cell(cell) == CellState.WRECK:
                    target = None
                    break

            # break in acceptable shot
            if target:
                break

        return target

    def get_move(self) -> Cell:
        # if has wounded ship
        if self.hits:
            target = self._chase()

        else:
            target = self._random_hit()

        self.old_shots.append(target)
        return target

    def proceed_answer(self, answer: ShipState):
        if answer == ShipState.HIT:
            self.hits.append(self.old_shots[-1])
            self.board.set_cell(self.old_shots[-1], CellState.WRECK)
        elif answer == ShipState.SINK:
            self.hits.clear()
            self.board.set_cell(self.old_shots[-1], CellState.WRECK)
        else:
            self.board.set_cell(self.old_shots[-1], CellState.MISS)


class Game:
    # platers - list of {"player": player, "board": board)
    players = []
    board_size = 0

    def __init__(self, board_size: int) -> None:
        if 0 < board_size <= 10:
            self.board_size = board_size
        else:
            raise BadGamerException

    def populate_board(self, board: Board, ship_set: list) -> None:
        # 100 attempt
        for _ in range(100):
            for ship_size in ship_set:
                # 1000 attempts to place ship
                # otherwise reset board and start from beggining
                for _ in range(1000):
                    ship = ShipFactory.build_ship(ship_size, board.size)
                    try:
                        board.add_ship(ship)
                        break
                    except BoardShipPlacementException:
                        ship = None

                # after all tries
                if ship is None:
                    board.clear()
                    print("Resetting board")
                    break

            if len(board.ships) == len(SHIP_SET):
                break

    def setup(self):
        player = {"player": Robot(self.board_size), "board": Board(self.board_size)}
        player["board"].visible = False
        self.populate_board(player["board"], SHIP_SET)
        self.players.append(player)

        print(player["player"])
        print(player["board"])

    def start(self):
        pass


def main():

    random.seed(datetime.now().timestamp())

    game = Game(BOARD_SIZE)
    game.setup()

    board = Board(BOARD_SIZE)
    board.visible = False
    while True:
        for ship_size in SHIP_SET:
            for _ in range(1000):
                ship = ShipFactory.build_ship(ship_size, board.size)
                try:
                    board.add_ship(ship)
                    break
                except BoardShipPlacementException:
                    ship = None

            # after all tries
            if ship is None:
                board.clear()
                print("Resetting board")
                break

        if len(board.ships) == len(SHIP_SET):
            break

    turn = 1
    hits = []

    print(board)
    print("\nMove #", turn)

    # while cmd := input("Move: "):
    while True:
        #row, col = list(cmd.upper())[:2]
        # time.sleep(1)
        if hits:
            print("hits: ", [str(cell) for cell in hits])

            nbhd = set()

            # if target only is 1 cell than search around cells
            if len(hits) == 1:
                nbhd = board.get_nbhd_v(hits[0]).union(
                    board.get_nbhd_h(hits[0]))

            # else if target contains more then 1 cell
            else:
                # True if vertical, False if horizontal
                is_vertical = hits[0].row - hits[1].row
                for cell in hits:
                    nbhd = nbhd.union(board.get_nbhd_v(cell) if is_vertical
                                      else board.get_nbhd_h(cell))

            # if area of area hits cells contain wreck remove this cell
            for cell in nbhd.copy():
                for cell_ in board.get_nbhd(cell):
                    if (board.get_cell(cell_) == CellState.WRECK) and (cell_ not in hits):
                        nbhd.remove(cell)
                        break

            for cell in nbhd:
                if board.get_cell(cell) != CellState.MISS and cell not in hits:
                    target = cell
                    break
        else:
            while True:
                row = random.randint(0, board.size - 1)
                col = random.randint(0, board.size - 1)
                target = Cell(row, col)
                for cell in board.get_nbhd(target):
                    if board.get_cell(cell) == CellState.WRECK:
                        target = None
                        break
                if target:
                    break
        try:
            # ret = board.shot(Cell(v_label.index(row), h_label.index(col))
            #ret = board.shot(Cell(ord(row) - ord("A"), int(col) - 1))
            ret = board.shot(target)
        except BoardOutException:
            print("Too far")
        except BoardUsedException:
            #print("Used cell as target")
            # time.sleep(1)
            pass
        else:
            print("Move is :", str(target))

            if ret == ShipState.HIT:
                print("Hit!")
                hits.append(target)
            elif ret == ShipState.SINK:
                print("Sink!!!!")
                hits.clear()
            else:
                print("Miss")

            if not board.ships:
                print(board)
                print("You're won!")
                break
            else:
                turn += 1
                print("\n\nMove #", turn)
                print(board)
                print()

            time.sleep(0.5)


if __name__ == '__main__':
    main()
