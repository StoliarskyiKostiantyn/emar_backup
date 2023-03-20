from datetime import datetime

# import psycopg2
# from flask import request, url_for

from sqlalchemy import JSON, or_
from sqlalchemy.orm import relationship
from flask_admin.contrib.sqla import form, filters as sqla_filters, tools

# from flask_login import current_user
# from flask_admin.contrib.sqla.fields import Select2Widget, QuerySelectField
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader

# from flask_admin.model.form import InlineFormAdmin
from flask_admin.model.template import EditRowAction, DeleteRowAction

from flask_login import current_user

from app import db
from .location import Location
from .company import Company

# from .desktop_client import DesktopClient

# from app.forms import SearchForm
from app.models.utils import ModelMixin, RowActionListMixin
from app.utils import MyModelView

from config import BaseConfig as CFG


# TODO add to all models secure form? csrf
# from flask_admin.form import SecureForm
# from flask_admin.contrib.sqla import ModelView

# class CarAdmin(ModelView):
#     form_base_class = SecureForm


# NOTE 1 rest of code below
# check if tables were created
# con = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/db")
# cur = con.cursor()
# query = "SELECT * FROM locations;"
# cur.execute(query)
# sql_result = cur.fetchall()
# print(sql_result)
# con.close()


class Computer(db.Model, ModelMixin):

    __tablename__ = "computers"

    id = db.Column(db.Integer, primary_key=True)
    computer_name = db.Column(db.String(64), unique=True, nullable=False)

    location = relationship(
        "Location", passive_deletes=True, backref="computers", lazy="select"
    )
    location_name = db.Column(
        db.String, db.ForeignKey("locations.name", ondelete="CASCADE")
    )

    type = db.Column(db.String(128))
    alert_status = db.Column(db.String(128))
    activated = db.Column(
        db.Boolean, default=False
    )  # TODO do we need this one? Could computer be deactivated?
    created_at = db.Column(db.DateTime, default=datetime.now)

    sftp_host = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_HOST)
    sftp_username = db.Column(db.String(64), default=CFG.DEFAULT_SFTP_USERNAME)
    sftp_password = db.Column(db.String(128), default=CFG.DEFAULT_SFTP_PASSWORD)
    sftp_folder_path = db.Column(db.String(256))

    folder_password = db.Column(db.String(128), default=CFG.DEFAULT_FOLDER_PASSWORD)
    download_status = db.Column(db.String(64))
    last_download_time = db.Column(db.DateTime)
    last_time_online = db.Column(db.DateTime)
    identifier_key = db.Column(db.String(128), default="new_computer", nullable=False)
    msi_version = db.Column(db.String(64))

    company = relationship(
        "Company", passive_deletes=True, backref="computers", lazy="select"
    )
    company_name = db.Column(
        db.String, db.ForeignKey("companies.name", ondelete="CASCADE")
    )

    manager_host = db.Column(db.String(256))
    last_downloaded = db.Column(db.String(256))
    files_checksum = db.Column(JSON)

    def __repr__(self):
        return self.computer_name

    def _cols(self):
        return [
            "computer_name",
            "alert_status",
            "company_name",
            "location_name",
            "download_status",
            "last_download_time",
            "last_time_online",
            "msi_version",
            "sftp_host",
            "sftp_username",
            "sftp_folder_path",
            "type",
            "manager_host",
            "activated",
        ]


