from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import polars as pl
import pytest

from kreuzberg._gmft import (
    _dataframe_to_csv,
    _dataframe_to_markdown,
    _is_dataframe_empty,
    _pandas_to_polars,
    extract_tables,
    extract_tables_sync,
)
from kreuzberg._types import GMFTConfig, TableData
from kreuzberg.exceptions import MissingDependencyError


def test_pandas_to_polars_with_none() -> None:
    result = _pandas_to_polars(None)
    assert isinstance(result, pl.DataFrame)
    assert result.is_empty()


def test_pandas_to_polars_with_valid_dataframe() -> None:
    mock_pandas_df = Mock()
    mock_polars_df = Mock(spec=pl.DataFrame)

    with patch("polars.from_pandas", return_value=mock_polars_df) as mock_from_pandas:
        result = _pandas_to_polars(mock_pandas_df)

    assert result == mock_polars_df
    mock_from_pandas.assert_called_once_with(mock_pandas_df)


def test_pandas_to_polars_with_conversion_error_and_duplicate_columns() -> None:
    mock_pandas_df = Mock()
    mock_pandas_df.columns = Mock()
    mock_pandas_df.columns.duplicated.return_value = np.array([False, True, False])

    mock_filtered_df = Mock()
    mock_pandas_df.loc = Mock()
    mock_pandas_df.loc.__getitem__ = Mock(return_value=mock_filtered_df)

    mock_polars_df = Mock(spec=pl.DataFrame)

    with patch("polars.from_pandas") as mock_from_pandas:
        mock_from_pandas.side_effect = [ValueError("Duplicate columns"), mock_polars_df]

        result = _pandas_to_polars(mock_pandas_df)

    assert result == mock_polars_df
    assert mock_from_pandas.call_count == 2
    mock_pandas_df.columns.duplicated.assert_called_once()


def test_pandas_to_polars_with_conversion_error_no_columns_attr() -> None:
    mock_pandas_df = Mock()
    del mock_pandas_df.columns

    with patch("polars.from_pandas", side_effect=TypeError("Conversion failed")):
        result = _pandas_to_polars(mock_pandas_df)

    assert isinstance(result, pl.DataFrame)
    assert result.is_empty()


def test_pandas_to_polars_with_attribute_error() -> None:
    mock_pandas_df = Mock()
    del mock_pandas_df.columns

    with patch("polars.from_pandas", side_effect=AttributeError("Missing attribute")):
        result = _pandas_to_polars(mock_pandas_df)

    assert isinstance(result, pl.DataFrame)
    assert result.is_empty()


def test_dataframe_to_markdown_with_none() -> None:
    result = _dataframe_to_markdown(None)
    assert result == ""


def test_dataframe_to_markdown_with_empty_polars_dataframe() -> None:
    empty_df = pl.DataFrame()
    result = _dataframe_to_markdown(empty_df)
    assert result == ""


def test_dataframe_to_markdown_with_polars_dataframe() -> None:
    df = pl.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    result = _dataframe_to_markdown(df)
    assert "col1" in result
    assert "col2" in result
    assert str(df) in result


def test_dataframe_to_markdown_with_pandas_dataframe() -> None:
    mock_df = Mock()
    mock_df.to_markdown.return_value = "| col1 | col2 |\n|------|------|\n| 1    | 2    |"

    result = _dataframe_to_markdown(mock_df)

    assert result == "| col1 | col2 |\n|------|------|\n| 1    | 2    |"
    mock_df.to_markdown.assert_called_once()


def test_dataframe_to_markdown_with_object_without_to_markdown() -> None:
    mock_df = Mock()
    del mock_df.to_markdown

    result = _dataframe_to_markdown(mock_df)

    assert result == str(mock_df)


def test_dataframe_to_csv_with_none() -> None:
    result = _dataframe_to_csv(None)
    assert result == ""


def test_dataframe_to_csv_with_empty_polars_dataframe() -> None:
    empty_df = pl.DataFrame()
    result = _dataframe_to_csv(empty_df)
    assert result == ""


