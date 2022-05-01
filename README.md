# sea_battle
```
Game
    init
    setup
        create player1 and his Board (Human or Robot based on Player class)
        create player2 and his Board (Human or Robot based on Player class)
        place_ships to Boards
            for ship in ship_set
                build ship
                put it on board
                if error
                    try another place
                if to many error
                    clear all ships and start from begining
    battle
        game loop
            Player is asked for move
                Human
                    used input()
                Robot
                    if there is a wounded ship
                        search other ship's cells
                    else
                        random shot with basic checks
            enemy Board procees this move
                check repeated shot
                check out of bounds
                check all ships to hit
                    if any
                        remove this cell
                    if no cells in ship
                        remove ship
            Player proceed Board's answer
                player set marks on his own Board
            print some game stats
            check if no ship on board
                break
            if MISS next Player
        print winner
```
