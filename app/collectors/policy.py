"""Pure, testable online collection permission gate."""


def may_fetch_online(*, global_enabled: bool, source_enabled: bool,
                     policy_status: str, policy_reference: str | None) -> bool:
    """True only with TWO enabled switches and a documented approved policy.

    This is a technical control, not a substitute for checking actual permissions.
    """
    return bool(global_enabled and source_enabled and policy_status == 'approved'
                and policy_reference and policy_reference.strip())
