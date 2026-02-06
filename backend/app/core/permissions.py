from typing import Iterable


def has_permission(user_permissions: Iterable[str], required: str) -> bool:
    if required in user_permissions:
        return True

    req_parts = required.split(":")

    for perm in user_permissions:
        if perm == "*":
            return True

        perm_parts = perm.split(":")

        # Case 1: Prefix wildcard e.g. "hotel:*" matches "hotel:rooms:create"
        if perm_parts[-1] == "*" and len(perm_parts) < len(req_parts):
            if perm_parts[:-1] == req_parts[: len(perm_parts) - 1]:
                return True

        # Case 2: Component wildcard e.g. "hotel:*:create" matches "hotel:rooms:create"
        if len(perm_parts) == len(req_parts):
            match = True
            for p, r in zip(perm_parts, req_parts):
                if p != "*" and p != r:
                    match = False
                    break
            if match:
                return True

    return False
