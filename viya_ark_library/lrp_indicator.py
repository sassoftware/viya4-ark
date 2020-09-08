####################################################################
# ### lrp_indicator.py                                           ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import sys
import threading
import time

from typing import Optional, Text


class LRPIndicator:
    """
    Custom context manager used to indicate that a long-running process is currently executing. An :code:`enter_message`
    can be displayed when entering the context manager. While running, a progression of the given :code:`character` will
    display to stdout up to the given :code:`line_length`. Once the :code:`line_length` is reached, the progression of
    :code:`characters` will be removed and the progression will start again from the end of the :code:`enter_message`.
    Upon exit, the line will be filled with the given :code:`character` up to the given :code:`line_length` and a
    configurable :code:`exit_message` will be displayed.
    """

    def __init__(self, enter_message: Text, character: Text = ".", delay: float = 0.9, line_length: int = 50):
        """
        Constructs a new :code:`LRPIndicator` instance.

        :param enter_message: The message to display when entering the context manager.
        :param character: The character to use in the indicator progression.
        :param delay: The delay between printing each character in the progression.
        :param line_length: The total length of the indicator line (i.e. message + character progression).
        """
        # indicator attributes
        self._indicator_char: Text = character
        self._indicator_delay: float = delay
        self._indicator_count: int = 0
        # minimum indicator length is 3 chars
        if len(enter_message) < (line_length - 2):
            self._indicator_total = line_length - len(enter_message)

        # line attributes
        self._line_length: int = line_length

        # status
        self._process_running: bool = False

        # thread
        self._screen_lock: Optional[threading.Lock] = None
        self._thread: Optional[threading.Thread] = None

        # messages
        self._enter_message: Text = enter_message
        # exit message can be set before context exits
        self.exit_message: Text = "DONE"

    def __enter__(self):
        """
        Sets up the thread for running the indicator and displays the :code:`enter_message`.

        :return: This LRPIndicator instance.
        """
        if sys.stdout.isatty():
            # hide the cursor
            sys.stdout.write("\033[?25l")

            # print the enter message
            sys.stdout.write(self._enter_message)
            sys.stdout.flush()

            # start the thread
            self._screen_lock = threading.Lock()
            self._process_running = True
            self._thread = threading.Thread(target=self._indicator_target)
            self._thread.start()
        else:
            sys.stdout.write(self._enter_message.ljust(self._line_length, self._indicator_char))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Closes the indicator context and displays the configured :code:`exit_message`.

        :param exc_type:  The exception type if an error was raised while executing the code block.
        :param exc_val: The exception value if an error was raised while executing the code block.
        :param exc_tb: The traceback if an error was raised while executing the code block.
        """
        if sys.stdout.isatty():
            self._process_running = False
            sys.stdout.write(f"\r{self._enter_message.ljust(self._line_length, self._indicator_char)}")

        # print exit message and move to next line
        sys.stdout.write(f"{self.exit_message}\n")

        # show the cursor again
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def _indicator_target(self):
        """
        Target method for the indicator thread.
        """
        while self._process_running:
            # if the indicator total hasn't been reached, print another
            if self._indicator_count < self._indicator_total:
                sys.stdout.write(self._indicator_char)
                self._indicator_count += 1
            else:
                sys.stdout.write("\r")
                sys.stdout.write(" " * self._line_length)
                sys.stdout.write(f"\r{self._enter_message}")
                self._indicator_count = 0

            sys.stdout.flush()
            time.sleep(self._indicator_delay)
