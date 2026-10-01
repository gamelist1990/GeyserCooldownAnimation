package com.pexserver.cooldown;

import io.netty.buffer.Unpooled;
import org.cloudburstmc.protocol.bedrock.codec.BedrockCodec;
import org.cloudburstmc.protocol.bedrock.codec.v729.Bedrock_v729;
import org.cloudburstmc.protocol.bedrock.codec.v748.Bedrock_v748;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AnimationPacketFactoryTest {
    @Test void supportedCodecsRoundTripEveryTimingSignal() {
        for (BedrockCodec codec : new BedrockCodec[] {Bedrock_v729.CODEC, Bedrock_v748.CODEC}) {
            var helper = codec.createHelper();
            for (int ticks = 1; ticks <= 200; ticks++) {
                String animation = AnimationSelector.select(ticks);
                long id = 0x1_0000_0000L + ticks;
                var packet = AnimationPacketFactory.create(codec, helper, animation, id);
                assertEquals(animation, packet.getAnimation());
                assertEquals("geyser_cooldown_timing", packet.getController());
                assertEquals("query.any_animation_finished", packet.getStopExpression());
                assertEquals(0, packet.getStopExpressionVersion());
                assertEquals(0f, packet.getBlendOutTime());
                assertEquals(1, packet.getRuntimeEntityIds().size());
                assertEquals(id, packet.getRuntimeEntityIds().getLong(0));
                var bytes = Unpooled.buffer();
                try {
                    codec.tryEncode(helper, bytes, packet);
                    var copy = codec.tryDecode(helper, bytes,
                            codec.getPacketDefinition(packet.getClass()).getId());
                    assertEquals(packet, copy);
                    assertFalse(bytes.isReadable());
                } finally { bytes.release(); }
            }
        }
    }
}
