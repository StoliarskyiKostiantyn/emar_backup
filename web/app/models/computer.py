import enum
from datetime import datetime

from sqlalchemy import JSON, or_, and_, sql, func, select, Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from flask import request

from flask_admin.model.template import EditRowAction, DeleteRowAction

from flask_login import current_user

from app import db
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView, get_outdated_status_comps

from .desktop_client import DesktopClient
from .user import UserPermissionLevel, UserRole
from .company import Company
from .location import Location
from .system_log import SystemLogType

from config import BaseConfig as CFG


# TODO add to all models secure form? csrf
# from flask_admin.form import SecureForm
# from flask_admin.contrib.sqla import ModelView

# class CarAdmin(ModelView):
#     form_base_class = SecureForm


class DeviceType(enum.Enum):
    LAPTOP = "LAPTOP"
    DESKTOP = "DESKTOP"


class DeviceRole(enum.Enum):
    PRIMARY = "PRIMARY"
    ALTERNATE = "ALTERNATE"


class Computer(db.Model, ModelMixin):

    __tablename__ = "computers"

    id = db.Column(db.Integer, primary_key=True)

    location_id = db.Column(
        db.Integer, db.ForeignKey("locations.id", ondelete="CASCADE"), nullable=True
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )

    computer_name = db.Column(db.String(64), unique=True, nullable=False)
    sftp_host = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_HOST)
    sftp_username = db.Column(db.String(64), default=CFG.DEFAULT_SFTP_USERNAME)
    sftp_password = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_PASSWORD)
    sftp_folder_path = db.Column(db.String(256))
    folder_password = db.Column(db.String(128), default=CFG.DEFAULT_FOLDER_PASSWORD)

    type = db.Column(db.String(128))
    device_type = db.Column(Enum(DeviceType), nullable=True)
    device_role = db.Column(
        Enum(DeviceRole),
        nullable=False,
        default=DeviceRole.PRIMARY,
        server_default=sql.text("'PRIMARY'"),
    )
    msi_version = db.Column(db.String(64), default="stable")
    current_msi_version = db.Column(db.String(64))

    alert_status = db.Column(db.String(128))
    download_status = db.Column(db.String(64))
    last_download_time = db.Column(db.DateTime)
    last_time_online = db.Column(db.DateTime)
    identifier_key = db.Column(db.String(128), default="new_computer", nullable=False)

    manager_host = db.Column(db.String(256), default=CFG.DEFAULT_MANAGER_HOST)
    # Place where backup file was downloaded last time (tempdir)
    last_downloaded = db.Column(db.String(256))
    # Place where backup file was saved last time (directory inside emar_backups.zip)
    last_saved_path = db.Column(db.String(256))
    files_checksum = db.Column(JSON)
    # TODO do we need this one? Could computer be deactivated?
    activated = db.Column(db.Boolean, default=False)

    logs_enabled = db.Column(db.Boolean, server_default=sql.true(), default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    computer_ip = db.Column(db.String(128))

    last_time_logs_enabled = db.Column(db.DateTime, default=datetime.now)
    last_time_logs_disabled = db.Column(db.DateTime)

    company = relationship(
        "Company",
        passive_deletes=True,
        backref=backref("computers", cascade="delete"),
        lazy="select",
    )

    location = relationship(
        "Location",
        passive_deletes=True,
        backref=backref("computers", cascade="delete"),
        lazy="select",
    )

    def __repr__(self):
        return self.computer_name

    def _cols(self):
        return [
            "computer_name",
            "alert_status",
            "company_id",
            "location_id",
            "download_status",
            "last_download_time",
            "last_time_online",
            "msi_version",
            "current_msi_version",
            "sftp_host",
            "sftp_username",
            "sftp_folder_path",
            "type",
            "device_type",
            "device_role",
            "manager_host",
            "activated",
            "logs_enabled",
            "files_checksum",
            "identifier_key",
            "computer_ip",
        ]

    @hybrid_property
    def location_name(self):
        return self.location.name if self.location else None

    @location_name.expression
    def location_name(cls):
        return select([Location.name]).where(cls.location_id == Location.id).as_scalar()

    @location_name.setter
    def location_name(self, value):
        new_location = Location.query.filter_by(name=value).first()
        self.location_id = new_location.id if new_location else None

    @hybrid_property
    def company_name(self):
        return self.company.name if self.company else None

    @company_name.expression
    def company_name(cls):
        return select([Company.name]).where(cls.company_id == Company.id).as_scalar()

    @company_name.setter
    def company_name(self, value):
        new_company = Company.query.filter_by(name=value).first()
        self.company_id = new_company.id if new_company else None


class ComputerView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "ComputerView"

    list_template = "import-computer-to-dashboard.html"

    column_hide_backrefs = False
    column_list = [
        "computer_name",
        "alert_status",
        "company_name",
        "location_name",
        "last_download_time",
        "last_time_online",
        "msi_version",
        "current_msi_version",
        "sftp_host",
        "sftp_username",
        "sftp_folder_path",
        "type",
        "device_type",
        "device_role",
        "manager_host",
        "activated",
        "logs_enabled",
        "computer_ip",
    ]

    form_excluded_columns = (
        "log_events",
        "backup_logs",
        "last_time_logs_enabled",
        "last_time_logs_disabled",
    )

    column_searchable_list = column_list
    column_sortable_list = column_list
    column_filters = column_list

    # NOTE allows edit in list view, but has troubles with permissions
    # column_editable_list = [
    #     # "computer_name",
    #     "company",
    #     # "location",
    #     # "type",
    #     # "sftp_host",
    #     # "sftp_username",
    #     # "sftp_folder_path",
    #     # "manager_host",
    # ]

    # TODO uncomment files_checksum when ready to go on
    form_widget_args = {
        "last_download_time": {"readonly": True},
        "last_time_online": {"readonly": True},
        "identifier_key": {"readonly": True},
        "created_at": {"readonly": True},
        "alert_status": {"readonly": True},
        "download_status": {"readonly": True},
        "last_downloaded": {"readonly": True},
        "last_saved_path": {"readonly": True},
        "current_msi_version": {"readonly": True},
        "computer_ip": {"readonly": True},
        "type": {"readonly": True},
        # "files_checksum": {"readonly": True},
    }

    # form_args control fields order. It is dict though...
    form_args = {
        "computer_name": {"label": "Computer name"},
        "company_id": {"label": "Company id", "id": "company_id"},
        "location_id": {"label": "Location id", "id": "location_id"},
        "sftp_host": {"label": "SFTP host"},
        "sftp_username": {"label": "SFTP username"},
        "sftp_password": {"label": "SFTP password"},
        "sftp_folder_path": {"label": "SFTP folder path"},
        "type": {"label": "Type"},
        "device_type": {"label": "Device type"},
        "device_role": {"label": "Device role"},
        "msi_version": {"label": "Msi version"},
        "current_msi_version": {"label": "Current msi version"},
        "manager_host": {"label": "Manager host"},
        "activated": {"label": "Activated"},
        "logs_enabled:": {"label": "Logs enabled"},
        "alert_status": {"label": "Alert status"},
        "download_status": {"label": "Download status"},
        "last_download_time": {"label": "Last download time"},
        "last_time_online": {"label": "Last time online"},
        "identifier_key": {"label": "Identifier key"},
        "files_checksum": {"label": "Files checksum"},
        "created_at": {"label": "Created at"},
        "computer_ip": {"label": "Computer IP"},
    }

    form_choices = {"msi_version": CFG.CLIENT_VERSIONS}

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

    def create_form(self, obj=None):
        form = super().create_form(obj)

        # apply a sort to the relation
        form.company.query_factory = lambda: Company.query.filter(
            Company.is_global.is_(False)
        ).order_by(Company.name)
        form.location.query_factory = lambda: Location.query.order_by(Location.name)

        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)

        # Remember the prev value of the field logs_enabled
        self.logs_enabled_prev_value = obj.logs_enabled

        # apply a sort to the relation
        form.company.query_factory = lambda: Company.query.filter(
            Company.is_global.is_(False)
        ).order_by(Company.name)
        form.location.query_factory = lambda: Location.query.order_by(Location.name)

        return form

    def on_model_change(self, form, model, is_created):
        if not is_created and self.logs_enabled_prev_value != model.logs_enabled:
            if model.logs_enabled:
                model.last_time_logs_enabled = datetime.utcnow()
            else:
                model.last_time_logs_disabled = datetime.utcnow()

    def after_model_change(self, form, model, is_created):
        from app.controllers import create_system_log

        # Create system log that computer was created or updated
        if is_created:
            create_system_log(SystemLogType.COMPUTER_CREATED, model, current_user)
        else:
            create_system_log(SystemLogType.COMPUTER_UPDATED, model, current_user)

    def after_model_delete(self, model):
        from app.controllers import create_system_log

        # Create system log that computer was deleted
        create_system_log(SystemLogType.COMPUTER_DELETED, model, current_user)

    def get_query(self):

        OBLIGATORY_VERSIONS = [
            ("stable", "stable"),
            ("latest", "latest"),
        ]

        versions = [
            i.version
            for i in DesktopClient.query.with_entities(DesktopClient.version).all()
        ]

        # remove old versions from global versions variable
        for version in CFG.CLIENT_VERSIONS:
            if version[0] not in versions or version not in OBLIGATORY_VERSIONS:
                CFG.CLIENT_VERSIONS.remove(version)

        # add new versions to global versions variable
        for version in versions:
            if (version, version) not in CFG.CLIENT_VERSIONS:
                CFG.CLIENT_VERSIONS.append((version, version))
        for dversion in OBLIGATORY_VERSIONS:
            if dversion not in CFG.CLIENT_VERSIONS:
                CFG.CLIENT_VERSIONS.append(dversion)

        # NOTE handle permissions - meaning which details current user could view
        self.form_choices = CFG.CLIENT_VERSIONS

        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and current_user.role == UserRole.ADMIN
        ):
            if "delete" in self.action_disallowed_list:
                self.action_disallowed_list.remove("delete")
            self.can_create = True
        else:
            if "delete" not in self.action_disallowed_list:
                self.action_disallowed_list.append("delete")
            self.can_create = False

        match current_user.permission:
            case UserPermissionLevel.GLOBAL:
                result_query = self.session.query(self.model)
            case UserPermissionLevel.COMPANY:
                result_query = self.session.query(self.model).filter(
                    or_(
                        self.model.company_id == current_user.company_id,
                        self.model.location_id.in_(
                            [loc.id for loc in current_user.company.locations]
                        ),
                    )
                )
            case UserPermissionLevel.LOCATION_GROUP:
                result_query = self.session.query(self.model).filter(
                    self.model.location_id.in_(
                        [loc.id for loc in current_user.location_group[0].locations]
                    )
                )
            case UserPermissionLevel.LOCATION:
                result_query = self.session.query(self.model).filter(
                    self.model.location_id == current_user.location[0].id
                )
            case _:
                result_query = self.session.query(self.model).filter(
                    self.model.id == -1
                )

        # NOTE this if closure is used for Dashboard cards searches (index.html)
        if "search" in request.values:
            # NOTE last letter is missed to not intervene in common user search
            alert_types = {"offlin": 48, "backu": 4}

            if request.values["search"] in alert_types:
                alerted_computers: list[Computer] = (
                    Computer.query.filter(
                        and_(
                            Computer.alert_status != "green",
                            Computer.alert_status.isnot(None),
                        )
                    )
                    .with_entities(
                        Computer.id, Computer.computer_name, Computer.alert_status
                    )
                    .all()
                )
                for alert in alert_types:
                    if request.values["search"] == alert:

                        offline_48h = get_outdated_status_comps(
                            alerted_computers, alert_types[alert], str(alert)[:-1]
                        )
                        result_query = result_query.filter(
                            self.model.id.in_([comp.id for comp in offline_48h])
                        )
                        # NOTE Change headers to use unique search value. Doesnt work at this point.
                        # from werkzeug.datastructures import ImmutableMultiDict, CombinedMultiDict
                        # change_search = request.args.to_dict()
                        # change_search["search"] = "offline"
                        # request.args = ImmutableMultiDict(change_search)
                        # request.values = CombinedMultiDict(
                        #     [ImmutableMultiDict([("search", "offline")])]
                        # )
                        # request.url = "http://localhost:5000/admin/computer/?search=offline"
                        # request.environ["QUERY_STRING"] = "search=offline"
                        # request.environ[
                        #     "HTTP_REFERER"
                        # ] = "http://localhost:5000/admin/computer/?search=offline"
                        # request.environ["RAW_URI"] = "/admin/computer/?search=offline"
                        # request.environ["REQUEST_URI"] = "/admin/computer/?search=offline"

        return result_query

    def get_count_query(self):
        actual_query = self.get_query()

        # .with_entities(func.count()) doesn't count correctly when there is no filtering was applied to query
        # Instead add select_from(self.model) to query to count correctly
        if (
            current_user.permission == UserPermissionLevel.GLOBAL
            and not request.values.get("search")
        ):
            return actual_query.with_entities(func.count()).select_from(self.model)

        return actual_query.with_entities(func.count())
