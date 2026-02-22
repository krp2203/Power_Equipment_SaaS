from flask import g
from sqlalchemy import event, orm
from app.core.extensions import db
from contextlib import contextmanager

@contextmanager
def global_tenant_bypass():
    """
    Context manager to temporarily bypass tenant filtering.
    Used during bridge key authentication to allow global lookup.
    """
    g.ignore_tenant_filter = True
    try:
        yield
    finally:
        g.ignore_tenant_filter = False

def register_multitenancy_handlers(app):
    @event.listens_for(orm.Session, "do_orm_execute")
    def _add_filtering_criteria(execute_state):
        """
        Intercepts every query to inject organization_id filter.
        """
        # 1. Skip filtering if we are in 'Superuser Context', outside a request, or during bridge auth
        if (getattr(g, 'is_superuser', False) or 
            not g.get('current_org_id') or 
            getattr(g, 'ignore_tenant_filter', False)):
            return

        # 2. Skip if the query isn't a SELECT/UPDATE/DELETE
        if execute_state.is_select or execute_state.is_update or execute_state.is_delete:
            # 3. Inject organization_id into the statement using with_loader_criteria
            # This is safer than filter_by as it handles joins and subqueries (like count) correctly.
            mapper = execute_state.bind_mapper
            if mapper and 'organization_id' in mapper.columns:
                execute_state.statement = execute_state.statement.options(
                    orm.with_loader_criteria(
                        mapper.class_,
                        lambda cls: cls.organization_id == g.current_org_id,
                        include_aliases=True
                    )
                )

def get_current_org_id():
    # Placeholder logic, to be replaced by middleware
    return g.get('current_org_id')
