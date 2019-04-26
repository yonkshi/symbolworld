#!/usr/bin/env python3

from __future__ import division, print_function

import sys
import numpy
from PyQt5.QtCore import Qt
import gym
import time
from optparse import OptionParser
import pycolab


def main():
    parser = OptionParser()
    parser.add_option(
        "-e",
        "--env-name",
        dest="env_name",
        help="gym environment to load",
        default='SymbolWorld-v0'
    )
    (options, args) = parser.parse_args()

    # Load the gym environment
    env = gym.make(options.env_name)

    def resetEnv():
        env.reset()
        if hasattr(env, 'mission'):
            print('Mission: %s' % env.mission)

    resetEnv()

    # Create a window to render into
    renderer = env.render('human')

    def keyDownCb(keyName):
        if keyName == 'BACKSPACE':
            resetEnv()
            return

        if keyName == 'ESCAPE':
            sys.exit(0)

        action = 0

        if keyName == Qt.Key_Left:
            action = env.actions.left
        elif keyName == Qt.Key_Right:
            action = env.actions.right
        elif keyName == Qt.Key_Up:
            action = env.actions.up
        elif keyName == Qt.Key_Down:
            action = env.actions.down
        else:
            print("unknown key %s" % keyName)
            return

        obs, reward, done, info = env.step(action)

        #print('step=%s, reward=%.2f' % (env.step_count, reward))

        if done:
            print('done!')
            resetEnv()

    renderer.window.setKeyDownCb(keyDownCb)

    while True:
        env.render('human')
        time.sleep(0.1)

        obs, reward, done, info = env.step(env.actions.stay)

        #print('step=%s, reward=%.2f' % (env.step_count, reward))

        if done:
            print('done!')
            resetEnv()
        # If the window was closed
        if renderer.window == None:
            break

if __name__ == "__main__":
    main()
