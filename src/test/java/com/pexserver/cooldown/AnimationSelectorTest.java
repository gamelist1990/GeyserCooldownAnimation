package com.pexserver.cooldown;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AnimationSelectorTest {
    private static String forAttackSpeed(double speed) {
        return AnimationSelector.select((int) Math.ceil(20.0 / speed));
    }

    @Test void standardJavaWeaponsSelectTheirOwnProfiles() {
        assertEquals("animation.geyser_cooldown.hand", forAttackSpeed(4.0));
        assertEquals("animation.geyser_cooldown.sword", forAttackSpeed(1.6));
        assertEquals("animation.geyser_cooldown.pickaxe", forAttackSpeed(1.2));
        assertEquals("animation.geyser_cooldown.diamond_axe", forAttackSpeed(1.0));
        assertEquals("animation.geyser_cooldown.iron_axe", forAttackSpeed(0.9));
        assertEquals("animation.geyser_cooldown.stone_axe", forAttackSpeed(0.8));
        assertEquals("animation.geyser_cooldown.mace", forAttackSpeed(0.6));
    }

    @Test void invalidProtocolCooldownsAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> AnimationSelector.select(0));
        assertThrows(IllegalArgumentException.class, () -> AnimationSelector.select(201));
    }
}
