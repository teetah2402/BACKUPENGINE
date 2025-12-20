########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\tools\image_generator_tools\processor.py total lines 128 
########################################################################

import smtplib
import os
import tempfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer
from flowork_kernel.utils.payload_helper import get_nested_value

class EmailSenderModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "basic"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.variable_manager = self.kernel.get_service("variable_manager_service")

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        recipient = config.get('recipient_to') or get_nested_value(payload, 'data.recipient')
        subject = config.get('subject', 'No Subject')
        body_template = config.get('body', '')

        if mode == 'SIMULATE':
            status_updater(f"Simulating email to {recipient}...", "INFO")
            if not recipient:
                self.logger("Simulation Warning: No recipient specified.", "WARN")

            self.logger(f"--- EMAIL SIMULATION ---\nTo: {recipient}\nSubject: {subject}\nBody: {body_template[:50]}...\n------------------------", "INFO")

            if 'data' not in payload: payload['data'] = {}
            payload['data']['email_status'] = 'Sent (Simulated)'
            status_updater("Email simulated successfully.", "SUCCESS")
            return {"payload": payload, "output_name": "success"}

        if not self.variable_manager:
            self.variable_manager = self.kernel.get_service("variable_manager_service")
            if not self.variable_manager:
                return self._error("VariableManager service is not available.", payload)

        smtp_host = self.variable_manager.get_variable("SMTP_HOST")
        smtp_port = self.variable_manager.get_variable("SMTP_PORT")
        email_address = self.variable_manager.get_variable("EMAIL_ADDRESS")
        email_password = self.variable_manager.get_variable("EMAIL_PASSWORD")

        if not all([smtp_host, smtp_port, email_address, email_password]):
            return self._error("SMTP credentials missing in Variable Manager. Please set SMTP_HOST, SMTP_PORT, EMAIL_ADDRESS, and EMAIL_PASSWORD.", payload)

        if not recipient:
            return self._error("Recipient address is empty.", payload)

        status_updater(f"Preparing email to {recipient}...", "INFO")

        try:
            msg = MIMEMultipart()
            msg['From'] = email_address
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body_template, 'plain'))

            attach_var = config.get('attachment_path_variable')
            attachment_path = get_nested_value(payload, attach_var) if attach_var else None

            payload_attachments = payload.get('data', {}).get('attachments', [])

            paths_to_attach = []
            if attachment_path and isinstance(attachment_path, str):
                paths_to_attach.append(attachment_path)

            if isinstance(payload_attachments, list):
                for item in payload_attachments:
                    if isinstance(item, str): paths_to_attach.append(item)

            for fpath in paths_to_attach:
                if os.path.exists(fpath) and os.path.isfile(fpath):
                    self._attach_file(msg, fpath)
                    status_updater(f"Attached: {os.path.basename(fpath)}", "INFO")
                else:
                    self.logger(f"Attachment not found or invalid: {fpath}", "WARN")

            status_updater("Connecting to SMTP server...", "INFO")
            smtp_port = int(smtp_port)

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(email_address, email_password)
                server.send_message(msg)

            status_updater("Email sent successfully.", "SUCCESS")
            self.logger(f"Email sent to {recipient}", "INFO")

            if 'data' not in payload: payload['data'] = {}
            payload['data']['email_status'] = 'Sent successfully'

            return {"payload": payload, "output_name": "success"}

        except Exception as e:
            return self._error(f"Failed to send email: {str(e)}", payload)

    def _attach_file(self, msg, file_path):
        try:
            with open(file_path, "rb") as attachment_file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_file.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(file_path)}",
            )
            msg.attach(part)
        except Exception as e:
            self.logger(f"Could not attach file '{file_path}': {e}", "WARN")

    def _error(self, msg, payload):
        self.logger(msg, "ERROR")
        if 'data' not in payload: payload['data'] = {}
        payload['data']['error'] = msg
        return {"payload": payload, "output_name": "error"}

    def get_data_preview(self, config: dict):
        recipient = config.get('recipient_to', 'Unknown')
        return [{'status': 'ready', 'message': f"To: {recipient}", 'details': {'subject': config.get('subject')}}]
