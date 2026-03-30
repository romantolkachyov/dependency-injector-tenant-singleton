.. image:: https://img.shields.io/github/actions/workflow/status/romantolkachyov/dependency-injector-tenant-singleton/build.yml?branch=master
   :target: https://github.com/romantolkachyov/dependency-injector-tenant-singleton/actions
   :alt: Build Status

.. image:: https://img.shields.io/pypi/v/dependency_injector_tenant_singleton.svg
   :target: https://pypi.org/project/dependency-injector-tenant-singleton/
   :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/dependency_injector_tenant_singleton.svg
   :target: https://pypi.org/project/dependency-injector-tenant-singleton/
   :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/l/dependency_injector_tenant_singleton.svg
   :target: https://pypi.org/project/dependency-injector-tenant-singleton/
   :alt: License

# dependency-injector-tenant-singleton

Tenant-scoped singleton provider for the [dependency-injector](https://github.com/ets-labs/python-dependency-injector) framework.

## Overview

`TenantSingleton` is a provider that creates singleton instances scoped to individual tenants. Unlike a global singleton that returns the same instance everywhere, `TenantSingleton` returns the same instance for the same tenant while providing different instances for different tenants.

This is useful in multi-tenant applications where you need:
- Separate configurations per tenant
- Isolated resources for each tenant
- Tenant-scoped caching or state

## Installation

```bash
pip install dependency-injector-tenant-singleton
```

## Usage

```python
from dependency_injector import containers, providers
from dependency_injector_tenant_singleton import TenantSingleton


def get_current_tenant() -> str:
    """Get the current tenant identifier."""
    return "tenant-a"


class Container(containers.DeclarativeContainer):
    #: Current active tenant
    active_tenant = providers.Factory(get_current_tenant)

    #: Tenant-scoped service instance
    service = TenantSingleton(
        active_tenant,
        SomeService,
        # Additional args/kwargs are passed to the factory
    )


container = Container()

# Same tenant - same instance
with container.active_tenant.override("tenant-a"):
    instance1 = container.service()
    instance2 = container.service()
    assert instance1 is instance2  # Same instance for tenant-a

# Different tenant - different instance
with container.active_tenant.override("tenant-b"):
    instance3 = container.service()
    assert instance3 is not instance1  # Different instance for tenant-b

# Back to tenant-a - same instance as before
with container.active_tenant.override("tenant-a"):
    instance4 = container.service()
    assert instance4 is instance1  # Same instance again
```

## How It Works

`TenantSingleton` accepts a provider that returns a tenant identifier and a factory callable:

```python
TenantSingleton(tenant_provider, factory, *args, **kwargs)
```

- `tenant_provider` - A provider that returns the current tenant identifier
- `factory` - Callable that creates the instance (class, function, etc.)
- `*args`, `**kwargs` - Additional arguments passed to the factory

Internally, `TenantSingleton` maintains a mapping of tenant identifiers to singleton instances. When called, it:

1. Resolves the current tenant identifier from `tenant_provider`
2. Creates a singleton for that tenant if it doesn't exist
3. Returns the tenant's singleton instance

## License

MIT License
