from datetime import date

from rkdigi import ManagedOAuth2Session

# Elements in the Nexus API that are specific to the assistive devices dashboard and its widgets/forms.
ASSISTIVE_DEVICES_DASHBOARD_NAME = "Dokumentation - Personlige hjælpemidler"
ASSISTIVE_DEVICES_DASHBOARD_DOCS_WIDGET_NAME = "Breve og dokumenter Personlige hjælpemidler"
ASSISTIVE_DEVICES_DASHBOARD_COMMUNICATION_WIDGET_NAME = "Henvendelse Visitation Personlige hjælpemidler"
ASSISTIVE_DEVICES_COMMUNICATION_FORM_TITLE = "Henvendelse Kropsbårne hjælpemidler"


class NexusClient:
    """A client for interacting with the Nexus API, which uses HAL (Hypertext Application Language) for hypermedia."""
    def __init__(self, base_url: str, token_url: str, client_id: str, client_secret: str):
        self.base_url = base_url
        self.session = ManagedOAuth2Session(token_url=token_url, client_id=client_id, client_secret=client_secret)

    # Universal private helpers for navigating the Nexus API, which uses HAL (Hypertext Application Language) for hypermedia.
    def _link(self, obj: dict, rel: str) -> str:
        """Get the URL for a given HAL link relation from an object."""
        return obj.get("_links", {}).get(rel, {}).get("href")

    def _follow(self, obj: dict, rel: str, method: str = "get", **kwargs) -> dict:
        """Follow a HAL link relation from an object and return the resulting JSON response."""
        url = obj.get("_links", {}).get(rel, {}).get("href")
        if not url:
            available_rels = ", ".join(obj.get("_links", {}).keys()) or "<none>"
            raise ValueError(f"Missing HAL link rel '{rel}'. Available rels: {available_rels}")
        res = self.session.request(method.upper(), url, **kwargs)
        res.raise_for_status()
        return res.json()

    def _get(self, endpoint: str = None, params: dict | None = None) -> dict:
        """Perform a GET request to the Nexus API, optionally to a specific endpoint with query parameters."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str = None, data: dict | None = None) -> dict:
        """Perform a POST request to the Nexus API, optionally to a specific endpoint with JSON data."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else self.base_url
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    # Private helpers
    def _get_patient_dashboard(self, patient_data: dict, dashboard_name: str) -> dict:
        """Get the dashboard data for a specific patient and dashboard name."""
        patient_preferences = self._follow(patient_data, "patientPreferences")
        dashboard_partial = next((item for item in patient_preferences["CITIZEN_DASHBOARD"] if item.get("name") == dashboard_name), None)
        if dashboard_partial is None:
            raise ValueError(f"Could not find '{dashboard_name}' in patient preferences")
        return self._follow(dashboard_partial, "self")

    def _get_widget(self, dashboard: dict, widget_header_title: str) -> dict:
        """Get a specific widget from a dashboard by its header title."""
        widget = next((item for item in dashboard["view"]["widgets"] if item.get("headerTitle") == widget_header_title), None)
        if widget is None:
            raise ValueError(f"Could not find widget with headerTitle '{widget_header_title}' in dashboard")
        return widget

    # Public methods
    def get_patient_data(self, cpr: str) -> dict:
        """Get the patient data for a specific CPR number."""
        home = self._get()
        patient_search = self._follow(home, "patients", params={"query": cpr})
        patient_data_search = self._follow(patient_search['pages'][0], "patientData")
        if len(patient_data_search) != 1:
            raise ValueError(f"Expected exactly one patient data entry, but found {len(patient_data_search)}")
        return self._follow(patient_data_search[0], "self")

    def add_assistive_device_document(self, patient_data: dict, file_name: str, file_bytes: bytes, mime_type: str) -> bool:
        """Add a document to the assistive devices dashboard for a specific patient."""
        dashboard = self._get_patient_dashboard(patient_data, ASSISTIVE_DEVICES_DASHBOARD_NAME)
        widget = self._get_widget(dashboard, ASSISTIVE_DEVICES_DASHBOARD_DOCS_WIDGET_NAME)
        new_document = self._follow(widget["creatableObjects"], "documentPrototype")
        new_document["originalFileName"] = file_name
        created_document = self._follow(new_document, "create", method="post", json=new_document)

        if mime_type != "application/pdf":
            raise ValueError(f"Expected MIME type 'application/pdf', but got '{mime_type}'")

        # Ensure the file name is valid and ends with .pdf (NOTE: no whitespaces)
        file_name = "_".join(file_name.strip().rstrip(".").split())
        if not file_name:
            raise ValueError("File name cannot be empty")
        if not file_name.lower().endswith(".pdf"):
            file_name = f"{file_name}.pdf"

        upload_res = self._follow(created_document, "upload", method="post", files={"file": (file_name, file_bytes, mime_type)})
        return upload_res.get("status", "").upper() == "UPLOADED"

    def create_assistive_device_communication_form(
            self,
            patient_data: dict,
            application_date: date,
            application_reason: str,
            communication_source: str,
            device: str,
            optional_contact_info: str | None = None,
            patient_understands: bool | None = None,
            can_information_be_obtained: bool | None = None
    ) -> dict:
        """Create a communication form for assistive devices for a specific patient."""
        # Field names
        APPLICATION_DATE_FIELD = "Ansøgningsdato"
        APPLICATION_REASON_FIELD = "Henvendelses årsag"
        COMMUNICATION_SOURCE_FIELD = "Henvendelseskilde"
        PATIENT_UNDERSTANDS_FIELD = "Er borgeren indforstået med henvendelsen?"
        INFORMATION_OBTAINED_FIELD = "Der er givet tilladelse til indhentning af oplysninger"
        DEVICE = "Hvad søges der om?"
        CONTACT_INFO_FIELD = "Uddyb med navn, telefonnummer m.m."

        dashboard = self._get_patient_dashboard(patient_data, ASSISTIVE_DEVICES_DASHBOARD_NAME)
        widget = self._get_widget(dashboard, ASSISTIVE_DEVICES_DASHBOARD_COMMUNICATION_WIDGET_NAME)

        forms = widget.get("creatableObjects", {}).get("forms", [])
        if not forms:
            raise ValueError("No forms found in widget.creatableObjects.forms")

        selected_form = next((form for form in forms if form.get("title") == ASSISTIVE_DEVICES_COMMUNICATION_FORM_TITLE), None)
        if selected_form is None:
            raise ValueError(
                f"Could not find form with title '{ASSISTIVE_DEVICES_COMMUNICATION_FORM_TITLE}'. "
            )

        form = self._follow(selected_form, "formDataPrototype")

        def _get_dropdown_value_or_raise(field_item: dict, option_name: str) -> dict:
            option = next((v for v in field_item.get("possibleValues", []) if v.get("name") == option_name), None)
            if option is None:
                available_options = [v.get("name") for v in field_item.get("possibleValues", [])]
                raise ValueError(
                    f"Could not find option '{option_name}' for field '{field_item.get('label')}'. "
                    f"Available options: {available_options}"
                )
            return option

        # Populate the form with provided data
        for item in form.get("items", []):
            label = item.get("label")
            if label == APPLICATION_DATE_FIELD:
                item["value"] = application_date.strftime("%Y-%m-%d")
            elif label == APPLICATION_REASON_FIELD:
                item["value"] = f"{device}\n{application_reason}"
            elif label == COMMUNICATION_SOURCE_FIELD:
                item["value"] = _get_dropdown_value_or_raise(item, communication_source)
            elif label == PATIENT_UNDERSTANDS_FIELD:
                # NOTE: Hardcoded options
                selected_name = "Uafklaret" if patient_understands is None else ("Ja" if patient_understands else "Nej")
                item["value"] = _get_dropdown_value_or_raise(item, selected_name)
            elif label == INFORMATION_OBTAINED_FIELD:
                # NOTE: Hardcoded options
                selected_name = "Der er ikke taget stilling" if can_information_be_obtained is None else ("Ja" if can_information_be_obtained else "Nej")
                item["value"] = _get_dropdown_value_or_raise(item, selected_name)
            elif label == DEVICE:
                option = next((v for v in item.get("possibleValues", []) if v.get("name", "").lower() == device.lower()), None)
                if option is not None:
                    item["value"] = [option]
            elif label == CONTACT_INFO_FIELD and optional_contact_info:
                item["value"] = optional_contact_info

        actions = self._follow(form, "availableActions")
        action = next((a for a in actions if a.get("name") == "Udfyldt"), None)  # NOTE: Hardcoded action name
        if action is None:
            raise ValueError("Could not find action 'Udfyldt' in availableActions")

        created_form = self._follow(action, "createFormData", method="post", json=form)
        return created_form
