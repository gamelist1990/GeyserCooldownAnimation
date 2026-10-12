package com.pexserver.cooldown;

import java.util.UUID;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AnimationReplayGateTest {
    private final AnimationReplayGate gate = new AnimationReplayGate();
    private final UUID player = UUID.randomUUID();

    private boolean click(long sequence) {
        return gate.accept(player, sequence);
    }

    @Test void everyServerTickCanUpdateTimingWithoutReplayingArmAnimation() {
        assertTrue(click(0));
        for (int time = 50; time <= 650; time += 50) {
            assertTrue(click(time));
        }
    }

    @Test void distinctSignalsAreAcceptedEvenWithin45Millis() {
        for (long sequence = 1000; sequence <= 1050; sequence++) {
            assertTrue(click(sequence));
            assertFalse(click(sequence));
        }
    }

    @Test void duplicateSequenceIsRejectedAfterRecovery() {
        assertTrue(click(1));
        assertFalse(click(1));
        assertTrue(click(2));
    }

    @Test void playersAreIndependentAndDisconnectResetsGate() {
        assertTrue(click(1));
        assertTrue(gate.accept(UUID.randomUUID(), 1));
        gate.remove(player);
        assertTrue(click(1));
        gate.clear();
        assertTrue(click(1));
    }
}
