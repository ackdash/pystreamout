"""Main module."""
from threading import Event, Thread
from typing import BinaryIO
import time


class Streamer:
    """
    Streams output from a target process' stream to stdout (non-blocking).

    ```
    # Usage 1
    target_process = subprocess.Popen(
        ["watch", "-n", "2", "ls"],
        stdout=subprocess.PIPE,
        close_fds=True,
    )
    Streamer(stream=target_process.stdout)
    ```

    ```
    # Usage 2
    streamer = Streamer()
    target_process = subprocess.Popen(
        ["watch", "-n", "2", "ls"],
        stdout=subprocess.PIPE,
        close_fds=True,
    )
    streamer.monitor(stream=target_process.stdout)
    ```
    """

    _messages = {
        "output_thread_is_none": """
            Streamer :: Nothing is being monitored.
            Pass a stream to be monitored to the Streamer constructor or to the monitor instance method
            """,
        "streamer_closed_early": "Streamer :: The stream closed while being read from",
        "finished": "Streamer :: done",
        "already_monitoring": "Streamer :: Already monitoring",
        "stream_none": "Streamer :: The given stream to monitor is None",
        "stop_but_not_monitoring": "Streamer :: stop called but not monitoring",
    }

    def __init__(self, *, stream=None, verbose=False):
        self._output_thread = None
        self._exit = None
        self.verbose = verbose
        if stream is not None:
            self.monitor(stream=stream)

    def print(self, message):
        if self.verbose:
            print(message)

    def __flush(self, stream):
        """
        Prints the target stream's output i.e. stdout or stderr to stdout.

        :param stream: The stream to monitor [process.stdout | process.stderr]
        """

        if self._output_thread is None:
            self.print(self._messages["output_thread_is_none"])
            return self._cleanup()

        while (
            self._exit is not None
            and not self._exit.is_set()
            and stream is not None
            and isinstance(stream, BinaryIO)
            and not stream.closed
        ):
            try:
                buffer_size = 0
                for line in iter(stream.readline, b""):
                    print(line.decode())
                    if buffer_size % 10 == 0:
                        time.sleep(0)
            except ValueError:
                self.print(self._messages["streamer_closed_early"])
                break

        self._cleanup()

    def is_monitoring(self):
        """
        Check if the Streamer is monitoring or not
        """
        return (
            self._output_thread
            and self._output_thread.is_alive()
            and not self._exit.is_set()
        )

    def _cleanup(self):
        """
        Perform clean up tasks
        """
        self.print(self._messages["finished"])

    def monitor(self, *, stream):
        """
        Start monitoring the output streams of the target process.
        Once a stream is already being monitored, calling monitor does nothing.

        :param stream: The stream to monitor [process.stdout | process.stderr]
        """
        if self.is_monitoring():
            self.print(self._messages["already_monitoring"])
            return

        if stream is None:
            self.print(self._messages["stream_none"])
            return

        self._exit = Event()

        self._output_thread = Thread(target=self.__flush, args=(stream,))
        self._output_thread.daemon = True
        self._output_thread.start()

    def stop(self):
        """
        Stops monitoring the stream
        """
        if not self.is_monitoring():
            self.print(self._messages["stop_but_not_monitoring"])
            return

        self._exit.set()

        time.sleep(0)
        self._output_thread.join()
