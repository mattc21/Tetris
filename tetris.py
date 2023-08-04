from collections import deque
from time import time
from enum import IntEnum
from random import randint
from functools import reduce
import curses
import sys

"""
Tetris pieces can be thought 

"""



class Playfield:
    class Index(IntEnum):
        ROW = 0
        COL = 1
        PIECE = 2

    def __init__(self) -> None:
        self.width = 10
        self.depth = 20
        self.board = [[0 for _ in range(self.width)] for _ in range(self.depth)]
        self.pendingObject = None
        self.gameEnded = False
        self.gameScore = 0

    def addPiece(self, piece):
        self.pendingObject = [0, self.width//2, piece]

    def checkOverlaps(self) -> bool:
        pieceY, pieceX, piece = self.pendingObject
        for y, row in enumerate(piece.getMatrix()):
            for x, val in enumerate(row):
                if val != 0 and (pieceY + y >= self.depth or pieceY + y < 0 or \
                      pieceX + x < 0 or pieceX + x >= self.width or\
                        val + self.board[pieceY + y][pieceX + x] != val):
                    return True
        return False

    def persistObject(self) -> None:
        if self.checkOverlaps() is True:
            self.gameEnded = True
        self._persistObjectToBoard(self.board)
        self.clearLines()
    
    def clearLines(self) -> None:
        newBoard = []
        linesDeleted = 0
        for row in self.board:
            if reduce(lambda a, b: a*b, row) != 0:
                linesDeleted += 1
            else:
                newBoard.append(row)

        self.gameScore += 100 * linesDeleted **2
        self.board = [[0]*self.width]*linesDeleted + newBoard


    def _persistObjectToBoard(self, board) -> None:
        pieceY, pieceX, piece = self.pendingObject
        for y, row in enumerate(piece.getMatrix()):
            for x, val in enumerate(row):
                if val != 0:
                    if pieceY + y >= self.depth or pieceY + y < 0 or \
                        pieceX + x < 0 or pieceX + x >= self.width:
                        return True
                    board[pieceY + y][pieceX + x] = val
        return False

    # Returns true if object persists as result of drop
    def dropOne(self) -> bool:
        self.pendingObject[Playfield.Index.ROW] += 1
        assert(self.pendingObject[Playfield.Index.PIECE] is not None)
        if self.checkOverlaps() is True:
            self.pendingObject[Playfield.Index.ROW] -= 1
            self.persistObject()
            return True
        return False
    
    def rotateCW(self) -> bool:
        piece = self.pendingObject[Playfield.Index.PIECE]
        piece.rotateCW()
        if self.checkOverlaps() is True:
            piece.rotateCCW()
            return False
        return True

    def rotateCCW(self) -> bool:
        piece = self.pendingObject[Playfield.Index.PIECE]
        piece.rotateCCW()
        if self.checkOverlaps() is True:
            piece.rotateCW()
            return False
        return True

    def moveLateral(self, yMov):
        self.pendingObject[Playfield.Index.COL] += yMov
        if self.checkOverlaps() is True:
            self.pendingObject[Playfield.Index.COL] -= yMov
            return False
        return True

    def getBoard(self):
        output = [row[:] for row in self.board]
        self._persistObjectToBoard(output)
        return output

    def checkEnded(self):
        return self.gameEnded
    def getScore(self):
        return self.gameScore


class GameRuntime:
    def __init__(self, view) -> None:
        self.field = Playfield()
        self.queue = deque()
        self.prevDropTime = time()
        self.moveTime = 1
        for _ in range(3):
            self.generatePiece()
        self.field.addPiece(self.queue.pop())
        self.view = view

    def generatePiece(self) -> None:
        self.queue.append(Piece.generateRandomPiece())

    def dropPiece(self):
        output = self.field.dropOne()
        if output is True:
            self.generatePiece()
            assert(len(self.queue) != 0) 
            self.field.addPiece(self.queue.pop())
        return output

    def gameLoop(self, stdscr) -> None:
        self.view.display(stdscr, self.field.getBoard(), f"Game Score: 0")
        while True:
            hasChanged = False
            newTime = time()
            if newTime - self.prevDropTime > self.moveTime:
                self.dropPiece()
                hasChanged = True
                self.prevDropTime = newTime
                
            c = stdscr.getch()
            if c != -1:
                if c == curses.KEY_LEFT:
                    hasChanged = self.field.moveLateral(-1)
                elif c == curses.KEY_RIGHT:
                    hasChanged = self.field.moveLateral(1)
                elif c == curses.KEY_DOWN:
                    self.dropPiece()
                    hasChanged = True 
    
                elif c == ord(' '):
                    while self.dropPiece() != True:
                        pass
                    hasChanged = True

                elif c == curses.KEY_UP:
                    hasChanged = self.field.rotateCW()
                elif c == ord('z'):
                    hasChanged = self.field.rotateCCW()
            printedHeader = f"Game Score: {self.field.getScore()}"
            
            if self.field.checkEnded() is True:
                printedHeader += f" GAME OVER"
                self.view.display(stdscr, self.field.getBoard(), printedHeader)
                break 

            if hasChanged is True:
                self.view.display(stdscr, self.field.getBoard(), printedHeader)


class Printer():
    def __init__(self):
        self.firstTime = True
        # begin_x = 20; begin_y = 7
        # height = 5; width = 40
        # win = curses.newwin(height, width, begin_y, begin_x)


    def display(self, stdscr, board, printedHeader):
        stdscr.clear()
        stdscr.addstr(0, 0, printedHeader)
        for lineNum, row in enumerate(board, 1):
            for colNum, val in enumerate(row):
                toShow = "#" if val == 0 else str(val)
                stdscr.addstr(lineNum, colNum, toShow, curses.color_pair(val))
        stdscr.refresh()
        


class Piece:
    def __init__(self, matrix) -> None:
        self.mat = matrix          # Want a lot of these to represent the different shapes

    @staticmethod
    def generateRandomPiece():
        shape = None

        shapeType = randint(1, 7)
        match shapeType:
            case 1:
                shape = [[0]*4, [shapeType]*4, [0]*4, [0]*4]
            case 2:
                shape = [[shapeType,0,0], [shapeType]*3, [0]*3]
            case 3:
                shape = [[0,0,shapeType], [shapeType]*3, [0,0,0]]
            case 4:
                shape = [[shapeType]*2]*2
            case 5:
                shape = [[0] + [shapeType]*2, [shapeType]*2 + [0], [0]*3]
            case 6:
                shape = [[0,shapeType,0], [shapeType]*3, [0]*3]
            case 7:
                shape = [[shapeType]*2 + [0], [0] + [shapeType]*2, [0]*3]            
            case _:
                raise "Error"


        return Piece(shape)        


    def rotateCW(self) -> None:
        temp = []
        for n in range(len(self.mat[0])):
            temp.append([row[n] for row in reversed(self.mat)])
        self.mat = temp
    
    def rotateCCW(self) -> None:
        for _ in range(3):
            self.rotateCW()
        

    def getMatrix(self) -> list[list[int]]:
        return self.mat




def main(stdscr):
     # curses.init_pair(0, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_RED, curses.COLOR_BLACK)
    
    while True:
        stdscr.nodelay(True)
        game = GameRuntime(Printer())
        game.gameLoop(stdscr)
        stdscr.nodelay(False)
        while stdscr.getch() != ord(' '):
            pass

if __name__ == "__main__":
    curses.wrapper(main)