"""SPLIT THE WIRES (STW-1.0) + COLD-COPY SURVIVAL (CCS-1.0)."""

from azmail.mesh import (
    CCS_SPEC,
    COLD_COPY_MIN,
    DWELL_SEC,
    MESH_HOP_DEFAULT_OFF,
    SOCKET_DWELL,
    SOCKET_TICK,
    STW_SPEC,
    TIP_TICK_BYTES,
    admit_payload,
    cold_copy_survival,
    creator_gone,
    decide_update,
    emit_last,
    encode_tip_tick,
    erase_tip,
    equivocation_ends_peer,
    heartbeat_loss,
    hop_enable,
    hop_status,
    live_body_sync,
    MeshClient,
    multiply_cold_copies,
    partition_heal,
    phoenix,
    poison_refuse,
    server_pull,
    sockets_are_split,
    split_the_wires,
    tick_interval_ok,
)

TIP = "ab" * 32
TIP_B = "cd" * 32


def test_split_the_wires_cite_and_hop_off():
    law = split_the_wires()
    assert law["spec"] == STW_SPEC == "STW-1.0"
    assert law["title"] == "SPLIT THE WIRES"
    assert law["author"] == "Aziel Eliab"
    assert law["hop_default"] is False
    assert MESH_HOP_DEFAULT_OFF is True
    assert hop_status()["enabled"] is False
    hop = hop_enable()
    assert hop["ok"] is False
    assert hop["enabled"] is False
    assert hop["code"] == "STW_HOP_DEFAULT_OFF"
    status = MeshClient().status()
    assert status["enabled"] is False
    assert status["split_the_wires"]["spec"] == "STW-1.0"
    assert status["cold_copy_survival"]["spec"] == "CCS-1.0"
    assert status["hop"]["enabled"] is False


def test_tip_only_fixed_size_tick():
    ok = encode_tip_tick("live", TIP)
    assert ok["ok"] is True
    assert ok["bytes"] == TIP_TICK_BYTES
    assert ok["payload"] is None
    assert ok["wire"].startswith("L")
    assert tick_interval_ok(0.5) and tick_interval_ok(1.0)
    assert not tick_interval_ok(0.4)
    assert not tick_interval_ok(1.1)
    refused = encode_tip_tick("live", TIP, payload="body")
    assert refused["ok"] is False
    assert refused["code"] == "STW_TIP_ONLY"


def test_pull_only_and_split_sockets():
    assert admit_payload(direction="pull")["ok"] is True
    push = admit_payload(direction="push")
    assert push["ok"] is False
    assert push["code"] == "STW_PULL_ONLY"
    mixed = admit_payload(direction="pull", socket=SOCKET_TICK)
    assert mixed["code"] == "STW_SOCKET_SPLIT"
    hop = admit_payload(direction="pull", hop_enabled=True)
    assert hop["code"] == "STW_HOP_DEFAULT_OFF"
    assert sockets_are_split(SOCKET_TICK, SOCKET_DWELL)["ok"] is True
    assert sockets_are_split(SOCKET_TICK, SOCKET_TICK)["ok"] is False


def test_update_is_proof_not_timer():
    timer = decide_update({"kind": "timer"})
    assert timer["apply"] is False
    assert timer["code"] == "STW_UPDATE_NOT_TIMER"
    missing = decide_update({"kind": "cite", "prev": TIP})
    assert missing["fail_closed"] is True
    assert missing["code"] == "STW_CITE_FAIL_CLOSED"
    desync = decide_update({"kind": "clock_desync"})
    assert desync["yes"] is False
    assert desync["apply"] is False
    amb = decide_update({"kind": "ambiguous"})
    assert amb["isolate"] is True
    cited = decide_update({"prev": TIP, "lockset": "LOCKSET-1"})
    assert cited["ok"] is True
    assert cited["apply"] is True
    assert cited["dwell_sec"] == DWELL_SEC == 777


def test_equivocation_emit_phoenix_partition_heartbeat():
    ended = equivocation_ends_peer("peer-a", [TIP, TIP_B])
    assert ended["ended"] is True
    assert ended["apply"] is False
    assert emit_last(scope="local")["relay"] is False
    assert emit_last(scope="public")["ok"] is False
    assert phoenix(scope="local")["public_restore"] is False
    assert phoenix(scope="public")["code"] == "STW_PHOENIX_LOCAL_ONLY"
    assert partition_heal(auto_splice=True)["splice"] is False
    hb = heartbeat_loss()
    assert hb["poison"] is False
    assert hb["apply_last_packet"] is False


def test_cold_copy_survival_multiply_and_refuses():
    law = cold_copy_survival()
    assert law["spec"] == CCS_SPEC == "CCS-1.0"
    assert law["title"] == "COLD-COPY SURVIVAL"
    assert law["keeps_split_the_wires"] is True
    assert law["min_copies"] == COLD_COPY_MIN == 2
    one = multiply_cold_copies([{"hash": TIP, "cold": True}])
    assert one["ok"] is False
    assert one["code"] == "CCS_MULTIPLY"
    two = multiply_cold_copies([{"hash": TIP, "cold": True}, {"hash": TIP_B, "cold": True}])
    assert two["ok"] is True
    assert two["copies"] >= 2
    live = multiply_cold_copies([{"hash": TIP, "live": True}, {"hash": TIP_B, "cold": True}])
    assert live["code"] == "CCS_LIVE_BODY_SYNC_REFUSED"
    sync = live_body_sync()
    assert sync["ok"] is False
    assert sync["synced"] is False


def test_tip_expensive_server_pull_poison_outlives_creators():
    cheap = erase_tip()
    assert cheap["erased"] is False
    assert cheap["code"] == "CCS_TIP_ERASE_EXPENSIVE"
    assert erase_tip(expensive=True)["erased"] is False
    copies = [{"hash": TIP, "cold": True}, {"hash": TIP_B, "cold": True}]
    wipe = server_pull(wipe_cold=True, replicas=copies)
    assert wipe["ok"] is False
    assert wipe["wiped"] is False
    assert wipe["copies"] == 2
    assert wipe["code"] == "CCS_SERVER_PULL_NO_WIPE"
    poison = poison_refuse(TIP, [TIP])
    assert poison["ok"] is False
    assert poison["interpret"] is False
    assert poison["code"] == "CCS_POISON_HASH_ABSOLUTE"
    clean = poison_refuse(TIP_B, [TIP])
    assert clean["poison"] is False
    gone = creator_gone("anon-dead", copies)
    assert gone["wiped"] is False
    assert gone["data_remains"] is True
    assert gone["copies"] == 2
    assert gone["code"] == "CCS_DATA_OUTLIVES_CREATORS"
