package com.pexserver.cooldown;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AnimationSelectorTest {
    @Test void everyProtocolDurationIsSelectedWithoutRounding() {
        for (int ticks = 1; ticks <= 200; ticks++) {
            assertEquals("animation.player.cooldown_tick_" + ticks, AnimationSelector.select(ticks));
            assertEquals(ticks * 50, AnimationSelector.replayDelayMillis(ticks));
        }
    }

    @Test void invalidProtocolCooldownsAreRejected() {
        for (int ticks : new int[] {Integer.MIN_VALUE, 0, 201, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> AnimationSelector.select(ticks));
            assertThrows(IllegalArgumentException.class, () -> AnimationSelector.replayDelayMillis(ticks));
        }
    }
}
