package com.pexserver.cooldown;

/** Selects the closest standard Java attack-speed profile. */
public final class AnimationSelector {
    private static final int[] REFERENCE_TICKS = {5, 13, 17, 20, 23, 25, 34};
    private static final String[] PROFILES = {
            "hand", "sword", "pickaxe", "diamond_axe", "iron_axe", "stone_axe", "mace"
    };

    private AnimationSelector() {}

    public static String select(int ticks) {
        if (ticks < 1 || ticks > 200) throw new IllegalArgumentException("Invalid cooldown");
        int closest = 0;
        for (int index = 1; index < REFERENCE_TICKS.length; index++) {
            if (Math.abs(ticks - REFERENCE_TICKS[index]) < Math.abs(ticks - REFERENCE_TICKS[closest])) {
                closest = index;
            }
        }
        return "animation.geyser_cooldown." + PROFILES[closest];
    }
}
