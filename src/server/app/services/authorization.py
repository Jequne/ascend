from __future__ import annotations

from collections.abc import Sequence

from ..models.auth import AuthContext, normalize_scopes
from .exceptions import AuthorizationError


class AuthorizationService:
    def can_access(self, context: AuthContext, required_scopes: Sequence[str]) -> bool:
        normalized_required = normalize_scopes(required_scopes)
        if not normalized_required:
            return True
        return context.has_all_scopes(normalized_required)

    def require_any_scope(self, context: AuthContext, required_scopes: Sequence[str]) -> AuthContext:
        normalized_required = normalize_scopes(required_scopes)
        if not normalized_required:
            return context
        if context.has_any_scope(normalized_required):
            return context
        raise AuthorizationError("insufficient scope")

    def require_all_scopes(self, context: AuthContext, required_scopes: Sequence[str]) -> AuthContext:
        normalized_required = normalize_scopes(required_scopes)
        if not normalized_required:
            return context
        if context.has_all_scopes(normalized_required):
            return context
        raise AuthorizationError("insufficient scope")