class ComputerView(RowActionListMixin, MyModelView):
    def __repr__(self):
        return "ComputerView"

    list_template = "import-computer-to-dashboard.html"

    # NOTE could be useful when define the permissions
    # can_create = False
    # can_edit = False
    # can_delete = False

    column_hide_backrefs = False
    column_list = [
        "computer_name",
        "alert_status",
        "company_name",
        "location_name",
        "download_status",
        "last_download_time",
        "last_time_online",
        "msi_version",
        "sftp_host",
        "sftp_username",
        "sftp_folder_path",
        "type",
        "manager_host",
        "activated",
    ]

    column_searchable_list = column_list
    column_sortable_list = column_list
    column_filters = column_list

    # allows edit in list view, but has troubles with permissions
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

    form_widget_args = {
        "last_download_time": {"readonly": True},
        "last_time_online": {"readonly": True},
        "identifier_key": {"readonly": True},
        "created_at": {"readonly": True},
        "alert_status": {"readonly": True},
        "download_status": {"readonly": True},
        "last_downloaded": {"readonly": True},
        # "files_checksum": {"readonly": True},
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

    # list rows depending on current user permissions
    def get_query(self):

        self.form_choices = CFG.CLIENT_VERSIONS

        if current_user:
            if str(current_user.asociated_with).lower() == "global-full":
                if "delete" in self.action_disallowed_list:
                    self.action_disallowed_list.remove("delete")
                self.can_create = True
            else:
                if "delete" not in self.action_disallowed_list:
                    self.action_disallowed_list.append("delete")
                self.can_create = False

        if current_user:
            user_permission: str = current_user.asociated_with
            if (
                user_permission.lower() == "global-full"
                or user_permission.lower() == "global-view"
            ):
                result_query = self.session.query(self.model)
            else:
                result_query = self.session.query(self.model).filter(
                    or_(
                        self.model.location_name == user_permission,
                        self.model.company_name == user_permission,
                    )
                )
        else:
            result_query = self.session.query(self.model).filter(
                self.model.computer_name == "None"
            )
        return result_query

    ###################################################

    # NOTE 1 this example is good if you want to show certain fields depending on some array
    # general_product_attributes = ['name']
    # # company_locations = {i.company_name: [j.location_name for j in i] for i in Location.query.all()}
    # # company_name_index = 2
    # # location_name_index = 3
    # company_locations = {i[2]: [j[1] for j in sql_result if i[2] in j] for i in sql_result}
    # # product_attributes_per_product_type_dict = {
    # #     'driving': ['honking_loudness'],
    # #     'flying': ['rotor_rpm', 'vertical_speed']
    # # }

    # def on_form_prefill(self, form, id):
    #     location = self.get_one(id)
    #     form_attributes = self.general_product_attributes + self.company_locations[location.company_name]
    #     for field in list(form):
    #         if field.name not in form_attributes:
    #             delattr(form, field.name)
    #     return form

    ###############################################################

    # form_ajax_refs = {
    #     'location_name': QueryAjaxModelLoader('locations', db.session, Location,
    #                                 fields=['name'], filters=["company_name=Dro Ltc"])
    # }

    ##############################################

    # NOTE 2 This one works as filter. You start to type company name in location field and
    # NOTE 2 and get list of aplicable locations
    # Setup AJAX lazy-loading for the ImageType inside the inline model
    form_ajax_refs = {
        "location": QueryAjaxModelLoader(
            name="location",
            session=db.session,
            model=Location,
            fields=["company_name"],
            order_by="name",
            # filters=["company_name='Dro Ltc'"],
            placeholder="Type company name to get appropriate locations",
            minimum_input_length=0,
        )
    }

    ########################################################

    # NOTE 3 working decision, but you should first choose a company, save, press edit and choose location
    # def edit_form(self, obj):
    #     form = super(ComputerView, self).edit_form(obj)
    #     query = self.session.query(Location).filter(Location.company == obj.company)
    #     form.location.query = query
    #     return form

    def edit_form(self, obj):
        form = super(ComputerView, self).edit_form(obj)

        computers = [
            {"location": comp.location_name, "company": comp.company_name}
            for comp in Computer.query.all()
        ]
        computers = Computer.query.all()
        computer_location = [loc.location_name for loc in computers]
        computer_company = [co.company_name for co in computers]
        computers_status = [stat.alert_status for stat in computers]
        # update number of computers in locations
        locations = Location.query.all()
        location_company = [loc.company_name for loc in locations]
        if locations:
            for location in locations:
                location.computers_per_location = computer_location.count(location.name)
                # TODO status will be updated only on computer save, though heartbeat checks it every 5 min
                computers_online = computers_status.count("green")
                location.computers_online = computers_online
                location.computers_offline = len(computers_status) - computers_online

        # update number of locations and computers in companies
        companies = Company.query.all()
        if companies:
            for company in companies:
                company.total_computers = computer_company.count(company.name)
                # TODO status will be updated only on computer save, though heartbeat checks it every 5 min
                computers_online = computers_status.count("green")
                company.computers_online = computers_online
                company.computers_offline = len(computers_status) - computers_online
                company.locations_per_company = location_company.count(company.name)
        return form

    ###############################################

    # form_ajax_refs = {
    #     "location": {
    #         "fields": ("company_name", ),
    #         "placeholder": "Please select",
    #         "page_size": 10,
    #         "minimum_input_length": 0,
    #     }
    # }

    # form_ajax_refs = {'location': {
    #     'fields': (Location.company_name, 'company_name'),
    #     "minimum_input_length": 0,
    #     }
    # }

    ################################################

    # form_extra_fields = {
    #     "location_name": QuerySelectField(
    #         label="Location_name",
    #         query_factory=lambda: Location.query.all(),
    #         widget=Select2Widget().
    #     )
    # }
    # column_list = ("company_name", "locations", "computers")

    ########################################################
