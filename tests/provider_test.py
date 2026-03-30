"""Tests for TenantSingleton provider."""

from copy import deepcopy

import pytest
from dependency_injector import containers, providers

from dependency_injector_tenant_singleton import TenantSingleton


class DummyService:
    """Test service for verifying singleton behavior."""

    def __init__(self, value: str = "default"):
        self.value = value


def get_tenant_a() -> str:
    return "tenant-a"


@pytest.fixture
def container():
    """Create a test container with TenantSingleton."""

    class Container(containers.DeclarativeContainer):
        tenant = providers.Factory(get_tenant_a)
        service = TenantSingleton(tenant, DummyService)

    return Container()


@pytest.fixture
def container_with_args():
    """Create a test container with TenantSingleton that passes args to factory."""

    class Container(containers.DeclarativeContainer):
        tenant = providers.Factory(get_tenant_a)
        service = TenantSingleton(tenant, DummyService, "custom-value")

    return Container()


@pytest.fixture
def container_with_kwargs():
    """Create a test container with TenantSingleton that passes kwargs to factory."""

    class Container(containers.DeclarativeContainer):
        tenant = providers.Factory(get_tenant_a)
        service = TenantSingleton(tenant, DummyService, value="kwarg-value")

    return Container()


def test_same_tenant_returns_same_instance(container):
    """Same tenant should get the same instance (singleton behavior)."""
    instance1 = container.service()
    instance2 = container.service()

    assert instance1 is instance2


def test_different_tenants_get_different_instances(container):
    """Different tenants should get different instances."""
    with container.tenant.override("tenant-a"):
        instance_a = container.service()

    with container.tenant.override("tenant-b"):
        instance_b = container.service()

    assert instance_a is not instance_b


def test_returning_to_same_tenant_returns_same_instance(container):
    """Returning to a previous tenant should return the cached instance."""
    with container.tenant.override("tenant-a"):
        instance1 = container.service()

    with container.tenant.override("tenant-b"):
        _ = container.service()

    with container.tenant.override("tenant-a"):
        instance2 = container.service()

    assert instance1 is instance2


def test_args_passed_to_factory(container_with_args):
    """Additional args should be passed to the factory."""
    instance = container_with_args.service()

    assert instance.value == "custom-value"


def test_kwargs_passed_to_factory(container_with_kwargs):
    """Additional kwargs should be passed to the factory."""
    instance = container_with_kwargs.service()

    assert instance.value == "kwarg-value"


def test_related_providers_includes_tenant_provider(container):
    """Related providers should include the tenant provider."""
    related = list(container.service.related)

    assert container.tenant in related


def test_deepcopy_creates_independent_copy(container):
    """Deepcopy should create an independent copy of the provider."""
    copied = deepcopy(container.service)

    with container.tenant.override("tenant-a"):
        container.service()

    with container.tenant.override("tenant-a"):
        copied_instance = copied()

    assert isinstance(copied_instance, DummyService)


def test_multiple_tenants_isolated_storage(container):
    """Multiple tenants should have completely isolated storage."""
    with container.tenant.override("tenant-1"):
        instance1 = container.service()

    with container.tenant.override("tenant-2"):
        instance2 = container.service()

    with container.tenant.override("tenant-3"):
        instance3 = container.service()

    assert instance1 is not instance2
    assert instance2 is not instance3
    assert instance1 is not instance3

    with container.tenant.override("tenant-1"):
        assert container.service() is instance1

    with container.tenant.override("tenant-2"):
        assert container.service() is instance2

    with container.tenant.override("tenant-3"):
        assert container.service() is instance3


def test_tenant_provider_can_be_any_provider_type():
    """The tenant provider can be any provider type, not just Factory."""

    class Container(containers.DeclarativeContainer):
        config = providers.Configuration()
        service = TenantSingleton(config.tenant_name, DummyService)

    container = Container()
    container.config.tenant_name.from_value("config-tenant")

    instance = container.service()

    assert isinstance(instance, DummyService)


def test_factory_function_as_provider():
    """Test with a dynamic tenant provider."""
    call_count = 0

    def get_tenant():
        nonlocal call_count
        call_count += 1
        return f"tenant-{call_count}"

    class Container(containers.DeclarativeContainer):
        tenant = providers.Factory(get_tenant)
        service = TenantSingleton(tenant, DummyService)

    container = Container()

    instance1 = container.service()
    instance2 = container.service()

    assert isinstance(instance1, DummyService)
    assert isinstance(instance2, DummyService)


def test_none_as_tenant_name():
    """None can be used as a valid tenant identifier."""

    class Container(containers.DeclarativeContainer):
        tenant = providers.Factory(lambda: None)
        service = TenantSingleton(tenant, DummyService)

    container = Container()

    instance1 = container.service()
    instance2 = container.service()

    assert instance1 is instance2


def test_integer_as_tenant_name():
    """Integer can be used as a valid tenant identifier."""

    class Container(containers.DeclarativeContainer):
        tenant = providers.Factory(lambda: 42)
        service = TenantSingleton(tenant, DummyService)

    container = Container()

    instance1 = container.service()
    instance2 = container.service()

    assert instance1 is instance2
