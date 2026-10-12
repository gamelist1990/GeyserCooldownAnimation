package com.pexserver.cooldown;

/** Encodes server cooldowns in 20 ms steps, without fixed item profiles. */
public final class AnimationSelector {
    public static final int STEP_MILLIS = 20;
    public static final int MAX_STEPS = 10_000 / STEP_MILLIS;
    private AnimationSelector() {}

    private static void validate(int ticks) {
        if (ticks < 1 || ticks > MAX_STEPS) throw new IllegalArgumentException("Invalid cooldown");
    }

    public static String select(int ticks) {
        validate(ticks);
        return "animation.player.cooldown_20ms_" + ticks;
    }

    public static int replayDelayMillis(int ticks) {
        validate(ticks);
        return ticks * STEP_MILLIS;
    }
}
