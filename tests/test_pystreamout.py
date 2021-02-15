#!/usr/bin/env python

"""Tests for `pystreamout` package.
"""
import time
from typing import Iterable, Iterator
import pytest
from pystreamout.pystreamout import Streamer

from .mocks.MockStream import MockStream


@pytest.fixture
def patchedOpenMockStream(monkeypatch):
    """
    A fixture that creates a stream that is open.
    """
    monkeypatch.setattr(MockStream, "closed", False)
    return MockStream()


@pytest.fixture
def patchedOpenExcepRasingMockSteam(monkeypatch):
    """
    A fixture that creates an open stream that raises a ValueError when read from.
    Streams indicate they have been closed by raising a ValueError.
    """

    def raiser(self):
        raise ValueError

    monkeypatch.setattr(MockStream, "closed", False)
    monkeypatch.setattr(MockStream, "readline", raiser)

    return MockStream(data=[[b"a", b"b", b"c", b"d", b""]])


def test_content(capsys, monkeypatch, patchedOpenMockStream):
    """
    Ensure that content is read from a stream is printed to stdout as expected
    """

    mockStream = patchedOpenMockStream
    mockStream.set_data(data=[[b"a", b"b", b"c", b"d", b""]])
    streamer = Streamer(stream=mockStream, verbose=True)

    wait_for(streamer, mockStream, monkeypatch)

    out, err = capsys.readouterr()
    assert out == f"a\nb\nc\nd\n{streamer._messages['finished']}\n"
    assert err == ""


def test_content_silent(capsys, monkeypatch, patchedOpenMockStream):
    """
    Ensure that content is read from a stream is printed to stdout as expected
    """

    mockStream = patchedOpenMockStream
    mockStream.set_data(data=[[b"a", b"b", b"c", b"d", b""]])
    streamer = Streamer(stream=mockStream, verbose=False)

    wait_for(streamer, mockStream, monkeypatch)

    out, err = capsys.readouterr()
    assert out == "a\nb\nc\nd\n"
    assert err == ""


def test_stream_close(capsys, patchedOpenExcepRasingMockSteam):
    """
    Tests that Streamer handles a closed stream properly
    """

    mockStream = patchedOpenExcepRasingMockSteam
    streamer = Streamer(stream=mockStream, verbose=True)

    while streamer.is_monitoring():
        pass

    out, err = capsys.readouterr()
    assert (
        out
        == f"{streamer._messages['streamer_closed_early']}\n{streamer._messages['finished']}\n"
    )
    assert err == ""


def test_non_blocking(capsys, monkeypatch, patchedOpenMockStream):
    """
    Ensure that Streamer does not block
    """

    mockStream = patchedOpenMockStream
    mockStream.set_data(data=[[b"Sa", b"Sa", b"Sa", b""], [b"Sa", b"Sa", b"Sa", b""]])
    mockStream.set_delay(delay=0.1)

    streamer = Streamer(stream=mockStream, verbose=True)
    print("TEST_TOKEN")

    wait_for(streamer, mockStream, monkeypatch)

    out, err = capsys.readouterr()
    assert "a\nTEST_TOKEN\nS" in out
    assert err == ""


def test_two_calls_to_monitor(capsys, monkeypatch, patchedOpenMockStream):
    """
    After the initial call to the monitor method, subsequent calls
    do nothing i.e. do not duplicate output to stdout or stderr
    """

    mockStream = patchedOpenMockStream
    mockStream.set_data(data=[[b"a", b"b", b"c", b"d", b""]])

    streamer = Streamer(verbose=True)
    streamer.monitor(stream=mockStream)
    streamer.monitor(stream=mockStream)

    wait_for(streamer, mockStream, monkeypatch)

    out, err = capsys.readouterr()
    assert streamer._messages["already_monitoring"] in out
    assert err == ""


def test_stream_call_to_flush_directly(capsys):
    """
    Tests that if a call to the flush method is called (it shouldn't be called directly)
    and no process is being monitored then a message is printed to stdout but it doesn't raise
    an exception.
    """

    streamer = Streamer(verbose=True)
    none_stream = None
    streamer._Streamer__flush(stream=none_stream)

    out, err = capsys.readouterr()
    assert streamer._messages["output_thread_is_none"] in out
    assert err == ""


def test_none_stream_fails(capsys):
    """
    Tests that if a call to the flush method is called (it shouldn't be called directly)
    and no process is being monitored then a message is printed to stdout but it doesn't raise
    an exception.
    """

    streamer = Streamer(verbose=True)
    none_stream = None
    streamer.monitor(stream=none_stream)

    out, err = capsys.readouterr()
    assert streamer._messages["stream_none"] in out
    assert err == ""


def wait_for(streamer, mockStream, monkeypatch):
    while streamer.is_monitoring():
        if mockStream.should_close:
            monkeypatch.setattr(MockStream, "closed", True)
        pass


def test_multiple_streamers(capsys, monkeypatch):
    """
    Ensure that Streamers are self contained
    """
    monkeypatch.setattr(MockStream, "closed", False)

    mockStream1 = MockStream()
    mockStream1.set_data(
        data=[[b"1-1a", b"1-1b", b"1-1c", b""], [b"1-2a", b"1-2b", b"1-2c", b""]]
    )
    mockStream1.set_delay(delay=0.1)

    mockStream2 = MockStream()
    mockStream2.set_data(
        data=[[b"2-1a", b"2-1b", b"2-1c", b""], [b"2-2a", b"2-2b", b"2-2c", b""]]
    )
    mockStream2.set_delay(delay=0.1)

    streamer1 = Streamer(stream=mockStream1, verbose=True)
    streamer2 = Streamer(stream=mockStream2, verbose=True)

    time.sleep(0.2)
    wait_for(streamer1, mockStream1, monkeypatch)
    wait_for(streamer2, mockStream2, monkeypatch)

    out, err = capsys.readouterr()
    assert (
        out
        == f"1-1a\n1-1b\n1-1c\n2-1a\n2-1b\n2-1c\n1-2a\n1-2b\n1-2c\n2-2a\n2-2b\n2-2c\n{Streamer._messages['finished']}\n{Streamer._messages['finished']}\n"
    )
    assert err == ""


def test_streamer_stop(monkeypatch):
    """
    Ensure that stopping stops the streamer printing to stdout
    """
    count = 0

    def infinite_readline(self):
        time.sleep(0.1)
        return b"" if count % 10 == 0 else b"_"

    monkeypatch.setattr(MockStream, "closed", False)
    monkeypatch.setattr(MockStream, "readline", infinite_readline)
    mockStream = MockStream()

    streamer = Streamer(stream=mockStream, verbose=True)
    assert streamer.is_monitoring()
    streamer.stop()
    assert not streamer.is_monitoring()


def test_streamer_stop_on_not_monitoring(capsys):
    """
    Ensure that calling stop on a streamer that is not monitoring is handled gracefully
    """
    streamer = Streamer(verbose=True)
    streamer.stop()

    out, err = capsys.readouterr()

    assert streamer._messages["stop_but_not_monitoring"] in out
    assert err == ""
