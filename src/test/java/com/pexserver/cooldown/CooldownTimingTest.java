package com.pexserver.cooldown;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CooldownTimingTest {
    @Test void roundsRemainingTimeUpWithLessThan20MillisError() {
        for (int elapsed = 0; elapsed < 1000; elapsed++) {
            int steps = new CooldownTiming(0).update(1000, 1.0, 50, 1000 + elapsed, true);
            int displayedMillis = AnimationSelector.replayDelayMillis(steps);
            int remainingMillis = 1000 - elapsed;
            assertTrue(displayedMillis >= remainingMillis);
            assertTrue(displayedMillis - remainingMillis < 20);
        }
        assertEquals(1, new CooldownTiming(0).update(1000, 1.0, 50, 1980, true));
        assertEquals(2, new CooldownTiming(0).update(1000, 1.0, 50, 1979, true));
        assertEquals(0, new CooldownTiming(0).update(1000, 1.0, 50, 2000, true));
    }

    @Test void usesServerAttackSpeedRatherThanFixedResourcePackDurations() {
        // Representative effective speeds: hand, sword, pickaxe, shovel,
        // trident, mace and slower weapons. The item name never chooses timing.
        double[] speeds = {4.0, 1.6, 1.2, 1.0, 1.1, 0.6, 0.8};
        int[] ticks = {13, 32, 42, 50, 46, 84, 63};
        for (int i = 0; i < speeds.length; i++) {
            assertEquals(ticks[i], new CooldownTiming(0).update(1000, speeds[i], 50, 1000, true));
            assertEquals((int) Math.ceil(100.0 / speeds[i]),
                    new CooldownTiming(0).update(1000, speeds[i], 100, 1000, true));
        }
    }

    @Test void observesNewAttacksAndRepeatedClicksWithoutReplayingProgressUpdates() {
        var timing = new CooldownTiming(1000);
        assertEquals(0, timing.update(1000, 1.6, 50, 1010, true));
        assertEquals(31, timing.update(1100, 1.6, 50, 1110, true));
        assertEquals(0, timing.update(1100, 1.6, 50, 1150, true));
        assertEquals(31, timing.update(1150, 1.6, 50, 1160, true));
    }

    @Test void subtractsObservationDelayAndMatchesGeyserTickRateScaling() {
        assertEquals(29, new CooldownTiming(0).update(1000, 1.6, 50, 1050, true));
        assertEquals(62, new CooldownTiming(0).update(1000, 1.6, 100, 1010, true));
        assertEquals(31, new CooldownTiming(0).update(1000, 1.6, 25, 1010, true));
        assertEquals(0, new CooldownTiming(0).update(1000, 4, 50, 1250, true));
        assertEquals(500, new CooldownTiming(0).update(1000, 0.01, 50, 1010, true));
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
        assertEquals(12, timing.update(1050, 4, 50, 1060, true));
    }
}
