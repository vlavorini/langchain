"""Test base LLM functionality."""
from sqlalchemy import (Column, DateTime, Integer,
                        Sequence, String, create_engine)

try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

from langchain_core.outputs import Generation, LLMResult

from langchain.cache import InMemoryCache, SQLAlchemyCache
from langchain.globals import get_llm_cache, set_llm_cache
from langchain.llms.base import __all__
from tests.unit_tests.llms.fake_llm import FakeLLM

EXPECTED_ALL = [
    "BaseLLM",
    "LLM",
    "BaseLanguageModel",
]


def test_all_imports() -> None:
    assert set(__all__) == set(EXPECTED_ALL)


def test_caching() -> None:
    """Test caching behavior."""
    set_llm_cache(InMemoryCache())
    llm = FakeLLM()
    params = llm.dict()
    params["stop"] = None
    llm_string = str(sorted([(k, v) for k, v in params.items()]))
    get_llm_cache().update("foo", llm_string, [Generation(text="fizz")])
    output = llm.generate(["foo", "bar", "foo"])
    expected_cache_output = [Generation(text="foo")]
    cache_output = get_llm_cache().lookup("bar", llm_string)
    assert cache_output == expected_cache_output
    set_llm_cache(None)
    expected_generations = [
        [Generation(text="fizz")],
        [Generation(text="foo")],
        [Generation(text="fizz")],
    ]
    expected_output = LLMResult(
        generations=expected_generations,
        llm_output=None,
    )
    assert output == expected_output


def test_custom_caching() -> None:
    """Test custom_caching behavior."""
    Base = declarative_base()

    class FulltextLLMCache(Base):  # type: ignore
        """Postgres table for fulltext-indexed LLM Cache."""

        __tablename__ = "llm_cache_fulltext"
        id = Column(Integer, Sequence("cache_id"), primary_key=True)
        prompt = Column(String, nullable=False)
        llm = Column(String, nullable=False)
        idx = Column(Integer)
        datetime = Column(DateTime)
        response = Column(String)

    engine = create_engine("sqlite://")
    set_llm_cache(SQLAlchemyCache(engine, FulltextLLMCache))
    llm = FakeLLM()
    params = llm.dict()
    params["stop"] = None
    llm_string = str(sorted([(k, v) for k, v in params.items()]))
    get_llm_cache().update("foo", llm_string, [Generation(text="fizz")])
    output = llm.generate(["foo", "bar", "foo"])
    expected_cache_output = [Generation(text="foo")]
    cache_output = get_llm_cache().lookup("bar", llm_string)
    assert cache_output == expected_cache_output
    set_llm_cache(None)
    expected_generations = [
        [Generation(text="fizz")],
        [Generation(text="foo")],
        [Generation(text="fizz")],
    ]
    expected_output = LLMResult(
        generations=expected_generations,
        llm_output=None,
    )
    assert output == expected_output
