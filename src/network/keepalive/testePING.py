import time

from src.network.keepalive.keepAlive import PeerStats

peer = PeerStats(ping_miss_limit=3)

# Criar PING
ping = peer.create_ping()
print("PING:", ping)

# Simular resposta
pong = peer.create_pong(ping["msg_id"], ping["timestamp"])

# Processar resposta
resultado = peer.process_pong(pong["msg_id"], pong["timestamp"])

print("PONG aceito:", resultado)
print("RTT médio:", peer.get_avg_rtt())
print("Missed PINGs:", peer.missed_pings)

assert resultado is True
assert peer.missed_pings == 0
assert peer.is_stale is False

# Simular três PINGs sem resposta
for _ in range(3):
    peer.create_ping()

time.sleep(0.02)
peer.check_timeouts(timeout_seconds=0.01)

assert peer.is_stale is True

print("TESTE KEEPALIVE PASSOU!")
