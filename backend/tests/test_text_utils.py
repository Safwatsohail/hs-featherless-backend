from backend.app.utils.text import stable_hash_embedding


def test_stable_hash_embedding_is_deterministic() -> None:
    a = stable_hash_embedding("hello", dims=64)
    b = stable_hash_embedding("hello", dims=64)
    c = stable_hash_embedding("world", dims=64)
    assert a == b
    assert a != c
    assert len(a) == 64

