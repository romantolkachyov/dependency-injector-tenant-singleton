from dependency_injector import providers

from dependency_injector_tenant_singleton import TenantSingleton


def get_current_tenant() -> str:
    return "example"


def test_smoke() -> None:
    active_tenant = providers.Factory(get_current_tenant)
    instance = TenantSingleton(active_tenant, providers.Object(42))
    assert instance() == 42


if __name__ == "__main__":  # pragma: no cover
    test_smoke()
