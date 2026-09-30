package com.pexserver.cooldown;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/** Deduplicates timing signals; local Bedrock controllers own visible playback. */
final class AnimationReplayGate {
    private record Stamp(long sequence, long startedAt, long duration) {}
    private final Map<UUID, Stamp> stamps = new HashMap<>();

    synchronized boolean accept(UUID uuid, int ticks, long sequence, long now) {
        long duration = TimeUnit.MILLISECONDS.toNanos(45);
        Stamp previous = stamps.get(uuid);
        if (previous != null && (previous.sequence() == sequence
                || now - previous.startedAt() < previous.duration())) {
            return false;
        }
        stamps.put(uuid, new Stamp(sequence, now, duration));
        return true;
    }

    synchronized void remove(UUID uuid) {
        stamps.remove(uuid);
    }

    synchronized void clear() {
        stamps.clear();
    }
}