def test_dataframe_to_csv_with_polars_dataframe() -> None:
    df = pl.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    result = _dataframe_to_csv(df)

    assert "col1,col2" in result
    assert "1,3" in result
    assert "2,4" in result


def test_dataframe_to_csv_with_pandas_dataframe() -> None:
    mock_df = Mock()
    mock_df.to_csv.return_value = "col1,col2\n1,2\n3,4\n"

    result = _dataframe_to_csv(mock_df)

    assert result == "col1,col2\n1,2\n3,4\n"
    mock_df.to_csv.assert_called_once_with(index=False)


def test_dataframe_to_csv_with_object_without_to_csv() -> None:
    mock_df = Mock()
    del mock_df.to_csv

    result = _dataframe_to_csv(mock_df)

    assert result == ""


def test_is_dataframe_empty_with_none() -> None:
    result = _is_dataframe_empty(None)
    assert result is True


def test_is_dataframe_empty_with_empty_polars_dataframe() -> None:
    empty_df = pl.DataFrame()
    result = _is_dataframe_empty(empty_df)
    assert result is True


def test_is_dataframe_empty_with_nonempty_polars_dataframe() -> None:
    df = pl.DataFrame({"col1": [1, 2]})
    result = _is_dataframe_empty(df)
    assert result is False


def test_is_dataframe_empty_with_pandas_dataframe_empty() -> None:
    mock_df = Mock()
    mock_df.empty = True

    result = _is_dataframe_empty(mock_df)

    assert result is True


def test_is_dataframe_empty_with_pandas_dataframe_nonempty() -> None:
    mock_df = Mock()
    mock_df.empty = False

    result = _is_dataframe_empty(mock_df)

    assert result is False


def test_is_dataframe_empty_with_object_without_empty_attr() -> None:
    mock_df = Mock()
    del mock_df.empty

    result = _is_dataframe_empty(mock_df)

    assert result is True


@pytest.mark.anyio
async def test_extract_tables_file_stat_os_error() -> None:
    file_path = "/nonexistent/file.pdf"

    with (
        patch("pathlib.Path.stat", side_effect=OSError("File not found")),
        patch.dict("os.environ", {"KREUZBERG_GMFT_ISOLATED": "true"}),
        patch("kreuzberg._gmft._extract_tables_isolated_async") as mock_isolated,
    ):
        mock_table_data = [TableData(cropped_image=Mock(), page_number=1, text="Sample table", df=pl.DataFrame())]
        mock_isolated.return_value = mock_table_data

        with patch("kreuzberg._gmft.get_table_cache") as mock_cache:
            mock_cache_instance = Mock()
            mock_cache.return_value = mock_cache_instance
            mock_cache_instance.aget = AsyncMock(return_value=None)
            mock_cache_instance.aset = AsyncMock()
            mock_cache_instance.is_processing.return_value = False
            mock_cache_instance.mark_processing.return_value = Mock()

            result = await extract_tables(file_path)

        assert result == mock_table_data
        mock_isolated.assert_called_once()


def test_extract_tables_sync_file_stat_os_error() -> None:
    file_path = "/nonexistent/file.pdf"

    with (
        patch("pathlib.Path.stat", side_effect=OSError("File not found")),
        patch.dict("os.environ", {"KREUZBERG_GMFT_ISOLATED": "true"}),
        patch("kreuzberg._gmft._extract_tables_isolated") as mock_isolated,
    ):
        mock_table_data = [TableData(cropped_image=Mock(), page_number=1, text="Sample table", df=pl.DataFrame())]
        mock_isolated.return_value = mock_table_data

        with patch("kreuzberg._gmft.get_table_cache") as mock_cache:
            mock_cache_instance = Mock()
            mock_cache.return_value = mock_cache_instance
            mock_cache_instance.get.return_value = None

            result = extract_tables_sync(file_path)

        assert result == mock_table_data
        mock_isolated.assert_called_once()


