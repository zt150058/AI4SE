from cart import total

def test_cart():
    assert total([1, 2, 6]) == 9  # fails: returns 10
