"""
Highway Rush  —  Advanced Python Pygame Project
Run:  python main.py
Requires: pip install pygame numpy
"""

import pygame
from game import Game


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