@pytest.mark.anyio
async def test_extract_tables_with_cache_hit() -> None:
    file_path = "/path/to/file.pdf"
    cached_tables = [TableData(cropped_image=Mock(), page_number=1, text="Cached table", df=pl.DataFrame())]

    with patch("pathlib.Path.stat") as mock_stat, patch("kreuzberg._gmft.get_table_cache") as mock_cache:
        mock_stat.return_value.st_size = 1000
        mock_stat.return_value.st_mtime = 123456789

        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.aget = AsyncMock(return_value=cached_tables)

        result = await extract_tables(file_path)

    assert result == cached_tables
    mock_cache_instance.aget.assert_called_once()


def test_extract_tables_sync_with_cache_hit() -> None:
    file_path = "/path/to/file.pdf"
    cached_tables = [TableData(cropped_image=Mock(), page_number=1, text="Cached table", df=pl.DataFrame())]

    with patch("pathlib.Path.stat") as mock_stat, patch("kreuzberg._gmft.get_table_cache") as mock_cache:
        mock_stat.return_value.st_size = 1000
        mock_stat.return_value.st_mtime = 123456789

        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = cached_tables

        result = extract_tables_sync(file_path)

    assert result == cached_tables
    mock_cache_instance.get.assert_called_once()


@pytest.mark.anyio
async def test_extract_tables_with_processing_wait() -> None:
    file_path = "/path/to/file.pdf"

    with (
        patch("pathlib.Path.stat") as mock_stat,
        patch("kreuzberg._gmft.get_table_cache") as mock_cache,
        patch("anyio.to_thread.run_sync") as mock_run_sync,
    ):
        mock_stat.return_value.st_size = 1000
        mock_stat.return_value.st_mtime = 123456789

        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance

        cached_result = [TableData(cropped_image=Mock(), page_number=1, text="Processed table", df=pl.DataFrame())]
        mock_cache_instance.aget = AsyncMock(side_effect=[None, cached_result])
        mock_cache_instance.is_processing.return_value = True

        mock_event = Mock()
        mock_cache_instance.mark_processing.return_value = mock_event

        result = await extract_tables(file_path)

        assert result == cached_result
        mock_run_sync.assert_called_once_with(mock_event.wait)
        assert mock_cache_instance.aget.call_count == 2


@pytest.mark.anyio
async def test_extract_tables_environment_variable_isolated_false() -> None:
    file_path = "/path/to/file.pdf"

    with (
        patch.dict("os.environ", {"KREUZBERG_GMFT_ISOLATED": "false"}),
        patch("pathlib.Path.stat") as mock_stat,
        patch("kreuzberg._gmft.get_table_cache") as mock_cache,
        patch("kreuzberg._gmft._extract_tables_isolated_async") as mock_isolated,
    ):
        mock_stat.return_value.st_size = 1000
        mock_stat.return_value.st_mtime = 123456789

        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.aget = AsyncMock(return_value=None)
        mock_cache_instance.aset = AsyncMock()
        mock_cache_instance.is_processing.return_value = False
        mock_cache_instance.mark_processing.return_value = Mock()

        with patch.dict("sys.modules", {"gmft": None, "gmft.auto": None}):
            with pytest.raises(MissingDependencyError):
                await extract_tables(file_path)

        mock_isolated.assert_not_called()


def test_extract_tables_sync_environment_variable_variations() -> None:
    file_path = "/path/to/file.pdf"

    test_cases = [
        ("true", True),
        ("1", True),
        ("yes", True),
        ("TRUE", True),
        ("false", False),
        ("0", False),
        ("no", False),
        ("", False),
        ("random", False),
    ]

    for env_value, expected_isolated in test_cases:
        with (
            patch.dict("os.environ", {"KREUZBERG_GMFT_ISOLATED": env_value}),
            patch("pathlib.Path.stat") as mock_stat,
            patch("kreuzberg._gmft.get_table_cache") as mock_cache,
            patch("kreuzberg._gmft._extract_tables_isolated") as mock_isolated,
        ):
            mock_stat.return_value.st_size = 1000
            mock_stat.return_value.st_mtime = 123456789

            mock_cache_instance = Mock()
            mock_cache.return_value = mock_cache_instance
            mock_cache_instance.get.return_value = None

            if expected_isolated:
                mock_isolated.return_value = []
                extract_tables_sync(file_path)
                mock_isolated.assert_called_once()
            else:
                with patch.dict("sys.modules", {"gmft": None, "gmft.auto": None}):
                    with pytest.raises(MissingDependencyError):
                        extract_tables_sync(file_path)
                mock_isolated.assert_not_called()


