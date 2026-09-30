package com.pexserver.cooldown;

/** Uses the exact server cooldown, in 50 ms ticks, without profile rounding. */
public final class AnimationSelector {
    private AnimationSelector() {}

    private static void validate(int ticks) {
        if (ticks < 1 || ticks > 200) throw new IllegalArgumentException("Invalid cooldown");
    }

    public static String select(int ticks) {
        validate(ticks);
        return "animation.player.cooldown_tick_" + ticks;
    }

    public static int replayDelayMillis(int ticks) {
        validate(ticks);
        return ticks * 50;
    }
}
