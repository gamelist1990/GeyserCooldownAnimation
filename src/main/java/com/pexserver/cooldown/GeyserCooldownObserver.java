package com.pexserver.cooldown;

import org.geysermc.geyser.api.connection.GeyserConnection;
import org.geysermc.geyser.session.GeyserSession;
import org.geysermc.geyser.util.CooldownUtils.CooldownType;
import org.geysermc.mcprotocollib.protocol.data.game.entity.player.GameMode;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

/** Observes the same session state that drives Geyser's built-in cooldown UI. */
final class GeyserCooldownObserver {
    private final Map<GeyserConnection, Registration> registrations = new HashMap<>();

    synchronized void attach(GeyserConnection connection, BiConsumer<Integer, Long> receive,
                             Consumer<String> diagnostic) {
        if (registrations.containsKey(connection)) return;
        if (!(connection instanceof GeyserSession session)) {
            throw new IllegalStateException("Unsupported Geyser connection type: " + connection.getClass().getName());
        }
        Registration registration = new Registration(session, receive, diagnostic);
        registrations.put(connection, registration);
        try {
            session.executeInEventLoop(registration::start);
        } catch (RuntimeException | LinkageError error) {
            registrations.remove(connection);
            registration.stop();
            throw error;
        }
    }

    synchronized void detach(GeyserConnection connection) {
        Registration registration = registrations.remove(connection);
        if (registration != null) registration.stop();
    }

    synchronized void close() {
        registrations.values().forEach(Registration::stop);
        registrations.clear();
    }

    private static final class Registration {
        private final GeyserSession session;
        private final BiConsumer<Integer, Long> receive;
        private final Consumer<String> diagnostic;
        private CooldownTiming timing;
        private boolean active = true;
        private ScheduledFuture<?> future;

        Registration(GeyserSession session, BiConsumer<Integer, Long> receive, Consumer<String> diagnostic) {
            this.session = session;
            this.receive = receive;
            this.diagnostic = diagnostic;
        }

        synchronized void start() {
            if (!active) return;
            try {
                // Do not replay an old cooldown when attaching to an existing connection.
                timing = new CooldownTiming(session.getLastHitTime());
                diagnostic.accept("Attached Geyser cooldown observer for " + session.javaUuid() + ".");
                poll();
            } catch (RuntimeException | LinkageError error) {
                fail(error);
            }
        }

        synchronized void poll() {
            if (!active) return;
            try {
                if (session.isClosed()) {
                    stop();
                    return;
                }
                long hit = session.getLastHitTime();
                boolean enabled = session.isSpawned() && session.getUpstream().isInitialized()
                        && session.getGameMode() != GameMode.SPECTATOR
                        && session.getPreferencesCache().getCooldownPreference() != CooldownType.DISABLED;
                int ticks = timing.update(hit, session.getAttackSpeed(), session.getMillisecondsPerTick(),
                        System.currentTimeMillis(), enabled);
                if (ticks > 0) receive.accept(ticks, hit);
                // Run on Geyser's event loop, so reading cooldown state cannot race translators.
                future = session.scheduleInEventLoop(this::poll, 10, TimeUnit.MILLISECONDS);
            } catch (RuntimeException | LinkageError error) {
                fail(error);
            }
        }

        private void fail(Throwable error) {
            stop();
            diagnostic.accept("Geyser cooldown observer stopped: " + error.getClass().getSimpleName()
                    + ": " + error.getMessage());
        }

        synchronized void stop() {
            active = false;
            if (future != null) future.cancel(false);
        }
    }
}