@pytest.mark.anyio
async def test_extract_tables_config_serialization() -> None:
    file_path = "/path/to/file.pdf"
    custom_config = GMFTConfig(verbosity=2, detector_base_threshold=0.8, formatter_base_threshold=0.9)

    with (
        patch("pathlib.Path.stat") as mock_stat,
        patch("kreuzberg._gmft.get_table_cache") as mock_cache,
        patch.dict("os.environ", {"KREUZBERG_GMFT_ISOLATED": "true"}),
        patch("kreuzberg._gmft._extract_tables_isolated_async") as mock_isolated,
    ):
        mock_stat.return_value.st_size = 1000
        mock_stat.return_value.st_mtime = 123456789

        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.aget = AsyncMock(return_value=None)
        mock_cache_instance.aset = AsyncMock()
        mock_cache_instance.is_processing.return_value = False
        mock_cache_instance.mark_processing.return_value = Mock()

        mock_isolated.return_value = []

        await extract_tables(file_path, config=custom_config)

        cache_call_kwargs = mock_cache_instance.aget.call_args[1]
        assert "config" in cache_call_kwargs
        assert "verbosity" in cache_call_kwargs["config"]
        assert "detector_base_threshold" in cache_call_kwargs["config"]


def test_extract_tables_sync_missing_gmft_dependency() -> None:
    file_path = "/path/to/file.pdf"

    with (
        patch.dict("os.environ", {"KREUZBERG_GMFT_ISOLATED": "false"}),
        patch("pathlib.Path.stat") as mock_stat,
        patch("kreuzberg._gmft.get_table_cache") as mock_cache,
    ):
        mock_stat.return_value.st_size = 1000
        mock_stat.return_value.st_mtime = 123456789

        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None

        with patch.dict("sys.modules", {"gmft": None, "gmft.auto": None}):
            with pytest.raises(MissingDependencyError) as exc_info:
                extract_tables_sync(file_path)

        error = exc_info.value
        assert "gmft" in str(error).lower()
        assert "table extraction" in str(error)


@pytest.mark.anyio
async def test_extract_tables_default_config() -> None:
    file_path = "/path/to/file.pdf"

    with (
        patch("pathlib.Path.stat") as mock_stat,
        patch("kreuzberg._gmft.get_table_cache") as mock_cache,
        patch.dict("os.environ", {"KREUZBERG_GMFT_ISOLATED": "true"}),
        patch("kreuzberg._gmft._extract_tables_isolated_async") as mock_isolated,
    ):
        mock_stat.return_value.st_size = 1000
        mock_stat.return_value.st_mtime = 123456789

        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.aget = AsyncMock(return_value=None)
        mock_cache_instance.aset = AsyncMock()
        mock_cache_instance.is_processing.return_value = False
        mock_cache_instance.mark_processing.return_value = Mock()

        mock_isolated.return_value = []

        await extract_tables(file_path)

        mock_isolated.assert_called_once()
        call_args = mock_isolated.call_args
        config_arg = call_args[0][1]
        assert isinstance(config_arg, GMFTConfig)


def test_extract_tables_sync_override_isolated_process_parameter() -> None:
    file_path = "/path/to/file.pdf"

    with (
        patch.dict("os.environ", {"KREUZBERG_GMFT_ISOLATED": "true"}),
        patch("pathlib.Path.stat") as mock_stat,
        patch("kreuzberg._gmft.get_table_cache") as mock_cache,
    ):
        mock_stat.return_value.st_size = 1000
        mock_stat.return_value.st_mtime = 123456789

        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get.return_value = None

        with patch.dict("sys.modules", {"gmft": None, "gmft.auto": None}):
            with pytest.raises(MissingDependencyError):
                extract_tables_sync(file_path, use_isolated_process=False)
