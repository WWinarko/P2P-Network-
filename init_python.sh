#!/bin/sh

xterm -hold -title "Peer 2" -e "python3 p2p.py init 2 4 5 15" &

xterm -hold -title "Peer 4" -e "python3 p2p.py init 4 5 8 15" &

xterm -hold -title "Peer 5" -e "python3 p2p.py init 5 8 9 15" &

xterm -hold -title "Peer 8" -e "python3 p2p.py init 8 9 14 15" &

xterm -hold -title "Peer 9" -e "python3 p2p.py init 9 14 19 15" &

xterm -hold -title "Peer 14" -e "python3 p2p.py init 14 19 2 15" &

xterm -hold -title "Peer 19" -e "python3 p2p.py init 19 2 4 15" & 