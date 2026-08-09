def test_package_importable():
    import coding_harness

    assert coding_harness.__version__ == "0.1.0"
