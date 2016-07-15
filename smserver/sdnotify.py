#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""
    Provide sd_notify wrapper to notify service manager about start-up
    completion and other service
"""

import socket
import os
import logging

class SDNotify(object):
    """
        Notify service manager about start-up completion and other service
        status changes

        :Example:

        >>> sd_notify = DSNotify()
        >>> sd_notify.ready()
    """

    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        addr = os.getenv('NOTIFY_SOCKET')
        if not addr:
            self.available = False
            return

        if addr[0] == '@':
            addr = '\0' + addr[1:]

        self.sock.connect(addr)
        self.available = True

    def notify(self, state):
        """
            Notify may be called by a service to notify the service manager
            about state changes.

            It can be used to send arbitrary information, encoded in an
            environment-block-like string.

            Most importantly, it can be used for start-up completion notification.
        """

        if not self.available:
            return

        self.sock.sendall(state.encode('utf-8'))

    def status(self, status):
        """
            Passes a single-line UTF-8 status string back to the service
            manager that describes the service state.

            This is free-form and can be used for various purposes:
        """

        self.notify("STATUS=%s" % status)

    def ready(self):
        """
            Tells the service manager that service startup is finished.

            This is only used by systemd if the service definition file has
            Type=notify set.
        """

        self.notify("READY=1")

    def stopping(self):
        """
            Tells the service manager that the service is beginning its shutdown.

            This is useful to allow the service manager to track the service's
            internal state, and present it to the user.
        """

        self.notify("STOPPING=1")

    def reloading(self):
        """
            Tells the service manager that the service is reloading its
            configuration.

            This is useful to allow the service manager to track the service's
            internal state, and present it to the user.

            Note that a service that sends this notification must also send a
            ready notification when it completed reloading its configuration.
        """

        self.notify("STOPPING=1")

    def watchdog(self):
        """
            Tells the service manager to update the watchdog timestamp.

            This is the keep-alive ping that services need to issue in regular
            intervals if WatchdogSec= is enabled for it.
        """

        self.notify("WATCHDOG=1")
