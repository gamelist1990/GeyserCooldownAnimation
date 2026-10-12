package com.pexserver.cooldown;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AnimationSelectorTest {
    @Test void everyProtocolDurationIsSelectedWithoutRounding() {
        for (int ticks = 1; ticks <= 500; ticks++) {
            assertEquals("animation.player.cooldown_20ms_" + ticks, AnimationSelector.select(ticks));
            assertEquals(ticks * 20, AnimationSelector.replayDelayMillis(ticks));
        }
    }

    @Test void invalidProtocolCooldownsAreRejected() {
        for (int ticks : new int[] {Integer.MIN_VALUE, 0, 501, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> AnimationSelector.select(ticks));
            assertThrows(IllegalArgumentException.class, () -> AnimationSelector.replayDelayMillis(ticks));
        }
    }
}
