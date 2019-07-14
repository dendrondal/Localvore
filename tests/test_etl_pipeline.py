import pytest
from src import ETL_pipeline
import pandas as pd
from hypothesis.extra.pandas import column, data_frames
from hypothesis import strategies as st
from hypothesis import given
from hypothesis import assume
import string


@st.composite
def same_len_lists(draw):
    n = draw(st.integers(min_value=3, max_value=12))
    ingrs = st.lists(st.dictionaries(keys=st.just('text'),
                                    values=st.text(min_size=3, max_size=12,
                                    alphabet=string.ascii_lowercase),
                                    min_size=1, max_size=1),
                     min_size=n, max_size=n)
    valid = st.lists(st.booleans(), min_size=n, max_size=n)
    return draw(ingrs), draw(valid)


@given(same_len_lists())
def test_compression(lists):
    true_vals = list(filter(lambda val: val is True, lists[1]))
    assert len(ETL_pipeline._compression(*lists)) == len(true_vals)


@given(
    data_frames(
        columns=[
            column(
                name='_id',
                elements=st.text(min_size=10, max_size=10,
                                 alphabet=string.ascii_lowercase)
            ),
            column(
                name='raw_ingrs',
                elements=st.lists(
                    st.dictionaries(keys=st.just('text'),
                                    values=st.text(min_size=3, max_size=12,
                                    alphabet=string.ascii_lowercase),
                                    min_size=1, max_size=1),
                    min_size=5, max_size=5),
            ),
            column(
                name='valid',
                elements=st.lists(st.booleans(), min_size=5, max_size=5)
            ),
        ]
    )
)
def test_filter_predictions(mock_df):
    assume(len(mock_df.columns) == 3)
    assume(len(mock_df) != 0)
    df = ETL_pipeline.filter_predictions(mock_df)
    assert df is not None