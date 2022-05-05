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

import random
from datetime import datetime
import time
import os

VERSION = "0.8b"

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


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

        return "Out of board"


class BoardUsedException(BoardException):

    def __str__(self) -> str:
        if self.msg:
            return "Same shot: " + self.msg

        return "Same shot"


class BoardShipPlacementException(BoardException):

    def __str__(self) -> str:
        if self.msg:
            return "No room for ship: " + self.msg

        return "No room for ship"


class BadBoardException(BoardException):

    def __str__(self) -> str:
        if self.msg:
            return "Error board initializing: " + self.msg

        return "Error board initializing"


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

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col

    def __str__(self) -> str:
        return f"{Board.V_LABELS[self.row]}{Board.H_LABELS[self.col]}"

    def __repr__(self):
        return f"Cell({Board.V_LABELS[self.row]}, {Board.H_LABELS[self.col]})"

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

    def is_hit(self, target: Cell) -> Cell:
        """Search ships hit point

        Return hit cell or None if miss

        Args:
            target (Cell): Cell to check

        Returns:
            Cell: Cell or None
        """
        for cell in self.cells:
            if cell == target:
                return cell
        return None

    def hit(self, target: Cell) -> ShipState:
        """Check hitting ship

        Args:
            target (Cell): Cell to check

        Returns:
            ShipState: Hit state (sink, hit, miss)
        """
        hit_cell = self.is_hit(target)
        if hit_cell:
            self.cells.remove(hit_cell)
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
        """Ships factoty.

        Generate random ship

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


# 1 - slyte as in B7.5 asked
# 2 - improved style (i hope :) )
class BoardViewStyle:

    CLASSIC_VIEW = 1
    MODERN_VIEW = 2


BOARD_STYLE = BoardViewStyle.MODERN_VIEW
class Board:

    V_LABELS = list("ABCDEFGHIJ")
    H_LABELS = list("1234567890")

    def __init__(self, size: int):
        if 0 < size <= 10:
            self.size = size
        else:
            raise BadBoardException

        self.show_ships = True

        self.field = [[CellState.FREE]*self.size for _ in range(self.size)]

        self.shots = set()
        self.ships = set()

    def __str__(self):
        """Draw board
        """
        if BOARD_STYLE == BoardViewStyle.CLASSIC_VIEW:
            buffer = "  | " + " | ".join(self.H_LABELS[:self.size]) + " |"

            for i, row in enumerate(self.field):
                buffer += f"\n{self.V_LABELS[i]} |"
                for cell in row:
                    if cell == CellState.SHIP:
                        buffer += " ■ |" if self.visible else " О |"
                    elif cell == CellState.WRECK:
                        buffer += " X |"
                    elif cell == CellState.MISS:
                        buffer += " T |"
                    elif cell == CellState.FREE:
                        buffer += " О |"

        elif BOARD_STYLE == BoardViewStyle.MODERN_VIEW:
            buffer = "  | " + " ".join(self.H_LABELS[:self.size]) + "|"
            buffer += "\n--|" + "-"*(self.size*2) + "|--"
            for i, row in enumerate(self.field):
                buffer += f"\n{self.V_LABELS[i]} |"
                for cell in row:
                    if not self.visible and cell == CellState.SHIP:
                        buffer += CellState.FREE*2
                    elif cell == CellState.MISS:
                        buffer += "()"
                    else:
                        buffer += cell*2
                buffer += f"| {self.V_LABELS[i]}"
            buffer += "\n--|" + "-"*(self.size*2) + "|--"
            buffer += "\n  | " + " ".join(self.H_LABELS[:self.size]) + "|"

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
        """Processing shot.

        Check every ship on the board for a hit.
        Remove cell if hit or remove ship if sunk

        Args:
            hit_point (Cell): Cell

        Raises:
            BoardUsedException: Raise if this cell was used

        Returns:
            ShipState: Ship status (hit, sink, miss)
        """
        if hit_point in self.shots:
            raise BoardUsedException(str(hit_point))

        self.shots.add(hit_point)

        # out of boundary check
        self.get_cell(hit_point)

        for ship in self.ships:
            hit_result = ship.hit(hit_point)
            if hit_result == ShipState.HIT:
                self.set_cell(hit_point, CellState.WRECK)
                return hit_result

            if hit_result == ShipState.SINK:
                self.ships.remove(ship)
                self.set_cell(hit_point, CellState.WRECK)
                return hit_result

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

    def __init__(self, board_size: int, name: str = None) -> None:
        if name:
            self.name = name
        else:
            self.name = type(self).__name__ + "-" + \
                str(random.randint(1, 1000))

        self.board_size = board_size
        self.board = Board(board_size)
        self.move_list = []

    def __str__(self) -> str:
        return self.name

    def _brain(self) -> Cell:
        """Main AI worker.

        Must be implemented for human or robot

        Raises:
            NotImplementedError: Raise when not implemented

        Returns:
            Cell: player's move
        """
        raise NotImplementedError

    def ask_move(self) -> Cell:
        """Asking for move.

        Return player's move and store it in move_list

        Returns:
            Cell: player's move
        """
        cell = self._brain()
        self.move_list.append(cell)
        return cell

    def processing_answer(self, answer: ShipState):
        """Processing last move result.

        Set marks at own board

        Args:
            answer (ShipState): Hit, sink or miss
        """
        if answer in (ShipState.HIT, ShipState.SINK):
            self.board.set_cell(self.move_list[-1], CellState.WRECK)
        else:
            self.board.set_cell(self.move_list[-1], CellState.MISS)


class Human(Player):

    def _brain(self) -> Cell:
        """Read user input.

        Check it and convert to Cell object

        Raises:
            BoardOutException: Out of bounds exception

        Returns:
            Cell: player's move
        """
        cmd = input()
        if not cmd:
            return None

        try:
            row, col = list(cmd.upper())[:2]
        except ValueError as error:
            raise BoardOutException from error

        while not row.isalpha() or not col.isdigit():
            cmd = input(" Move must be LETTER+DIGIT (A1, B2, c3). Try again: ")
            row, col = list(cmd.upper())[:2]

        try:
            return Cell(Board.V_LABELS.index(row), Board.H_LABELS.index(col))
        except ValueError as error:
            raise BoardOutException from error


class Robot(Player):

    def __init__(self, board_size: int, name: str = None) -> None:
        super().__init__(board_size, name)
        self.enemy_board = Board(board_size)
        self.hits = []

    def _chase(self) -> Cell:
        """Chase AI

        If there is wounded ship. Try to found other ship's cell

        Returns:
            Cell: player's move
        """
        nbhd = set()

        # search around cells if hits is only 1 cell
        if len(self.hits) == 1:
            nbhd = self.enemy_board.get_nbhd_v(self.hits[0]).union(
                self.enemy_board.get_nbhd_h(self.hits[0]))

        # else if hits more then 1 calc direction and seach
        else:
            # True if vertical, False if horizontal
            is_vertical = self.hits[0].row - self.hits[1].row
            for cell in self.hits:
                nbhd = nbhd.union(self.enemy_board.get_nbhd_v(cell) if is_vertical
                                  else self.enemy_board.get_nbhd_h(cell))

        for cell in nbhd.copy():
            # remove cell if already hits
            if cell in self.move_list:
                nbhd.remove(cell)
                continue

            # remove this cell if area of area hits cells contain wrecks of other ship
            for cell_ in self.enemy_board.get_nbhd(cell):
                if self.enemy_board.get_cell(cell_) == CellState.WRECK and (cell_ not in self.hits):
                    nbhd.discard(cell_)
                    break

        print("CHASE: ", end="")
        return random.choice(list(nbhd))

    def _random_hit(self) -> Cell:
        """Generate random move

        Returns:
            Cell: player's move
        """
        # random shot with some checks (do not be repeted and hit near wrecks)
        while True:
            row = random.randint(0, self.board_size - 1)
            col = random.randint(0, self.board_size - 1)
            target = Cell(row, col)

            if target in self.move_list:
                continue

            # check neighborhood cells for wrecks
            for cell in self.enemy_board.get_nbhd(target):
                if self.enemy_board.get_cell(cell) == CellState.WRECK:
                    target = None
                    break

            # break in acceptable shot
            if target:
                break

        print("RND: ", end="")
        return target

    def _brain(self) -> Cell:
        # if has wounded ship
        if self.hits:
            target = self._chase()

        else:
            target = self._random_hit()

        time.sleep(0.5)
        return target

    def processing_answer(self, answer: ShipState):
        super().processing_answer(answer)

        if answer == ShipState.HIT:
            self.hits.append(self.move_list[-1])
            self.enemy_board.set_cell(self.move_list[-1], CellState.WRECK)
        elif answer == ShipState.SINK:
            self.hits.clear()
            self.enemy_board.set_cell(self.move_list[-1], CellState.WRECK)
        else:
            self.enemy_board.set_cell(self.move_list[-1], CellState.MISS)


class Game:

    def __init__(self, board_size: int, ship_set: list) -> None:
        if 0 < board_size <= 10:
            self.board_size = board_size
        else:
            raise BadBoardException

        self.ship_set = ship_set

        # opponents - list of players
        # player - {"brain": player, "board": board, "enemy": player)

        self.opponents = []

    def place_ships(self, board: Board, ship_set: list):
        # 100 attempt before raise exception
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
                    #print("Resetting board")
                    break

            if len(board.ships) == len(SHIP_SET):
                return

        raise BoardShipPlacementException

    def setup(self) -> bool:
        """Print fome greeting, ask for player names

        Returns:
            bool: True is ok
        """
        global BOARD_STYLE
        print("\nWelcome to Sea Battle Game")
        print("--------------------------\n\n")

        print("Select style\n")
        style_text = """  | 1 | 2 | 3 | 4 | 5 | 6 |            | 1 2 3 4 5 6|
