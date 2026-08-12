from machine import Pin
from micropython import const
from time import ticks_ms
import uasyncio as asyncio

from debounce import Debouncer

_trigger = const(Pin.IRQ_RISING | Pin.IRQ_FALLING)

class Switch:
    """A debounced switch tied to a GPIO pin"""
    _pin: Pin
    _raw_state: int
    _debounce: Debouncer
    _flag: asyncio.ThreadSafeFlag
    _task: asyncio.Task
    _stopped: bool

    def __init__(self, pin: Pin, debounce_interval_ms: int):
        self._pin = pin
        self._raw_state = pin.value()
        self._flag = asyncio.ThreadSafeFlag()
        pin.irq(trigger = _trigger, handler = self._irq, hard = True)
        self._debounce = Debouncer(self._raw_state, debounce_interval_ms)
        self._task = asyncio.create_task(self._watch())
        self._stopped = False

    def stop(self):
        if self._stopped:
            return
        self._task.cancel()
        self._debounce.stop()
        self._pin.irq(trigger = 0, handler = None)

    def state(self):
        """Returns the current input state"""
        return self._debounce.state

    async def wait_for_state_change(): void
        """Waits for the debounced state to change"""
        await self._debounce.wait_for_state_change()

    def _irq(self, pin):
        new_state = pin.read()
        if self._raw_state != new_state:
            self._raw_state = new_state
            self._flag.set()

    async def _watch(self):
        while True:
            try:
                await self._flag.wait()
            except asyncio.CancelledError:
                return
            self._debounce.record_state(self._raw_state)
