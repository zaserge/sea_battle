# sea_battle

```text
Game
    init
    setup
        create player1 and his Board (Human or Robot based on Player class)
        create player2 and his Board (Human or Robot based on Player class)
        place_ships to Boards
            for ship in ship_set
                build a ship
                put the ship on the board
                if error
                    try another place
                if too many errors
                    delete all ships and start over
    battle
        game loop
            the Player is asked for a move
                Human
                    used input()
                Robot
                    if there is a wounded ship
                        search other ship's cells
                    else
                        random shot with basic checks
            the enemy's Board processes this move
                check repeated shot
                check out of bounds
                check all ships for a hit
                    if any
                        remove this cell
                    if no cells in ship
                        remove ship
            Player processes the Board's answer
                player set marks on his own Board
            print some game stats
            check if no ship on board
                break
            if MISS next Player
        print winner
```
