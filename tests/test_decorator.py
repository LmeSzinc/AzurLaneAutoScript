"""Unit tests for cached_class_property (moved to module.base.decorator in P2.1).

The descriptor caches per-class, supports inheritance, and reads through
instances to the class-level cache.
"""

from module.base.decorator import cached_class_property


class Base:
    calls = 0

    @cached_class_property
    def value(cls):
        cls.calls += 1
        return object()


class Child(Base):
    pass


def test_cached_per_class():
    first = Base.value
    assert Base.value is first
    assert Base.calls == 1


def test_inheritance_isolates_cache():
    value_base = Base.value
    value_child = Child.value
    assert value_base is not value_child
    # Base's cache was computed by the earlier test run or this one; the
    # key property is that computing Child's value ran the getter exactly
    # once more and cached independently.
    calls_after_child = Child.calls
    assert Child.value is value_child
    assert Child.calls == calls_after_child
    assert Base.value is value_base


def test_instance_access_reads_class_cache():
    instance = Base()
    assert instance.value is Base.value
    assert Base.calls <= 2  # at most one extra computation from previous tests
