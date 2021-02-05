"""Main module."""
from threading import Event, Thread

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

    def __init__(self, stream=None):
        self._output_thread = None
        self._exit = None
        if stream:
            self.monitor(stream=stream)

    def flush(self, out=None):
        """
        Prints the target streams output i.e. stdout or stderr to stdout.

        """
        while not self._exit and out and not out.closed:
            try:
                for line in iter(out.readline, b""):
                    print(line.decode())
            except ValueError:
                print("Streamer :: The stream closed while being read from")
                break

    def monitor(self, *, stream):
        """
        Start monitoring the output streams of the target process.

        Once a stream is already being monitored, calling monitor does nothing.

        [stream] process.stdout | process.stderr
        """
        is_monitoring = self._output_thread and self._output_thread.is_alive()

        if is_monitoring:
            return

        self._exit = Event()

        self._output_thread = Thread(target=self.flush, args=(stream))
        self._output_thread.daemon = True
        self._output_thread.start()

    def stop(self):
        """
        Stops monitoring the stream
        """
        self._exit.set()
        self._output_thread.join()
