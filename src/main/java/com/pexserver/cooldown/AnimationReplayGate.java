package com.pexserver.cooldown;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Deduplicates timing signals; local Bedrock controllers own visible playback. */
final class AnimationReplayGate {
    private final Map<UUID, Long> sequences = new HashMap<>();

    synchronized boolean accept(UUID uuid, long sequence) {
        Long previous = sequences.get(uuid);
        if (previous != null && previous == sequence) return false;
        sequences.put(uuid, sequence);
        return true;
    }

    synchronized void remove(UUID uuid) {
        sequences.remove(uuid);
    }

    synchronized void clear() {
        sequences.clear();
    }
}
