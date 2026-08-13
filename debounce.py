import uasyncio as asyncio
from time import ticks_diff, ticks_ms

class Debouncer:
    """Debounces an arbitrary input

    This suppresses transitions from a given state back to the previously
    observed state if the return transitions happen faster than the given interval.

    This design is meant to be interrupt-driven.
    Here's a rough overview of the state transitions:

    The underlying switch has a current state, and the debouncer has a control state and a debounced switch state.
    The debouncer starts in the "stable" control state with an initial debounced state value matching the switch.
    When it receives a new switch state via `record_state`, it enters the "freshly switched" control state.
    If it stays in that state for a duration of `interval_ms`, it (implicitly) transitions to "stable".
    If it instead detects a transition to the previous switch state while "freshly switched", it enters the "bouncing" control state.
    If `interval_ms` elapses in the "bouncing" state without the switch state changing, the debounced state transitions to the previous switch state and we enter the "stable" control state.
    Bouncing back to the current state cancels the "bouncing" state, transitioning to "freshly switched" again.
    On any other switch state transition, the debouncer switches immediately to "freshly switched" and accepts the new switch state.
    This is useful for multi-state inputs such as rotary encoders, which may make rapid "forward" transitions and will only experience contact bounce in the "backward" direction."""
    _interval_ms: int
    _last_transition: int | None
    _bounce_timer: asyncio.Task | None
    _flag: asyncio.ThreadSafeFlag
    _stopped: bool

    def __init__(self, current_state, interval_ms: int):
        # The state actually reported to the user
        self._current_state = current_state
        # The previous state
        self._last_state = current_state
        # The minimum interval between making a state transition
        # and making its inverse transition. This should be greater
        # than they typical period of a switch bounce.
        self._interval_ms = interval_ms
        # The time of the last bounce (if any)
        self._last_transition = None
        # Waits to see if our last "bounce" actually took us to a settled state
        #
        # This also doubles as an indicator that we were bouncing.
        self._bounce_timer = None
        # Signals when a state change happens
        self._flag = asyncio.ThreadSafeFlag()
        # Signals when we have shut the debouncer down and will send no more events
        self._stopped = False

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        if self._bounce_timer != None:
            self._bounce_timer.cancel()

    def state(self):
        """Returns the current input state"""
        return self._current_state

    async def wait_for_state_change(self) -> None:
        """Waits for the debounced state to change"""
        if self._stopped:
            raise asyncio.CancelledError()
        await self._flag.wait()
        if self._stopped:
            raise asyncio.CancelledError()

    def record_state(self, observed_state) -> None:
        """Takes a new observed input state and, if appropriate, transitions to it"""
        when_ms = ticks_ms()
        if observed_state == self._current_state:
            # If we weren't bouncing, the caller has just given us a redundant state update, which we should ignore.
            # If we _were_ bouncing, we've just bounced back to _current_state and should reset the bounce timer.
            if self._bounce_timer != None:
                self._bounce_timer.cancel()
                self._last_transition = when_ms
            return
        if observed_state == self._last_state and self._last_transition != None and ticks_diff(when_ms, self._last_transition) < self._interval_ms:
            # We're returning to the previous state only a short time after the last state transition.
            # This could be a bounce, so give it time to settle before we accept the new state.
            self._last_transition = when_ms
            # Since we don't expect the raw input state to transition at the time we settle, we can't rely
            # on a state transition event to inform us that we need to update the current state. We'll need
            # a timer to do that.
            if self._bounce_timer != None:
                self._bounce_timer.cancel()
            self._bounce_timer = asyncio.create_task(self._wait_for_settle())
        else:
            # Either we're in a state that looks "settled", or (for cases where there are more
            # than two states available) we've moved all the way through to a new state in a
            # way that's not a bounce back to the previous state.
            self._last_state = self.state
            self._current_state = observed_state
            if self._bounce_timer != None:
                self._bounce_timer.cancel()
                self._bounce_timer = None
            self._flag.set()
        self._last_transition = when_ms

    async def _wait_for_settle(self) -> None:
        """Waits for the state to settle after a bounce returns us to _last_state.
        If we stay there long enough, we treat it as a state transition."""
        try:
            await asyncio.sleep_ms(self._interval_ms)
        except asyncio.CancelledError:
            return
        # The period has elapsed, and we haven't observed
        # a new state transition. Lock the state in.
        if self._last_transition != None:
            self._last_transition = ticks_ms()
            self._bounce_timer = None
            curr = self._current_state
            self._current_state = self._last_state
            self._last_state = curr
            self._flag.set()
