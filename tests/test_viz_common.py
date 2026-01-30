import pytest


def test_viz_common_ensure_helpers_and_as_plotly_dict():
    from smrforge.visualization._viz_common import (
        as_plotly_dict,
        ensure_matplotlib_available,
        ensure_plotly_available,
    )

    ensure_plotly_available(True)
    ensure_matplotlib_available(True)

    with pytest.raises(ImportError):
        ensure_plotly_available(False)

    with pytest.raises(ImportError):
        ensure_matplotlib_available(False)

    assert as_plotly_dict(None, title="t") == {"data": [], "layout": {"title": "t"}}

    d = {"data": [1], "layout": {}}
    out = as_plotly_dict(d, title="x")
    assert out["layout"]["title"] == "x"

    class HasToDict:
        def to_dict(self):
            return {"data": [], "layout": {}}

    out2 = as_plotly_dict(HasToDict(), title="y")
    assert out2["layout"]["title"] == "y"

    class NoToDict:
        pass

    out3 = as_plotly_dict(NoToDict(), title=None)
    assert out3["layout"]["title"] == "Unsupported figure type"

