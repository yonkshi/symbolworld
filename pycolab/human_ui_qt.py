'''
This is an alternative UI that uses PyQT instead of Curses
'''
import datetime
import copy
import time

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPolygon
from PyQt5.QtCore import QPoint, QSize, QRect
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTextEdit
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QFrame


# TODO move this somewhere else
CELL_PIXELS = 10
from pycolab import cropping
from pycolab.protocols import logging as plab_logging

class Window(QMainWindow):
    """
    Simple application window to render the environment into
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle('MiniGrid Gym Environment')

        # Image label to display the rendering
        self.imgLabel = QLabel()
        self.imgLabel.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        # Text box for the mission
        self.missionBox = QTextEdit()
        self.missionBox.setReadOnly(True)
        self.missionBox.setMinimumSize(50, 50)

        # Center the image
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.imgLabel)
        hbox.addStretch(1)

        # Arrange widgets vertically
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.missionBox)

        # Create a main widget for the window
        mainWidget = QWidget(self)
        self.setCentralWidget(mainWidget)
        mainWidget.setLayout(vbox)

        # Show the application window
        self.show()
        self.setFocus()

        self.closed = False

        # Callback for keyboard events
        self.keyDownCb = None

    def closeEvent(self, event):
        self.closed = True

    def setPixmap(self, pixmap):
        self.imgLabel.setPixmap(pixmap)

    def setText(self, text):
        self.missionBox.setPlainText(text)

    def setKeyDownCb(self, callback):
        self.keyDownCb = callback

    def keyPressEvent(self, e):
        if self.keyDownCb == None:
            return

        keyName = None
        if e.key() == Qt.Key_Left:
            keyName = 'LEFT'
        elif e.key() == Qt.Key_Right:
            keyName = 'RIGHT'
        elif e.key() == Qt.Key_Up:
            keyName = 'UP'
        elif e.key() == Qt.Key_Down:
            keyName = 'DOWN'
        elif e.key() == Qt.Key_Space:
            keyName = 'SPACE'
        elif e.key() == Qt.Key_Return:
            keyName = 'RETURN'
        elif e.key() == Qt.Key_Alt:
            keyName = 'ALT'
        elif e.key() == Qt.Key_Control:
            keyName = 'CTRL'
        elif e.key() == Qt.Key_PageUp:
            keyName = 'PAGE_UP'
        elif e.key() == Qt.Key_PageDown:
            keyName = 'PAGE_DOWN'
        elif e.key() == Qt.Key_Backspace:
            keyName = 'BACKSPACE'
        elif e.key() == Qt.Key_Escape:
            keyName = 'ESCAPE'

        if keyName == None:
            return
        self.keyDownCb(e.key())

class HumanUIRenderer:
    def __init__(self, width, height, ownWindow=False):
        self.width = width
        self.height = height

        self.img = QImage(width, height, QImage.Format_RGB888)
        self.painter = QPainter()

        self.app = QApplication([])
        self.window = Window()

    def close(self):
        """
        Deallocate resources used
        """
        pass

    def beginFrame(self):
        self.painter.begin(self.img)
        self.painter.setRenderHint(QPainter.Antialiasing, False)

        # Clear the background]
        self.painter.setBrush(QColor(0, 0, 0))
        self.painter.drawRect(0, 0, self.width - 1, self.height - 1)



    def endFrame(self):
        self.painter.end()

        if self.window:
            if self.window.closed:
                self.window = None
            else:
                self.window.setPixmap(self.getPixmap())
                self.app.processEvents()

    def getPixmap(self):
        return QPixmap.fromImage(self.img)

    def getArray(self):
        """
        Get a numpy array of RGB pixel values.
        The array will have shape (height, width, 3)
        """

        numBytes = self.width * self.height * 3
        buf = self.img.bits().asstring(numBytes)
        output = np.frombuffer(buf, dtype='uint8')
        output = output.reshape((self.height, self.width, 3))

        return output

    def push(self):
        self.painter.save()

    def pop(self):
        self.painter.restore()

    def rotate(self, degrees):
        self.painter.rotate(degrees)

    def translate(self, x, y):
        self.painter.translate(x, y)

    def scale(self, x, y):
        self.painter.scale(x, y)

    def setLineColor(self, r, g, b, a=255):
        self.painter.setPen(QColor(r, g, b, a))

    def setColor(self, r, g, b, a=255):
        self.painter.setBrush(QColor(r, g, b, a))

    def setLineWidth(self, width):
        pen = self.painter.pen()
        pen.setWidthF(width)
        self.painter.setPen(pen)

    def drawLine(self, x0, y0, x1, y1):
        self.painter.drawLine(x0, y0, x1, y1)

    def drawCircle(self, x, y, r):
        center = QPoint(x, y)
        self.painter.drawEllipse(center, r, r)

    def drawPolygon(self, points):
        """Takes a list of points (tuples) as input"""
        points = map(lambda p: QPoint(p[0], p[1]), points)
        self.painter.drawPolygon(QPolygon(points))

    def drawPolyline(self, points):
        """Takes a list of points (tuples) as input"""
        points = map(lambda p: QPoint(p[0], p[1]), points)
        self.painter.drawPolyline(QPolygon(points))

    def fillRect(self, x, y, width, height, color):
        # Hard code alpha into colors
        self.painter.fillRect(QRect(x, y, width, height), QColor(*color, 99))

class HumanUI:
    def __init__(self, rows, cols,
                 delay,
                 croppers = None,
                 repainter = None,
                 keys_to_actions = None, ):

        self.rows = rows
        self.cols = cols

        self.qt_renderer = None

        self._delay = delay
        self._repainter = repainter
        self._game = None
        self._keys_to_actions = keys_to_actions
        if croppers is None:
            self._croppers = [cropping.ObservationCropper()]
        else:
            self._croppers = croppers


    def play(self, game_engine):
        """Play a pycolab game.

        Calling this method initialises curses and starts an interaction loop. The
        loop continues until the game terminates or an error occurs.

        This method will exit cleanly if an exception is raised within the game;
        that is, you shouldn't have to reset your terminal.

        Args:
          game: a pycolab game. Ths game must not have had its `its_showtime` method
              called yet.

        Raises:
          RuntimeError: if this method is called while a game is already underway.
        """

        if self._game is not None:
            raise RuntimeError('CursesUi is not at all thread safe')
        self._game = game_engine
        self._start_time = datetime.datetime.now()
        # Inform the croppers which game we're playing.
        for cropper in self._croppers:
            cropper.set_engine(self._game)

        # After turning on curses, set it up and play the game.
        self._init_qt_and_play()

        # The game has concluded. Print the final statistics.
        duration = datetime.datetime.now() - self._start_time
        print('Game over! Final score is {}, earned over {}.'.format(
            self._total_return, duration))

        # Clean up in preparation for the next game.
        self._game = None
        self._start_time = None
        self._total_return = None

    def _init_qt_and_play(self):
        """Set up an already-running curses; do interaction loop.

        This method is intended to be passed as an argument to `curses.wrapper`,
        so its only argument is the main, full-screen curses window.

        Args:
          screen: the main, full-screen curses window.

        Raises:
          ValueError: if any key in the `keys_to_actions` dict supplied to the
              constructor has already been reserved for use by `CursesUi`.
        """

        # if self._delay is None:  # TODO Change to PYQT blocking timer
        #     screen.timeout(-1)  # Blocking reads
        # else:
        #     screen.timeout(self._delay)  # Nonblocking (if 0) or timing-out reads

        # By default, the log display window is hidden
        paint_console = False

        # Kick off the game---get first observation, crop and repaint as needed,
        # initialise our total return, and display the first frame.

        # TODO update observation so it's RGB based rather than txt based
        observation, reward, _ = self._game.its_showtime()
        self.observations = self._crop_and_repaint(observation)
        self._total_return = reward
        self._display(
            self.observations, self._total_return, elapsed=datetime.timedelta())
        self.qt_renderer.window.setKeyDownCb(self._key_down_cb)
        # Oh boy, play the game!

        while not self._game.game_over:
            time.sleep(self._delay / 1000.0)

            observation, reward, _ = self._game.play(4) # Do nothing # TODO make do nothing more generalized
            self._display(
                self.observations, self._total_return, elapsed=datetime.timedelta())

            # If the window was closed
            if self.qt_renderer.window == None:
                break

            # Update the game display, regardless of whether we've called the game's
            # play() method.
            elapsed = datetime.datetime.now() - self._start_time
            self._display(self.observations, self._total_return, elapsed)

            # TODO Add logging support

            ## self._update_game_console(
            ##    plab_logging.consume(self._game.the_plot), console, paint_console)

    def _crop_and_repaint(self, observation):
        # Helper for game display: applies all croppers to the observation, then
        # repaints the cropped subwindows. Since the same repainter is used for
        # all subwindows, and since repainters "own" what they return and are
        # allowed to overwrite it, we copy repainted observations when we have
        # multiple subwindows.
        observations = [cropper.crop(observation) for cropper in self._croppers]
        if self._repainter:
            raise NotImplementedError('I have not had time to implement the repainter module')
        else:
            return observations

    def _key_down_cb(self, keycode):
        # Wait (or not, depending) for user input, and convert it to an action.
        # Unrecognised keycodes cause the game display to repaint (updating the
        # elapsed time clock and potentially showing/hiding/updating the log
        # message display) but don't trigger a call to the game engine's play()
        # method. Note that the timeout "keycode" -1 is treated the same as any
        # other keycode here.
        if keycode in self._keys_to_actions:
            # Convert the keycode to a game action and send that to the engine.
            # Receive a new observation, reward, discount; crop and repaint; update
            # total return.
            action = self._keys_to_actions[keycode]
            observation, reward, _ = self._game.play(action)
            self.observations = self._crop_and_repaint(observation)
            if self._total_return is None:
                self._total_return = reward
            elif reward is not None:
                self._total_return += reward

            elapsed = datetime.datetime.now() - self._start_time
            self._display(self.observations, self._total_return, elapsed)



    def _render_grid(self, r):
        '''
        Renders the grid and draws lines
        :param r:
        :param tile_size:
        :return:
        '''

        assert r.height == self.rows * CELL_PIXELS
        assert r.width == self.cols * CELL_PIXELS

        # End drawing grid

    def _display(self, observations, score, elapsed):
        """Redraw the game board onto the screen, with elapsed time and score.

        Args:
          screen: the main, full-screen curses window.
          observations: a list of `rendering.Observation` objects containing
              subwindows of the current game board.
          score: the total return earned by the player, up until now.
          elapsed: a `datetime.timedelta` with the total time the player has spent
              playing this game.
        """
        #screen.erase()  # Clear the screen

        # Display the game clock and the current score.

        # TODO add score information
        ##screen.addstr(0, 2, _format_timedelta(elapsed), curses.color_pair(0))
        ##screen.addstr(0, 20, 'Score: {}'.format(score), curses.color_pair(0))

        # Display cropped observations side-by-side.
        for observation in observations:
            # TODO Add "God View" for observations
            board = observation.board
            assert board.shape[0] == self.rows
            assert board.shape[1] == self.cols

            if self.qt_renderer is None:
                from gym_minigrid.rendering import Renderer
                self.qt_renderer = HumanUIRenderer(
                    width=self.cols * CELL_PIXELS,
                    height=self.rows * CELL_PIXELS,
                    ownWindow=True,
                )
            r = self.qt_renderer

            # if r.window:
            #     r.window.setText("Hi I am Yonk")

            r.beginFrame()

            # Render grid
            # Total grid size at native scale

            widthPx = self.cols * CELL_PIXELS
            heightPx = self.rows * CELL_PIXELS

            r.push()

            r.fillRect(
                0,
                0,
                widthPx,
                heightPx,
                (0,0,0), #black color
            )
            # Draw grid lines
            r.setLineColor(33, 33, 33)
            for rowIdx in range(0, self.rows):
                y = CELL_PIXELS * rowIdx
                r.drawLine(0, y, widthPx, y)
            for colIdx in range(0, self.cols):
                x = CELL_PIXELS * colIdx
                r.drawLine(x, 0, x, heightPx)

            r.pop()

            # Render each cell
            # TODO More efficient rendering, render as bitmap frames
            for row, row_data in enumerate(board):
                for cell, color in enumerate(row_data):
                    # Highlight the cell
                    r.fillRect(
                        cell * CELL_PIXELS,
                        row * CELL_PIXELS,
                        CELL_PIXELS,
                        CELL_PIXELS,
                        color
                    )

            r.endFrame()

            self._update_console(
                plab_logging.consume(self._game.the_plot))

    def _update_console(self, messagees):
        '''
        Pushes messages into the console
        :param message:
        :return:
        '''
        for message in messagees:
            self.qt_renderer.window.setText(message)

