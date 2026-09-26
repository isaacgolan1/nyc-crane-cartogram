from src.download import build_curl_command, chunks, in_clause


def test_build_curl_command_encodes_each_param():
    cmd = build_curl_command(
        "https://example.org/resource/abcd-1234.csv",
        {"$where": "boroughname='MANHATTAN'", "$limit": "10"},
    )

    assert cmd[0] == "curl"
    assert "--fail" in cmd
    assert "--get" in cmd
    assert cmd[cmd.index("--retry") + 1] == "3"
    assert "https://example.org/resource/abcd-1234.csv" in cmd
    assert "$where=boroughname='MANHATTAN'" in cmd
    assert "$limit=10" in cmd


def test_chunks_splits_and_keeps_remainder():
    assert chunks(["a", "b", "c", "d", "e"], 2) == [["a", "b"], ["c", "d"], ["e"]]


def test_chunks_empty():
    assert chunks([], 100) == []


def test_in_clause_quotes_values():
    assert in_clause("permitnumber", ["M1", "B2"]) == "permitnumber in('M1','B2')"


def test_in_clause_escapes_single_quotes():
    assert in_clause("name", ["O'NEIL"]) == "name in('O''NEIL')"