A | О | ■ | ■ | О | ■ | ■ |          --|------------|--
B | О | О | О | О | О | О |          A |████      ██| A
C | ■ | ■ | ■ | О | О | О |          B |      ██    | B
D | О | О | О | О | О | ■ |          C |  ██  ██    | C
"""
        print(style_text)
        print("What kind of board style you prefer? Left one is as required by B7.5.")
        answer = input("Enter 1 - for left, 2 - for right (default is 2): ")
        if answer == "1":
            BOARD_STYLE = 1
        else:
            BOARD_STYLE = 2
        print("\n\nMove format is 'RowColumn' (A1, C4, B3, etc)")
        print("Empty string for exit")
        print("--------------------------\n")
        print("Enter your names. If name is empty then Robot will be assign to this player")
        print()
        name = input("> 1st player name: ")
        if name:
            self.opponents.append(
                {"brain": Human(self.board_size, name), "board": Board(self.board_size)})
            print(f">> Player {name} added to game")
            self.opponents.append(
                {"brain": Robot(self.board_size, "Robot-Right"), "board": Board(self.board_size)})
            self.opponents[-1]["board"].visible = False
            print(">> Player 'Robot-Right' added to game")
        else:
            self.opponents.append(
                {"brain": Robot(self.board_size, "Robot-Left"), "board": Board(self.board_size)})
            print(">> Player 'Robot-Left' added to game")
            name = input("> 2nd player name: ")
            if name:
                self.opponents.append(
                    {"brain": Human(self.board_size, name), "board": Board(self.board_size)})
                print(f">> Player {name} added to game")
                self.opponents[0]["board"].visible = False
            else:
                self.opponents.append(
                    {"brain": Robot(self.board_size, "Robot-Right"),
                     "board": Board(self.board_size)})
                print(">> Player 'Robot-Right' added to game")

        # assign enemy for each player
        try:
            for i, player in enumerate(self.opponents):
                self.place_ships(player["board"], self.ship_set)
                player["enemy"] = self.opponents[(i + 1) % len(self.opponents)]
        except BadBoardException:
            return False
        else:
            print(f'\n\n  {self.opponents[0]["brain"].name} VS {self.opponents[1]["brain"].name}')
            return True

    def _print_2_board(self, player1: Player, player2: Player):
        """Print two boards side by side

        Args:
            player1 (Player): player1
            player2 (Player): player2
        """


        screen1 = []
        screen1.append("  | " + player1["brain"].name)
        screen1 += str(player1["board"]).split("\n")

        screen2 = []
        screen2.append("  | " + player2["brain"].name)
        screen2 += str(player2["board"]).split("\n")

        screen_width = len(max(screen1))
        for l_1, l_2 in zip(screen1, screen2):

            print(f"{l_1:<{screen_width}}          {l_2:<{screen_width}}")

    def start(self):

        turn = 1
        player_in_game = 0

        print("\n\n")

        while True:
            player = self.opponents[player_in_game]

            self._print_2_board(self.opponents[0], self.opponents[0]["enemy"])

            print(f'\nMove # {turn}  {player["brain"]}')
            print("Enter your move: ", end="")

            try:
                cell = player["brain"].ask_move()
                if type(player["brain"]).__name__ == "Robot":
                    print(str(cell))

                if not cell:
                    print(f'\nPlayer {player["brain"]} has left the game')
                    return

                answer = player["enemy"]["board"].shot(cell)
            except BoardOutException:
                print("Out of board shot. Try again\n")
                time.sleep(1)
            except BoardUsedException:
                print("You have already shot this target. Try again\n")
                time.sleep(1)
            else:
                # cls()

                player["brain"].processing_answer(answer)

                if answer == ShipState.HIT:
                    print("\n >>>>>>> Hit! <<<<<<<\n")
                elif answer == ShipState.SINK:
                    print("\n >>>>>>> Sunk!!!! <<<<<<<\n")
                else:
                    print("\n >>>>>>> Miss <<<<<<<\n")
                    player_in_game = 1 - player_in_game

                if not player["enemy"]["board"].ships:
                    winner = player
                    break

                turn += 1

        # "open" opponent boards for final print
        for player in self.opponents:
            player["board"].visible = True
        self._print_2_board(self.opponents[0], self.opponents[0]["enemy"])
        print(f'\nPlayer {winner["brain"]} won!')



# Game
#     init
#     setup
#         create player1 and his Board (Human or Robot based on Player class)
#         create player2 and his Board (Human or Robot based on Player class)
#         place_ships to Boards
#             for ship in ship_set
#                 build a ship
#                 put the ship on the board
#                 if error
#                     try another place
#                 if too many errors
#                     delete all ships and start over
#     battle
#         game loop
#             the Player is asked for a move
#                 Human
#                     used input()
#                 Robot
#                     if there is a wounded ship
#                         search other ship's cells
#                     else
#                         random shot with basic checks
#             the enemy's Board processes this move
#                 check repeated shot
#                 check out of bounds
#                 check all ships for a hit
#                     if any
#                         remove this cell
#                     if no cells in ship
#                         remove ship
#             Player processes the Board's answer
#                 player set marks on his own Board
#             print some game stats
#             check if no ship on board
#                 break
#             if MISS next Player
#         print winner


BOARD_SIZE = 6
SHIP_SET = [3, 2, 2, 1, 1, 1, 1]

def main():

    random.seed(datetime.now().timestamp())

    cls()
    game = Game(BOARD_SIZE, SHIP_SET)
    if game.setup():
        input("\nPress Enter key to start")
        cls()
        game.start()
    else:
        print("\nBoard generation error. Try next time. Sorry")


if __name__ == '__main__':
    main()
