from secure_line.netutils import valid_channel_name, valid_name


def test_valid_name_accepts_ascii_callsigns():
    assert valid_name("Alice-2_test.name")


def test_valid_name_rejects_non_ascii_alphanumeric_characters():
    assert not valid_name("Émile")
    assert not valid_name("李雷")


def test_valid_channel_name_uses_ascii_callsign_rules():
    assert valid_channel_name("#general-2")
    assert not valid_channel_name("#café")