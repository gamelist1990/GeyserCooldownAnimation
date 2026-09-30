package com.pexserver.cooldown;

import java.util.UUID;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AnimationReplayGateTest {
    private final AnimationReplayGate gate = new AnimationReplayGate();
    private final UUID player = UUID.randomUUID();

    private boolean click(int ticks, long sequence, long millis) {
        return gate.accept(player, ticks, sequence, TimeUnit.MILLISECONDS.toNanos(millis));
    }

    @Test void rapidClicksDoNotRestartOrExtendSwordRecovery() {
        assertTrue(click(13, 0, 0));
        for (int time = 50; time < 650; time += 50) {
            assertFalse(click(13, time, time));
        }
        assertTrue(click(13, 650, 650));
    }

    @Test void axeWaitsForVisualRecoveryBeyondServerCooldown() {
        assertTrue(click(20, 1, 0));
        assertFalse(click(20, 2, 1000));
        assertTrue(click(20, 3, 1050));
    }

    @Test void weaponChangeCannotInterruptPreviousRecovery() {
        assertTrue(click(34, 1, 0));
        assertFalse(click(5, 2, 250));
        assertTrue(click(5, 3, 1700));
    }

    @Test void duplicateSequenceIsRejectedAfterRecovery() {
        assertTrue(click(13, 1, 0));
        assertFalse(click(13, 1, 1000));
        assertTrue(click(13, 2, 1000));
    }

    @Test void playersAreIndependentAndDisconnectResetsGate() {
        assertTrue(click(13, 1, 0));
        assertTrue(gate.accept(UUID.randomUUID(), 13, 1, 0));
        gate.remove(player);
        assertTrue(click(13, 1, 50));
        gate.clear();
        assertTrue(click(13, 1, 100));
    }
}
