import logging

logger = logging.getLogger("CLI")

def execute_cmd_peers(peer_table, local_namespace=None):
    print("[CLI] Peers descobertos:")
    peers = peer_table.get_all_peers()
    if not peers:
        print("  Nenhum peer encontrado.")
        return

    for peer_id, data in peers.items():
        # Filtra pelo namespace local caso tenha sido invocado sem parâmetros
        ns = data.get('namespace', '')
        if local_namespace and ns != local_namespace:
            continue
        print(f"  {peer_id} | {data['ip']}:{data['port']} | Estado: {data.get('state', 'DISCOVERED')}")

def execute_cmd_conn(active_connections):
    print("[CLI] Conexões ativas:")
    if not active_connections:
        print("  Nenhuma conexão ativa.")
        return
        
    for peer_id, conn in active_connections.items():
        rtt_medio = conn.stats.get_avg_rtt()
        print(f"  {peer_id} | Dir: {conn.direction} | RTT: {rtt_medio:.1f} ms")

def execute_cmd_rtt(active_connections):
    print("[CLI] RTT médio por peer:")
    if not active_connections:
        print("  Nenhuma conexão ativa para medir RTT.")
        return
        
    for peer_id, conn in active_connections.items():
        print(f"  {peer_id}: {conn.stats.get_avg_rtt():.1f} ms")