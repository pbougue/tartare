# Copyright (c) 2001-2016, Canal TP and/or its affiliates. All rights reserved.
#
# This file is part of Navitia,
#     the software to build cool stuff with public transport.
#
# Hope you'll enjoy and contribute to this project,
#     powered by Canal TP (www.canaltp.fr).
# Help us simplify mobility and open public transport:
#     a non ending quest to the responsive locomotion way of traveling!
#
# LICENCE: This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Stay tuned using
# twitter @navitia
# IRC #navitia on freenode
# https://groups.google.com/d/forum/navitia
# www.navitia.io


import logging
import smtplib
import socket
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from tartare.core.models import Job


class Mailer(object):
    def __init__(self, config: dict, platform: str = 'Unknown') -> None:
        self.from_ = config.get("from", 'tartare@canaltp.fr')
        self.to = config.get("to")
        self.cc = config.get("cc")
        self.host = config.get('smtp', {}).get("host", 'localhost')
        self.port = config.get('smtp', {}).get("port", 25)
        self.timeout = config.get('smtp', {}).get("timeout", 1)
        self.platform = platform

    def get_message(self, job: Job) -> str:
        message = ["Problem Tartare, Platform {}".format(self.platform),
                   "",
                   "",
                   "Start execution : {}".format(job.started_at),
                   "End execution : {}".format(job.updated_at),
                   "Action type: {}".format(job.action_type),
                   "Job: {}".format(job.id),
                   "Step: {}".format(job.step)]
        if job.contributor_id:
            message.append("Contributor: {}".format(job.contributor_id))
        if job.coverage_id:
            message.append("Coverage: {}".format(job.coverage_id))
        message = message + ["Error Message : {}".format(job.error_message),
                             "",
                             "",
                             "=" * 75,
                             "Automatic email from Tartare",
                             "=" * 75]
        str_message = "\n".join(message)
        return str_message.format(job=job)

    def format_mail(self, job: Job) -> MIMEMultipart:
        attachment = MIMEBase('application', "text/html")

        mail = MIMEMultipart("alternative")
        mail["From"] = self.from_
        mail["To"] = self.to
        mail["Cc"] = self.cc
        mail["Subject"] = 'Problem Tartare'
        mail['X-MSMail-Priority'] = 'High'
        mail.attach(MIMEText(self.get_message(job), 'plain', "utf-8"))
        mail.attach(attachment)
        return mail

    def get_to_addrs(self) -> List[str]:
        return [self.to] + self.cc.split(',') if self.cc else self.to

    def send(self, mail: MIMEMultipart) -> None:
        server = smtplib.SMTP()
        server.timeout = self.timeout
        try:
            server.connect(host=self.host, port=self.port)
            server.sendmail(self.from_, self.get_to_addrs(), mail.as_string())
            logging.getLogger(__name__).debug("Mail sent to %s" % self.get_to_addrs())
        except smtplib.SMTPException as exception:
            logging.getLogger(__name__).critical("Sendmail error [from = %s, to = %s], error message :%s" %
                                                 (self.from_, self.to, str(exception)))
        except (socket.gaierror, Exception) as e:
            logging.getLogger(__name__).critical("Connection error [host = %s], error message :%s" %
                                                 (self.host, str(e)))
        finally:
            server.quit()

    def build_msg_and_send_mail(self, job: Job) -> None:
        if job:
            mail = self.format_mail(job)
            self.send(mail)
