from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import relationship

from flask_login import current_user
from flask_admin.model.template import EditRowAction, DeleteRowAction

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView


class Location(db.Model, ModelMixin):

    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    company = relationship("Company", passive_deletes=True, lazy="select")
    # TODO swap company name to company id. Same for all models
    company_name = db.Column(
        db.String, db.ForeignKey("companies.name", ondelete="CASCADE")
    )
    computers_per_location = db.Column(db.Integer)
    computers_online = db.Column(db.Integer)
    computers_offline = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return self.name

    def _cols(self):
        return [
            "name",
            "company_name",
            "computers_per_location",
            "computers_online",
            "computers_offline",
        ]


class LocationView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "LocationView"

    column_hide_backrefs = False
    column_list = [
        "name",
        "company_name",
        "computers_per_location",
        "computers_online",
        "computers_offline",
    ]
    column_searchable_list = column_list
    column_filters = column_list
    column_sortable_list = column_list
    action_disallowed_list = ["delete"]

    def search_placeholder(self):
        """Defines what text will be displayed in Search input field

        Returns:
            str: text to display in search
        """
        return "Search by all text columns"

    def _can_edit(self, model):
        # return True to allow edit
        if str(current_user.asociated_with).lower() == "global-full":
            return True
        else:
            return False

    def _can_delete(self, model):
        if str(current_user.asociated_with).lower() == "global-full":
            return True
        else:
            return False

    def allow_row_action(self, action, model):

        if isinstance(action, EditRowAction):
            return self._can_edit(model)

        if isinstance(action, DeleteRowAction):
            return self._can_delete(model)

        # otherwise whatever the inherited method returns
        return super().allow_row_action(action, model)

    def get_query(self):

        # TODO make universal (func or something) for every model
        # NOTE handle permissions - meaning which details current user could view
        if current_user:
            if str(current_user.asociated_with).lower() == "global-full":
                if "delete" in self.action_disallowed_list:
                    self.action_disallowed_list.remove("delete")
                self.can_create = True
            else:
                if "delete" not in self.action_disallowed_list:
                    self.action_disallowed_list.append("delete")
                self.can_create = False

            user_permission: str = current_user.asociated_with
            if (
                user_permission.lower() == "global-full"
                or user_permission.lower() == "global-view"
            ):
                result_query = self.session.query(self.model)
            else:
                result_query = self.session.query(self.model).filter(
                    or_(
                        self.model.name == user_permission,
                        self.model.company_name == user_permission,
                    )
                )
        else:
            result_query = self.session.query(self.model).filter(
                self.model.computer_name == "None"
            )
        return result_query
