package com.pexserver.cooldown;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AnimationSelectorTest {
    private static String forAttackSpeed(double speed) {
        return AnimationSelector.select((int) Math.ceil(20.0 / speed));
    }

    @Test void standardJavaWeaponsSelectTheirOwnProfiles() {
        assertEquals("animation.player.hand", forAttackSpeed(4.0));
        assertEquals("animation.player.sword", forAttackSpeed(1.6));
        assertEquals("animation.player.pickaxe", forAttackSpeed(1.2));
        assertEquals("animation.player.diamond_axe", forAttackSpeed(1.0));
        assertEquals("animation.player.iron_axe", forAttackSpeed(0.9));
        assertEquals("animation.player.stone_axe", forAttackSpeed(0.8));
        assertEquals("animation.player.mace", forAttackSpeed(0.6));
    }

    @Test void invalidProtocolCooldownsAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> AnimationSelector.select(0));
        assertThrows(IllegalArgumentException.class, () -> AnimationSelector.select(201));
    }
}
