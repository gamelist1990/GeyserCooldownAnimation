package com.pexserver.cooldown;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CooldownTimingTest {
    @Test void observesNewAttacksAndRepeatedClicksWithoutReplayingProgressUpdates() {
        var timing = new CooldownTiming(1000);
        assertEquals(0, timing.update(1000, 1.6, 50, 1010, true));
        assertEquals(13, timing.update(1100, 1.6, 50, 1110, true));
        assertEquals(0, timing.update(1100, 1.6, 50, 1150, true));
        assertEquals(13, timing.update(1150, 1.6, 50, 1160, true));
    }

    @Test void subtractsObservationDelayAndMatchesGeyserTickRateScaling() {
        assertEquals(12, new CooldownTiming(0).update(1000, 1.6, 50, 1050, true));
        assertEquals(25, new CooldownTiming(0).update(1000, 1.6, 100, 1010, true));
        assertEquals(13, new CooldownTiming(0).update(1000, 1.6, 25, 1010, true));
        assertEquals(0, new CooldownTiming(0).update(1000, 4, 50, 1250, true));
        assertEquals(200, new CooldownTiming(0).update(1000, 0.01, 50, 1010, true));
    }

    @Test void rejectsInvalidAndDisabledStatesAndDoesNotReplayOnReenable() {
        for (double speed : new double[]{0, -1, 21, Double.NaN, Double.POSITIVE_INFINITY}) {
            assertEquals(0, new CooldownTiming(0).update(1000, speed, 50, 1010, true));
        }
        assertEquals(0, new CooldownTiming(0).update(1100, 4, 50, 1000, true));
        assertEquals(0, new CooldownTiming(1).update(0, 4, 50, 1000, true));
        assertEquals(0, new CooldownTiming(0).update(1000, 4, Double.NaN, 1010, true));
        var timing = new CooldownTiming(0);
        assertEquals(0, timing.update(1000, 4, 50, 1010, false));
        assertEquals(0, timing.update(1000, 4, 50, 1020, true));
        assertEquals(5, timing.update(1050, 4, 50, 1060, true));
    }
}
