package com.pexserver.cooldown;

/** Converts a new Geyser cooldown start into remaining wall-clock animation ticks. */
final class CooldownTiming {
    private long lastHitTime;

    CooldownTiming(long initialHitTime) {
        lastHitTime = initialHitTime;
    }

    int update(long hitTime, double attackSpeed, double millisecondsPerTick, long now, boolean enabled) {
        if (hitTime == lastHitTime) return 0;
        lastHitTime = hitTime;
        if (!enabled || hitTime <= 0 || hitTime > now || !Double.isFinite(attackSpeed)
                || attackSpeed <= 0 || attackSpeed > 20 || !Double.isFinite(millisecondsPerTick)
                || millisecondsPerTick <= 0) return 0;
        // Matches CooldownUtils.tickCooldown, including slower server tick rates.
        double duration = 1000.0 * Math.max(millisecondsPerTick / 50.0, 1.0) / attackSpeed;
        double remaining = duration - (now - hitTime);
        if (remaining <= 0) return 0;
        return (int) Math.min(200, Math.ceil(remaining / 50.0));
    }
}
