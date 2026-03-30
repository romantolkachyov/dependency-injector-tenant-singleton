from collections.abc import Callable, Iterator
from typing import Any, TypeVar

from dependency_injector import providers
from dependency_injector.providers import deepcopy

T = TypeVar("T")


class TenantSingleton(providers.Provider[T]):
    """Tenant-scoped singleton provider.

    A DI container provider that returns the same object instance for the same
    ``tenant_name`` value.

    This enables implementing singleton providers that are scoped to individual
    tenants or clients, rather than global singletons.

    Example usage in a container:

    .. code-block:: python

        class Container(containers.DeclarativeContainer):
            #: Current active tenant
            active_tenant_name = providers.Factory(get_active_tenant_name)

            tenant_local_object = TenantSingleton(active_tenant_name, object)

        container = Container()
        with container.active_tenant_name.override("first"):
            instance1 = container.tenant_local_object()
            instance2 = container.tenant_local_object()

        assert instance1 is instance2

        with container.active_tenant_name.override("second"):
            instance3 = container.tenant_local_object()

        assert instance3 is not instance1

    """

    __slots__ = ("_tenant_name", "_provides", "_instance_by_tenant", "_args", "_kwargs")

    def __init__(
        self,
        tenant_name: providers.Provider[Any],
        provides: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self._tenant_name = tenant_name
        self._instance_by_tenant: dict[Any, providers.Singleton[T]] = {}
        self._provides = provides
        self._args = args
        self._kwargs = kwargs
        super().__init__()

    def __deepcopy__(self, memo: dict[Any, Any] | None) -> Any:
        memo = memo or {}
        copied = memo.get(id(self))
        if copied is not None:  # pragma: no cover
            return copied

        copied = self.__class__(
            deepcopy(self._tenant_name, memo),
            self._provides,
            *providers.deepcopy(self._args, memo),
            **providers.deepcopy(self._kwargs, memo),
        )
        copied.set_storage(providers.deepcopy(self._instance_by_tenant, memo))
        self._copy_overridings(copied, memo)

        return copied

    def set_storage(
        self, instance_by_tenant: dict[Any, providers.Singleton[T]]
    ) -> None:
        self._instance_by_tenant = instance_by_tenant

    @property
    def related(self) -> Iterator[providers.Provider[Any]]:
        """Return related providers generator."""
        yield from [self._tenant_name]
        yield from self._instance_by_tenant.values()
        yield from super().related

    def _provide(self, args: Any, kwargs: Any) -> T:
        tenant_name = self._tenant_name()
        if tenant_name not in self._instance_by_tenant:
            self._instance_by_tenant[tenant_name] = providers.Singleton(
                self._provides, *self._args, **self._kwargs
            )
        return self._instance_by_tenant[tenant_name]()
